from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("NHANES Gold").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

try:
    base = "/workspace/data"
    keys = ["survey_cycle", "SEQN"]

    demo = spark.read.parquet(
        f"{base}/silver/2015-2016/DEMO_I/data.parquet"
    )
    food = spark.read.parquet(
        f"{base}/silver/2015-2016/DR1IFF_I/data.parquet"
    )

    assert demo.filter(F.col("SEQN").isNull()).count() == 0
    assert food.filter(F.col("SEQN").isNull()).count() == 0
    assert demo.select(*keys).distinct().count() == demo.count()
    assert food.select(*keys).distinct().join(
        demo.select(*keys), keys, "left_anti"
    ).count() == 0

    nutrients = {
        "DR1IKCAL": "energy_kcal",
        "DR1IPROT": "protein_g",
        "DR1ICARB": "carbohydrate_g",
        "DR1ITFAT": "fat_g",
        "DR1IIRON": "iron_mg",
    }

    # Participant-level fields must be consistent across food records.
    for column in ["DR1DRSTZ", "WTDRD1", "WTDR2D"]:
        inconsistent = food.groupBy(*keys).agg(
            F.countDistinct(column).alias("values"),
            F.count(column).alias("present"),
            F.count("*").alias("rows"),
        ).filter(
            (F.col("values") > 1)
            | ((F.col("present") > 0) & (F.col("present") < F.col("rows")))
        )
        assert inconsistent.count() == 0, f"Inconsistent {column}"

    expressions = [
        F.count("*").alias("food_record_count"),
        F.first("DR1DRSTZ").alias("recall_status"),
        F.first("WTDRD1").alias("WTDRD1"),
        F.first("WTDR2D").alias("WTDR2D"),
    ]

    for source, target in nutrients.items():
        # Return null if any food record lacks this nutrient.
        expressions.extend([
            F.when(
                F.count(source) == F.count("*"),
                F.sum(source),
            ).alias(target),
            F.sum(
                F.col(source).isNull().cast("int")
            ).alias(f"{target}_missing_records"),
        ])

    dietary = food.groupBy(*keys).agg(*expressions)

    # Left join preserves all demographic participants.
    gold = (
        demo.join(dietary, keys, "left")
        .withColumn(
            "has_food_records",
            F.col("food_record_count").isNotNull(),
        )
        .withColumn(
            "reliable_day1_recall",
            F.coalesce(F.col("recall_status") == 1, F.lit(False)),
        )
    )

    assert gold.count() == 9971
    assert dietary.count() == 8505

    women = gold.filter(F.col("RIAGENDR") == 2)
    assert women.filter("has_food_records").count() == 4335

    # Refuse to overwrite existing outputs.
    gold.write.mode("errorifexists").parquet(
        f"{base}/gold/2015-2016/participants"
    )
    women.write.mode("errorifexists").parquet(
        f"{base}/gold/2015-2016/women"
    )

    print("PASS: Gold saved — 9,971 participants; all female ages preserved.")
    print("Reliable recall is flagged; no training subset selected yet.")
finally:
    spark.stop()