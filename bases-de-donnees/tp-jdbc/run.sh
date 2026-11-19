#!/usr/bin/env bash
# TP JDBC: Oracle Free in Docker + the three Java programs.
# Usage: ./run.sh up | reset | 1 | 2 [TABLE] | 3 | all | down
set -euo pipefail
cd "$(dirname "$0")"

CONTAINER=tp-oracle
IMAGE=gvenzl/oracle-free:23-slim
CP="out:lib/ojdbc11.jar"
# Docker Desktop without WSL integration only puts a stub "docker" on the PATH: use the Windows client then.
DOCKER=docker
docker version >/dev/null 2>&1 || DOCKER="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"

docker_() { "$DOCKER" "$@"; }

up() {
  if [ -z "$(docker_ ps -aq -f name=^${CONTAINER}$)" ]; then
    # Local throwaway container: the passwords are not secrets.
    docker_ run -d --name "$CONTAINER" -p 1521:1521 \
      -e ORACLE_PASSWORD=oracle -e APP_USER=tp -e APP_USER_PASSWORD=tp "$IMAGE" >/dev/null
    echo "Conteneur $CONTAINER cree, premier demarrage (1 a 2 min)..."
    until docker_ logs "$CONTAINER" 2>&1 | grep -q "DATABASE IS READY TO USE"; do sleep 5; done
    reset
  else
    docker_ start "$CONTAINER" >/dev/null
    until docker_ exec "$CONTAINER" healthcheck.sh >/dev/null 2>&1; do sleep 3; done
  fi
  echo "Oracle pret sur localhost:1521/FREEPDB1 (tp/tp)"
}

reset() {
  docker_ exec -i "$CONTAINER" sqlplus -S -L tp/tp@//localhost/FREEPDB1 < sql/init.sql >/dev/null
  echo "Base reinitialisee (EMP, DEPT)"
}

JAR_URL=https://repo1.maven.org/maven2/com/oracle/database/jdbc/ojdbc11/23.5.0.24.07/ojdbc11-23.5.0.24.07.jar

# The driver is not in git: download it from Maven Central once and check its SHA1.
driver() {
  [ -f lib/ojdbc11.jar ] && return
  mkdir -p lib
  curl -fsSL -o lib/ojdbc11.jar.part "$JAR_URL"
  if [ "$(curl -fsSL "$JAR_URL.sha1")" != "$(sha1sum lib/ojdbc11.jar.part | cut -d' ' -f1)" ]; then
    rm lib/ojdbc11.jar.part; echo "SHA1 du driver incorrect" >&2; exit 1
  fi
  mv lib/ojdbc11.jar.part lib/ojdbc11.jar
}

build() { driver; javac -d out -cp lib/ojdbc11.jar src/*.java; }

case "${1:-}" in
  up)    up ;;
  reset) reset ;;
  1)     build; java -cp "$CP" Partie1ContenuEmp ;;
  2)     build; java -cp "$CP" Partie2Metadonnees "${@:2}" ;;
  3)     reset; build; java -cp "$CP" Partie3Manipulation ;;
  all)   reset; build
         for p in Partie1ContenuEmp Partie2Metadonnees Partie3Manipulation; do
           echo "===== $p ====="; java -cp "$CP" "$p"; echo
         done ;;
  down)  docker_ stop "$CONTAINER" >/dev/null && echo "Conteneur arrete" ;;
  *)     echo "Usage: $0 up | reset | 1 | 2 [TABLE] | 3 | all | down"; exit 1 ;;
esac
