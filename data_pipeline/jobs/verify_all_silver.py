import json
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

root = Path("/workspace")
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

spark = SparkSession.builder.appName("Verify all Silver").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

try:
    for cycle in config["cycles"]:
        label = cycle["label"]
        tables = {}

        for component in config["initial_components"]:
            name = f"{component}_{cycle['suffix']}"
            folder = root / "data/silver" / label / name

            metadata = json.loads(
                (folder / "metadata.json").read_text(encoding="utf-8")
            )
            df = spark.read.parquet(str(folder / "data.parquet"))
            rows = df.count()

            assert rows == metadata["rows"], f"Row mismatch: {name}"

            expected_columns = set(metadata["original_columns"])
            expected_columns.add("survey_cycle")
            assert set(df.columns) == expected_columns, (
                f"Column mismatch: {name}"
            )

            assert df.filter(F.col("SEQN").isNull()).count() == 0, (
                f"Missing participant IDs: {name}"
            )

            invalid_cycle = df.filter(
                F.col("survey_cycle").isNull()
                | (F.col("survey_cycle") != label)
            )
            assert invalid_cycle.count() == 0, (
                f"Invalid cycle identifier: {name}"
            )

            if component != "DR1IFF":
                assert df.select("SEQN").distinct().count() == rows, (
                    f"Duplicate participant IDs: {name}"
                )

            tables[component] = df
            print(f"PASS: {label}/{name} — {rows:,} rows", flush=True)

        demographic_ids = tables["DEMO"].select("SEQN")

        for component in config["initial_components"]:
            if component == "DEMO":
                continue

            unmatched = (
                tables[component]
                .select("SEQN")
                .distinct()
                .join(demographic_ids, "SEQN", "left_anti")
            )

            assert unmatched.count() == 0, (
                f"Unmatched participant IDs: {label}/{component}"
            )

        print(f"PASS: {label} — all participant links valid", flush=True)

    print(
        "PASS: all Silver tables readable; "
        "counts, columns, keys and participant links valid."
    )
finally:
    spark.stop()