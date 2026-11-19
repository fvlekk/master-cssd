# Master CSSD (Université Paris 8)

Labs and projects of my Master in Cybersecurity and Data Science, grouped by subject.

| Folder | Content |
|---|---|
| [`bases-de-donnees/`](bases-de-donnees) | [`tp-jdbc`](bases-de-donnees/tp-jdbc): Java/JDBC on Oracle (queries, metadata, DML/DDL, transactions). [`tp-bd-distribuees`](bases-de-donnees/tp-bd-distribuees): data split across two Oracle schemas, cross-schema foreign key, synonyms. |
| [`data/`](data) | [`tp-hadoop-spark`](data/tp-hadoop-spark): French road accidents 2024 on HDFS, Hive and Spark (RDD and DataFrame), with a report. |
| [`machine-learning/`](machine-learning) | `projet-fraude-faux-conseiller`: fake bank advisor fraud detection (team project, private repository linked as a submodule). |
| [`python/`](python) | Optimisation course: simplex method in Python, C++ and a web version. |

The database labs run on Oracle Free in Docker: each folder has a `run.sh` that starts its container and replays the lab.
Statements and course slides belong to the teachers and are not published here.
