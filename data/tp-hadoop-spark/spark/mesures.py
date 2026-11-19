"""Measures asked by the report: partitions, lineage, cache, shuffle sizes, plans and Parquet.

Run: spark-submit --master local[2] mesures.py
"""
import json
import time
import urllib.request
from operator import add

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BASE = "hdfs://localhost:9000/user/falek/accidents"
PARQUET = "hdfs://localhost:9000/user/falek/accidents_parquet/usagers"

spark = SparkSession.builder.appName("TP-BAAC-Mesures").getOrCreate()
sc = spark.sparkContext
sc.setLogLevel("WARN")


def load(name):
    rdd = sc.textFile(f"{BASE}/{name}")
    header = rdd.first()
    return rdd.filter(lambda l: l != header).map(lambda l: l.split(";"))


def duration(action):
    start = time.time()
    action()
    return time.time() - start


def shuffle_write():
    """Total shuffle write of the finished stages, from the Spark UI REST API."""
    time.sleep(1)
    url = f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}/stages?status=complete"
    with urllib.request.urlopen(url) as response:
        return sum(stage["shuffleWriteBytes"] for stage in json.load(response))


carac = load("caracteristiques")
lieux = load("lieux")
vehicules = load("vehicules")
usagers = load("usagers")

print("\n== Partitions")
for name, rdd in [("carac", carac), ("lieux", lieux), ("vehicules", vehicules), ("usagers", usagers)]:
    print(name, rdd.getNumPartitions())

print("\n== Lineage of the pairs")
print(usagers.map(lambda r: (r[6], 1)).toDebugString().decode())

print("\n== Lineage of Q5")
killed = usagers.filter(lambda r: r[6] == "2").map(lambda r: (r[0], 1)).reduceByKey(add)
q5 = carac.map(lambda r: (r[0], r[5])).leftOuterJoin(killed)
print(q5.toDebugString().decode())

print("\n== Shuffle write")
before = shuffle_write()
usagers.map(lambda r: (r[6], 1)).reduceByKey(add).collect()
after_reduce = shuffle_write()
usagers.map(lambda r: (r[6], 1)).groupByKey().mapValues(len).collect()
after_group = shuffle_write()
print("reduceByKey bytes:", after_reduce - before)
print("groupByKey bytes:", after_group - after_reduce)

print("\n== Cache")
usagers.cache()
print(f"first count: {duration(usagers.count):.3f} s")
print(f"second count: {duration(usagers.count):.3f} s")
print("is_cached:", usagers.is_cached)
usagers.unpersist()

print("\n== repartition and coalesce")
print("repartition(8):", usagers.repartition(8).getNumPartitions())
print(usagers.repartition(8).toDebugString().decode())
print("coalesce(1):", usagers.coalesce(1).getNumPartitions())
print(usagers.coalesce(1).toDebugString().decode())


def read(name):
    return (spark.read.option("header", True).option("sep", ";")
            .option("inferSchema", True).csv(f"{BASE}/{name}"))


print("\n== Plan of carac JOIN lieux")
q = read("caracteristiques").join(read("lieux"), "Num_Acc").filter(F.col("vma") > 0).groupBy("catr").count()
q.explain(True)
q.show()

print("\n== Parquet")
df = read("usagers")
df.write.mode("overwrite").parquet(PARQUET)
parquet = spark.read.parquet(PARQUET)
print(f"group by grav on CSV: {duration(lambda: df.groupBy('grav').count().collect()):.3f} s")
print(f"group by grav on Parquet: {duration(lambda: parquet.groupBy('grav').count().collect()):.3f} s")
parquet.groupBy("grav").count().orderBy("grav").show()
parquet.select("grav").explain()

spark.stop()
