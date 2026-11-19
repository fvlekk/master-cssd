# TP Hadoop et Spark : accidents de la route en France

M1 CSSD, Conférence industrielle (Ilyes Zeroual), 2026/2027.

## Layout
- `sujet/`: TP statement and the BAAC data description (ONISR).
- `scripts/`: `env.sh` (source it in non-interactive shells), `clean_csv.py` (raw CSV to `~/data/clean/`), `partie2_hdfs.sh`.
- `hive/lab.hql`: tables, Q1 to Q9, ORC comparison. Run `hive -v -f` from `~/hive_work`.
- `spark/`: `rdd.py`, `df.py` (Q1 to Q9), `mesures.py` (partitions, shuffle, cache, plans, Parquet), `count_modes.py` (same count on the 3 modes).
- `rapport/`: `rapport.html` to `rapport.pdf`, `captures/`, `resultats/` (raw logs of every run).
- `hdfs_commands.txt`: generated from the `partie2_hdfs.sh` log, not from shell history.
- `TP_Hadoop_Spark_SEHILI.zip`: the deliverable (PDF, `lab.hql`, `rdd.py`, `df.py`, `hdfs_commands.txt`).

## Outside this folder (the TP commands expect these paths)
- Tools: `~/hadoop` (3.4.3), `~/hive` (3.1.3), `~/spark` (3.5.1). Env vars at the end of `~/.bashrc`.
- Data: `~/data/{caracteristiques,lieux,vehicules,usagers}-2024.csv`.
- HDFS storage: `~/hadoop_data/`. Hive metastore: run `hive` from `~/hive_work` only.

## Version deviation
The statement asks for Hadoop 3.5.0, which needs Java 17, while Hive 3.1.3 only runs on Java 8.
We use Hadoop 3.4.3 on Java 8. Test results and errors are in the vault note "TP Hadoop Spark".

## Local fixes needed to run
- `commons-collections-3.2.2.jar` in `~/hive/lib` and `~/hive/auxlib`: Hive needs it, Hadoop 3.4.3 no longer ships it.
- `spark.locality.wait 0` in `~/spark/conf/spark-defaults.conf`: otherwise joins hang in `local[2]` (HDFS host name differs from the executor's).
- YARN capped at 3 GB, MapReduce containers at 512 MB (`yarn-site.xml`, `mapred-site.xml`).
- With `spark-submit` on YARN, pass `--master yarn` on the command line: set only in the code, `pyspark` is not shipped to the executors.

## Restart after a reboot
```bash
sudo service ssh start          # WSL only
start-dfs.sh && start-yarn.sh && jps
# before shutting down: stop-yarn.sh && stop-dfs.sh (never reformat HDFS)
```
