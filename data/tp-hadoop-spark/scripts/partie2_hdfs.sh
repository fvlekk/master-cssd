#!/usr/bin/env bash
# Part 2: load the cleaned BAAC files into HDFS and inspect blocks and replication.
source "$(dirname "$0")/env.sh"
BASE=/user/$USER/accidents
run() { echo; echo "\$ $*"; "$@" 2>&1 | grep -v "WARN util.NativeCodeLoader"; }

for table in caracteristiques lieux vehicules usagers; do
  run hdfs dfs -mkdir -p $BASE/$table
  run hdfs dfs -put -f ~/data/clean/$table-2024.csv $BASE/$table/
done
run hdfs dfs -ls -R $BASE
run hdfs dfs -ls -h $BASE/usagers
run hdfs dfs -du -h $BASE
run hdfs dfs -count $BASE
echo; echo "\$ hdfs dfs -cat $BASE/usagers/usagers-2024.csv | head -5"
hdfs dfs -cat $BASE/usagers/usagers-2024.csv 2>/dev/null | head -5
echo; echo "\$ hdfs dfs -tail $BASE/usagers/usagers-2024.csv | tail -2"
hdfs dfs -tail $BASE/usagers/usagers-2024.csv 2>/dev/null | tail -2
run hdfs dfs -stat "%n %b octets, taille de bloc %o, replication %r" $BASE/usagers/usagers-2024.csv

run hdfs fsck $BASE -files -blocks -locations
run hdfs dfsadmin -report

run hdfs dfs -D dfs.blocksize=1048576 -put -f ~/data/clean/usagers-2024.csv /user/$USER/usagers_small_blocks.csv
run hdfs fsck /user/$USER/usagers_small_blocks.csv -files -blocks
# With a single DataNode the second replica never arrives, so -w would wait forever.
run timeout 10 hdfs dfs -setrep -w 2 /user/$USER/usagers_small_blocks.csv
run hdfs fsck /user/$USER/usagers_small_blocks.csv

run hdfs dfs -cp -f /user/$USER/usagers_small_blocks.csv /user/$USER/usagers_copy.csv
run hdfs dfs -mv /user/$USER/usagers_copy.csv $BASE/usagers_backup.csv
run hdfs dfs -get -f $BASE/usagers_backup.csv ~/usagers_from_hdfs.csv
echo; echo "\$ diff ~/data/clean/usagers-2024.csv ~/usagers_from_hdfs.csv"
diff ~/data/clean/usagers-2024.csv ~/usagers_from_hdfs.csv && echo identiques
run hdfs dfs -rm $BASE/usagers_backup.csv
run hdfs dfs -rm /user/$USER/usagers_small_blocks.csv
rm -f ~/usagers_from_hdfs.csv

run hdfs dfs -getmerge $BASE/lieux /tmp/lieux_merged.csv
echo; echo "\$ wc -l /tmp/lieux_merged.csv"; wc -l /tmp/lieux_merged.csv; rm -f /tmp/lieux_merged.csv
