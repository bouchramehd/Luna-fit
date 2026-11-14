import json
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

root = Path("/workspace")
destination = root / "data/gold/nutrition_activity_profiles_v1"

if destination.exists():
    raise FileExistsError(f"Output already exists: {destination}")

config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)

spark = SparkSession.builder.appName("Nutrition activity profiles").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

keys = ["survey_cycle", "SEQN"]
cycles = ["2011-2012", "2013-2014", "2015-2016"]

try:
    women = spark.read.parquet(
        str(root / "data/gold/multicycle_v3/women")
    ).filter(F.col("survey_cycle").isin(cycles))

    original_count = women.count()
    activity = None

    for cycle in config["cycles"]:
        if cycle["label"] not in cycles:
            continue

        name = f"PAQ_{cycle['suffix']}"
        table = spark.read.parquet(
            str(
                root / "data/silver" / cycle["label"]
                / name / "data.parquet"
            )
        ).select(
            *keys,
            "PAQ665", "PAQ670", "PAD675",
            "PAQ635", "PAQ640", "PAD645", "PAD680",
        )

        assert table.select(*keys).distinct().count() == table.count()

        activity = (
            table if activity is None
            else activity.unionByName(table)
        )

    result = women.join(activity, keys, "left")
    adult = F.col("RIDAGEYR") >= 18

    for prefix, answer, days, minutes in [
        ("moderate_recreation", "PAQ665", "PAQ670", "PAD675"),
        ("active_transport", "PAQ635", "PAQ640", "PAD645"),
    ]:
        absent = F.col(days).isNull() & F.col(minutes).isNull()
        valid = (
            F.col(days).between(1, 7)
            & (F.col(days) == F.floor(F.col(days)))
            & (F.col(minutes) >= 10)
            & (F.col(minutes) < 1440)
        )

        result = result.withColumn(
            f"{prefix}_minutes_week",
            F.when(adult & (F.col(answer) == 2) & absent, 0.0)
            .when(
                adult & (F.col(answer) == 1) & valid,
                F.col(days) * F.col(minutes),
            ),
        ).withColumn(
            f"{prefix}_followup_conflict",
            F.coalesce(
                adult & (F.col(answer) == 2) & ~absent,
                F.lit(False),
            ),
        )

    result = result.withColumn(
        "sedentary_minutes_day",
        F.when(
            adult & (F.col("PAD680") >= 0) & (F.col("PAD680") < 1440),
            F.col("PAD680"),
        ),
    ).withColumn(
        "eligible_for_profile_analysis",
        F.coalesce(
            adult
            & F.col("reliable_day1_recall")
            & (F.col("energy_kcal") > 0),
            F.lit(False),
        ),
    )

    assert result.count() == original_count
    assert result.select(*keys).distinct().count() == original_count

    result.write.mode("errorifexists").parquet(
        str(destination / "women")
    )

    result.filter("eligible_for_profile_analysis").groupBy(
        "survey_cycle"
    ).agg(
        F.count("*").alias("eligible_women"),
        F.count("moderate_recreation_minutes_week").alias("moderate_known"),
        F.count("active_transport_minutes_week").alias("transport_known"),
        F.count("sedentary_minutes_day").alias("sedentary_known"),
        F.sum(
            F.col("moderate_recreation_followup_conflict").cast("int")
        ).alias("moderate_conflicts"),
        F.sum(
            F.col("active_transport_followup_conflict").cast("int")
        ).alias("transport_conflicts"),
    ).orderBy("survey_cycle").show()

    print("PASS: profile preparation saved; all source women preserved.")
    print("No clustering trained yet; no hemoglobin eligibility requirement.")
finally:
    spark.stop()