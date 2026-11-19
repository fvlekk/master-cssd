"""Part 6: Q1 to Q9 with the DataFrame API, then with Spark SQL.

Run: spark-submit --master local[2] df.py
"""
import time

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BASE = "hdfs://localhost:9000/user/falek/accidents"

spark = SparkSession.builder.appName("TP-BAAC-DF").getOrCreate()
spark.sparkContext.setLogLevel("WARN")


def read(name):
    return (spark.read.option("header", True).option("sep", ";")
            .option("inferSchema", True).csv(f"{BASE}/{name}"))


def timed(name, query):
    start = time.time()
    rows = query().collect()
    print(f"\n{name} ({time.time() - start:.2f} s)")
    for row in rows:
        print(tuple(row))


carac = read("caracteristiques")
lieux = read("lieux")
vehicules = read("vehicules")
usagers = read("usagers")

for name, table in [("caracteristiques", carac), ("lieux", lieux), ("vehicules", vehicules), ("usagers", usagers)]:
    table.createOrReplaceTempView(name)
    print(name)
    table.printSchema()

killed_by_acc = usagers.filter(F.col("grav") == 2).groupBy("Num_Acc").agg(F.count("*").alias("killed"))

dataframe_queries = [
    ("Q1", lambda: spark.createDataFrame(
        [("accidents", carac.count()), ("vehicules", vehicules.count()), ("usagers", usagers.count())],
        ["tbl", "nb"])),
    ("Q2", lambda: carac.groupBy("mois").count().orderBy("mois")),
    ("Q3", lambda: usagers.groupBy("grav").agg(F.count("*").alias("nb"))
        .withColumn("pct", F.round(100 * F.col("nb") / usagers.count(), 2)).orderBy("grav")),
    ("Q4", lambda: carac.groupBy("dep").count().orderBy(F.desc("count"), "dep").limit(10)),
    ("Q5", lambda: carac.join(killed_by_acc, "Num_Acc", "left").groupBy("lum")
        .agg(F.count("*").alias("accidents"), F.sum(F.coalesce(F.col("killed"), F.lit(0))).alias("killed"))
        .orderBy("lum")),
    ("Q6", lambda: usagers.filter(F.col("grav") == 2).join(vehicules, "id_vehicule").groupBy("catv")
        .agg(F.count("*").alias("killed")).orderBy(F.desc("killed"), "catv").limit(5)),
    ("Q7", lambda: usagers.withColumn("age", 2024 - F.col("an_nais"))
        .filter((F.col("grav") == 2) & F.col("sexe").isin(1, 2) & (F.col("an_nais") > 0))
        .groupBy("sexe").agg(F.round(F.avg("age"), 2).alias("age_moyen")).orderBy("sexe")),
    ("Q8", lambda: carac.join(lieux, "Num_Acc").filter(F.col("vma") > 0).groupBy("catr")
        .agg(F.count("*").alias("nb_lignes"), F.countDistinct("Num_Acc").alias("nb_accidents"),
             F.round(F.avg("vma"), 2).alias("vma_moyenne")).orderBy("catr")),
    ("Q9", lambda: spark.createDataFrame([(vehicules.join(usagers, "id_vehicule", "left_anti").count(),)], ["nb"])),
]

sql_queries = {
    "Q1": """SELECT 'accidents' AS tbl, COUNT(*) AS nb FROM caracteristiques
             UNION ALL SELECT 'vehicules', COUNT(*) FROM vehicules
             UNION ALL SELECT 'usagers', COUNT(*) FROM usagers""",
    "Q2": "SELECT mois, COUNT(*) AS nb FROM caracteristiques GROUP BY mois ORDER BY mois",
    "Q3": """SELECT grav, COUNT(*) AS nb, ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
             FROM usagers GROUP BY grav ORDER BY grav""",
    "Q4": "SELECT dep, COUNT(*) AS nb FROM caracteristiques GROUP BY dep ORDER BY nb DESC, dep LIMIT 10",
    "Q5": """SELECT c.lum, COUNT(*) AS accidents, SUM(COALESCE(k.killed, 0)) AS killed
             FROM caracteristiques c
             LEFT JOIN (SELECT Num_Acc, COUNT(*) AS killed FROM usagers WHERE grav = 2 GROUP BY Num_Acc) k
               ON c.Num_Acc = k.Num_Acc
             GROUP BY c.lum ORDER BY c.lum""",
    "Q6": """SELECT v.catv, COUNT(*) AS killed
             FROM usagers u JOIN vehicules v ON u.id_vehicule = v.id_vehicule
             WHERE u.grav = 2
             GROUP BY v.catv ORDER BY killed DESC, v.catv LIMIT 5""",
    "Q7": """SELECT sexe, ROUND(AVG(2024 - an_nais), 2) AS age_moyen
             FROM usagers
             WHERE grav = 2 AND sexe IN (1, 2) AND an_nais > 0
             GROUP BY sexe ORDER BY sexe""",
    "Q8": """SELECT l.catr, COUNT(*) AS nb_lignes, COUNT(DISTINCT l.Num_Acc) AS nb_accidents,
                    ROUND(AVG(l.vma), 2) AS vma_moyenne
             FROM caracteristiques c JOIN lieux l ON c.Num_Acc = l.Num_Acc
             WHERE l.vma > 0
             GROUP BY l.catr ORDER BY l.catr""",
    "Q9": """SELECT COUNT(*) AS nb
             FROM vehicules v LEFT ANTI JOIN usagers u ON v.id_vehicule = u.id_vehicule""",
}

for name, query in dataframe_queries:
    timed(f"{name} DataFrame", query)

for name, query in sql_queries.items():
    timed(f"{name} SQL", lambda: spark.sql(query))

spark.stop()
