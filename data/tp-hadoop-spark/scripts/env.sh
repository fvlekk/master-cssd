# Environment of the TP tools, for shells that did not load ~/.bashrc.
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop HADOOP_MAPRED_HOME=$HOME/hadoop HADOOP_CONF_DIR=$HOME/hadoop/etc/hadoop
export HIVE_HOME=$HOME/hive SPARK_HOME=$HOME/spark PYSPARK_PYTHON=$HOME/venv-tp/bin/python
export USER=${USER:-$(whoami)}
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin:$SPARK_HOME/bin
