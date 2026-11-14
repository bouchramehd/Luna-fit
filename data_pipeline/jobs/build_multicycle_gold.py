import json
from pathlib import Path
from pyspark.sql import SparkSession, functions as F

root = Path("/workspace")
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)

spark = SparkSession.builder.appName("NHANES multi-cycle Gold").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

nutrients = {
    "DR1TKCAL": "energy_kcal",
    "DR1TPROT": "protein_g",
    "DR1TCARB": "carbohydrate_g",
    "DR1TTFAT": "fat_g",
    "DR1TIRON": "iron_mg",
}

combined = None

try:
    for cycle in config["cycles"]:
        label = cycle["label"]
        suffix = cycle["suffix"]
        folder = root / "data/silver" / label
        keys = ["survey_cycle", "SEQN"]

        def read(component):
            return spark.read.parquet(
                str(folder / f"{component}_{suffix}/data.parquet")
            )

        demo = read("DEMO").select(
            *keys,
            "RIAGENDR", "RIDAGEYR",
            "SDMVSTRA", "SDMVPSU",
            "WTINT2YR", "WTMEC2YR",
        )

        totals = read("DR1TOT").select(
            *keys,
            F.lit(True).alias("has_dietary_totals"),
            F.col("DR1DRSTZ").alias("recall_status"),
            "WTDRD1", "WTDR2D",
            *[
                F.col(source).alias(target)
                for source, target in nutrients.items()
            ],
        )

        food_counts = read("DR1IFF").groupBy(*keys).agg(
            F.count("*").alias("food_record_count")
        )

        for table in (demo, totals):
            assert table.select(*keys).distinct().count() == table.count()

        result = (
            demo.join(totals, keys, "left")
            .join(food_counts, keys, "left")
            .fillna({
                "has_dietary_totals": False,
                "food_record_count": 0,
            })
            .withColumn(
                "reliable_day1_recall",
                F.coalesce(F.col("recall_status") == 1, F.lit(False)),
            )
        )

        assert result.count() == demo.count()

        combined = (
            result if combined is None
            else combined.unionByName(result)
        )

    assert combined.count() == 39156
    assert combined.select("survey_cycle", "SEQN").distinct().count() == 39156

    # New destination: preserves the earlier single-cycle Gold outputs.
    destination = root / "data/gold/multicycle_v1"

    # Fail before writing if either destination already exists.
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")

    combined.write.mode("errorifexists").parquet(
        str(destination / "participants")
    )
    combined.filter(F.col("RIAGENDR") == 2).write.mode(
        "errorifexists"
    ).parquet(str(destination / "women"))

    combined.groupBy("survey_cycle").agg(
        F.count("*").alias("participants"),
        F.sum(F.col("RIAGENDR").eqNullSafe(2).cast("int")).alias("female"),
        F.sum(F.col("reliable_day1_recall").cast("int")).alias("reliable_recalls"),
    ).orderBy("survey_cycle").show()

    print("PASS: multi-cycle Gold saved; all demographic participants preserved.")
finally:
    spark.stop()