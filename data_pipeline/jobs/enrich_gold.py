import json
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

root = Path("/workspace")
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)
rules = json.loads(
    (root / "data_pipeline/configs/harmonization.json").read_text()
)

destination = root / "data/gold/multicycle_v2"
if destination.exists():
    raise FileExistsError(f"Output already exists: {destination}")

spark = SparkSession.builder.appName("Enrich NHANES Gold").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

keys = ["survey_cycle", "SEQN"]

def yes_no(column):
    return (
        F.when(F.col(column) == 1, F.lit(True))
        .when(F.col(column) == 2, F.lit(False))
    )

try:
    gold = spark.read.parquet(
        str(root / "data/gold/multicycle_v1/participants")
    )
    original_count = gold.count()

    for component in ("PAQ", "RHQ"):
        combined = None

        for cycle in config["cycles"]:
            name = f"{component}_{cycle['suffix']}"
            path = (
                root / "data/silver" / cycle["label"]
                / name / "data.parquet"
            )
            table = spark.read.parquet(str(path))

            if component == "PAQ":
                columns = ["PAQ650", "PAQ655", "PAD660"]
            else:
                columns = ["RHQ031", "RHD143"]

            table = table.select(
                *keys,
                *columns,
                F.lit(True).alias(f"has_{component.lower()}_record"),
            )

            assert table.select(*keys).distinct().count() == table.count()

            combined = (
                table if combined is None
                else combined.unionByName(table)
            )

        gold = gold.join(combined, keys, "left")
        gold = gold.fillna({f"has_{component.lower()}_record": False})

    adult = F.col("RIDAGEYR") >= rules["activity"]["minimum_age"]

    valid_days = (
        F.col("PAQ655").between(1, 7)
        & (F.col("PAQ655") == F.floor(F.col("PAQ655")))
    )
    valid_minutes = (
        (F.col("PAD660") >= 10) & (F.col("PAD660") < 1440)
    )
    explicit_no = F.col("PAQ650") == rules["activity"]["no_code"]
    explicit_yes = F.col("PAQ650") == rules["activity"]["yes_code"]

    absent_followups = (
        F.col("PAQ655").isNull() & F.col("PAD660").isNull()
    )

    gold = gold.withColumn(
        "vigorous_recreation_minutes_week",
        F.when(adult & explicit_no & absent_followups, F.lit(0.0))
        .when(
            adult & explicit_yes & valid_days & valid_minutes,
            F.col("PAQ655") * F.col("PAD660"),
        ),
    ).withColumn(
        "activity_followup_conflict",
        F.coalesce(
            adult & explicit_no & ~absent_followups,
            F.lit(False),
        ),
    )

    female = F.col("RIAGENDR") == 2

    gold = gold.withColumn(
        "had_period_past_12_months",
        F.when(
            female
            & (F.col("RIDAGEYR") >= rules["period_history"]["minimum_age"]),
            yes_no("RHQ031"),
        ),
    ).withColumn(
        "self_reported_pregnant",
        F.when(
            female
            & F.col("RIDAGEYR").between(
                rules["pregnancy"]["minimum_age"],
                rules["pregnancy"]["maximum_age"],
            ),
            yes_no("RHD143"),
        ),
    )

    assert gold.count() == original_count == 39156
    assert gold.select(*keys).distinct().count() == original_count

    gold.write.mode("errorifexists").parquet(
        str(destination / "participants")
    )
    gold.filter(female).write.mode("errorifexists").parquet(
        str(destination / "women")
    )

    # Save the exact rules alongside the generated data.
    (destination / "harmonization.json").write_text(
        json.dumps(rules, indent=2), encoding="utf-8"
    )

    gold.filter(female & adult).groupBy("survey_cycle").agg(
        F.count("*").alias("adult_women"),
        F.count("vigorous_recreation_minutes_week").alias("activity_known"),
        F.count("had_period_past_12_months").alias("period_history_known"),
        F.count("self_reported_pregnant").alias("pregnancy_known"),
        F.sum(F.col("activity_followup_conflict").cast("int")).alias("conflicts"),
    ).orderBy("survey_cycle").show()

    print("PASS: Gold v2 saved; all participants and raw selected responses preserved.")
finally:
    spark.stop()