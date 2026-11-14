import json
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

root = Path("/workspace")
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)

destination = root / "data/gold/multicycle_v3"
if destination.exists():
    raise FileExistsError(f"Output already exists: {destination}")

spark = SparkSession.builder.appName("NHANES body measurements").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

keys = ["survey_cycle", "SEQN"]
combined = None

try:
    gold = spark.read.parquet(
        str(root / "data/gold/multicycle_v2/participants")
    )

    for cycle in config["cycles"]:
        name = f"BMX_{cycle['suffix']}"
        body = spark.read.parquet(
            str(
                root / "data/silver" / cycle["label"]
                / name / "data.parquet"
            )
        ).select(
            *keys,
            "BMDSTATS",
            "BMIWT", "BMIHT", "BMIWAIST",
            "BMXWT", "BMXHT", "BMXBMI", "BMXWAIST",
            F.lit(True).alias("has_body_measurements_record"),
        )

        assert body.select(*keys).distinct().count() == body.count()
        assert body.join(
            gold.select(*keys), keys, "left_anti"
        ).count() == 0

        combined = (
            body if combined is None
            else combined.unionByName(body)
        )

    result = gold.join(combined, keys, "left").fillna(
        {"has_body_measurements_record": False}
    )

    assert result.count() == gold.count() == 39156
    assert result.select(*keys).distinct().count() == 39156

    result.write.mode("errorifexists").parquet(
        str(destination / "participants")
    )
    result.filter(F.col("RIAGENDR") == 2).write.mode(
        "errorifexists"
    ).parquet(str(destination / "women"))

    # Preserve the activity/reproductive rules from the previous version.
    previous_rules = root / "data/gold/multicycle_v2/harmonization.json"
    rules = json.loads(previous_rules.read_text(encoding="utf-8"))
    rules["body_measurements"] = {
        "BMXWT": {"unit": "kg", "minimum_age": 0},
        "BMXHT": {"unit": "cm", "minimum_age": 2},
        "BMXBMI": {"unit": "kg/m²", "minimum_age": 2},
        "BMXWAIST": {"unit": "cm", "minimum_age": 2},
        "processing": "Source values and selected comment/status codes retained; no clipping or imputation",
    }
    (destination / "harmonization.json").write_text(
        json.dumps(rules, indent=2), encoding="utf-8"
    )

    result.filter(
        (F.col("RIAGENDR") == 2) & (F.col("RIDAGEYR") >= 18)
    ).groupBy("survey_cycle").agg(
        F.count("*").alias("adult_women"),
        F.count("BMXWT").alias("weight_known"),
        F.count("BMXHT").alias("height_known"),
        F.count("BMXBMI").alias("bmi_known"),
        F.count("BMXWAIST").alias("waist_known"),
    ).orderBy("survey_cycle").show()

    print("PASS: Gold v3 saved; all participants preserved.")
finally:
    spark.stop()