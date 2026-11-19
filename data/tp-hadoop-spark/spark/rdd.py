"""Part 5: Q1 to Q9 with the RDD API.

Run: spark-submit --master local[2] rdd.py
"""
import time
from operator import add

from pyspark.sql import SparkSession

BASE = "hdfs://localhost:9000/user/falek/accidents"

spark = SparkSession.builder.appName("TP-BAAC-RDD").getOrCreate()
sc = spark.sparkContext
sc.setLogLevel("WARN")


def load(name):
    rdd = sc.textFile(f"{BASE}/{name}")
    header = rdd.first()
    return rdd.filter(lambda l: l != header).map(lambda l: l.split(";"))


def timed(name, query):
    start = time.time()
    result = query()
    print(f"\n{name} ({time.time() - start:.2f} s)")
    for row in result:
        print(row)


def add_pairs(a, b):
    return a[0] + b[0], a[1] + b[1]


carac = load("caracteristiques")
lieux = load("lieux")
vehicules = load("vehicules")
usagers = load("usagers")


def q1():
    return [
        ("accidents", carac.map(lambda r: r[0]).distinct().count()),
        ("vehicules", vehicules.map(lambda r: r[1]).distinct().count()),
        ("usagers", usagers.map(lambda r: r[1]).distinct().count()),
    ]


def q2():
    return carac.map(lambda r: (int(r[2]), 1)).reduceByKey(add).sortByKey().collect()


def q3():
    by_grav = usagers.map(lambda r: (r[6], 1)).reduceByKey(add)
    total = by_grav.values().sum()
    return by_grav.mapValues(lambda n: (n, round(100 * n / total, 2))).sortByKey().collect()


def q4():
    return (carac.map(lambda r: (r[6], 1)).reduceByKey(add)
            .takeOrdered(10, key=lambda x: (-x[1], x[0])))


def q5():
    lum = carac.map(lambda r: (r[0], r[5]))
    killed = usagers.filter(lambda r: r[6] == "2").map(lambda r: (r[0], 1)).reduceByKey(add)
    # (num_acc, (lum, killed or None)) becomes (lum, (1 accident, killed))
    return (lum.leftOuterJoin(killed)
            .map(lambda kv: (kv[1][0], (1, kv[1][1] or 0)))
            .reduceByKey(add_pairs).sortByKey().collect())


def q6():
    killed = usagers.filter(lambda r: r[6] == "2").map(lambda r: (r[2], 1))
    catv = vehicules.map(lambda r: (r[1], r[4]))
    return (killed.join(catv).map(lambda kv: (kv[1][1], 1)).reduceByKey(add)
            .takeOrdered(5, key=lambda x: (-x[1], x[0])))


def q7():
    return (usagers.filter(lambda r: r[6] == "2" and r[7] in ("1", "2") and r[8].isdigit())
            .map(lambda r: (r[7], (2024 - int(r[8]), 1)))
            .reduceByKey(add_pairs)
            .mapValues(lambda v: round(v[0] / v[1], 2))
            .sortByKey().collect())


def q8():
    # catr and vma come from the same lieux row: joining them separately would multiply
    # the rows of an accident that has several lieux rows.
    places = (lieux.filter(lambda r: int(r[17]) > 0)
              .map(lambda r: (r[0], (r[1], int(r[17])))))
    rows = carac.map(lambda r: (r[0], 1)).join(places).map(lambda kv: (kv[1][1][0], kv[0], kv[1][1][1]))
    stats = rows.map(lambda x: (x[0], (1, x[2]))).reduceByKey(add_pairs)
    accidents = rows.map(lambda x: (x[0], x[1])).distinct().map(lambda x: (x[0], 1)).reduceByKey(add)
    return (stats.join(accidents)
            .mapValues(lambda v: (v[0][0], v[1], round(v[0][1] / v[0][0], 2)))
            .sortByKey().collect())


def q9():
    veh = vehicules.map(lambda r: (r[1], 1))
    usr = usagers.map(lambda r: (r[2], 1)).distinct()
    return [veh.subtractByKey(usr).count()]


for name, query in [("Q1", q1), ("Q2", q2), ("Q3", q3), ("Q4", q4), ("Q5", q5),
                    ("Q6", q6), ("Q7", q7), ("Q8", q8), ("Q9", q9)]:
    timed(name, query)

spark.stop()
