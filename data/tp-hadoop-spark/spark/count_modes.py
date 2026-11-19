"""Part 4: the same count() to compare the cluster modes.

Run: spark-submit --master <local[2] | yarn | spark://localhost:7077> count_modes.py
"""
import time

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("TP-BAAC").getOrCreate()
sc = spark.sparkContext
sc.setLogLevel("WARN")

lines = sc.textFile("hdfs://localhost:9000/user/falek/accidents/usagers/usagers-2024.csv")
start = time.time()
count = lines.count()
print(f"master={sc.master} lines={count} count_seconds={time.time() - start:.2f} app={sc.applicationId}")
spark.stop()
