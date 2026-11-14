from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Verify NHANES Silver").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

try:
    for name, expected in [("DEMO_I", 9971), ("DR1IFF_I", 121481)]:
        df = spark.read.parquet(
            f"/workspace/data/silver/2015-2016/{name}/data.parquet"
        )
        count = df.count()
        assert count == expected, f"{name}: unexpected count {count}"
        assert df.filter("survey_cycle IS NULL OR survey_cycle != '2015-2016'").count() == 0
        print(f"PASS: {name} — {count} rows")
finally:
    spark.stop()