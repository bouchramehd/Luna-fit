import tempfile
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Luna-fit Spark test").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

try:
    with tempfile.TemporaryDirectory(dir="/workspace/data") as folder:
        path = folder + "/parquet"
        spark.range(100).repartition(2).write.parquet(path)
        result = spark.read.parquet(path)

        assert result.count() == 100, "Row count mismatch"
        assert result.groupBy().sum("id").first()[0] == 4950, "Sum mismatch"

        print("PASS: Spark wrote and read 100 rows as Parquet.")
finally:
    spark.stop()