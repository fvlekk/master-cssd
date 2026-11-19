#!/usr/bin/env bash
# TP BD distribuees: Oracle Free in Docker, USER1 (EMP) and USER2 (DEPT) in the same PDB.
# Usage: ./run.sh up | all | sql USER | down
#   all       replays the TP from scratch (users dropped and recreated), output in resultats/sortie.txt
#   sql USER  interactive sqlplus as system, user1 or user2
set -euo pipefail
cd "$(dirname "$0")"

CONTAINER=tp-oracle-bdd
IMAGE=gvenzl/oracle-free:23-slim
SERVICE=//localhost/FREEPDB1
# Local throwaway container: the passwords are not secrets.
declare -A PASSWORD=([system]=oracle [user1]=user1 [user2]=user2)
# Docker Desktop without WSL integration only puts a stub "docker" on the PATH: use the Windows client then.
DOCKER=docker
docker version >/dev/null 2>&1 || DOCKER="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
docker_() { "$DOCKER" "$@"; }

up() {
  if [ -z "$(docker_ ps -aq -f name=^${CONTAINER}$)" ]; then
    # Port 1522 on the host so it can run next to the tp-jdbc container (1521).
    docker_ run -d --name "$CONTAINER" -p 1522:1521 -e ORACLE_PASSWORD="${PASSWORD[system]}" "$IMAGE" >/dev/null
    echo "Conteneur $CONTAINER cree, premier demarrage (1 a 2 min)..."
    until docker_ logs "$CONTAINER" 2>&1 | grep -q "DATABASE IS READY TO USE"; do sleep 5; done
  else
    docker_ start "$CONTAINER" >/dev/null
    until docker_ exec "$CONTAINER" healthcheck.sh >/dev/null 2>&1; do sleep 3; done
  fi
  echo "Oracle pret : localhost:1522/FREEPDB1 (system/oracle, user1/user1, user2/user2)"
}

# Copies a script into the container and runs it with echo on, so the output shows each statement and its result.
run_as() {
  local user=$1 file=$2
  echo; echo "########## $file (connecte en ${user^^}) ##########"
  { echo "SET FEEDBACK ON LINESIZE 150 PAGESIZE 100 TAB OFF"
    for c in DNAME LOC ENAME USERNAME GRANTEE COLUMN_NAME TABLE_OWNER TABLE_NAME SYNONYM_NAME R_OWNER; do
      echo "COLUMN $c FORMAT A12"
    done
    echo "COLUMN CONSTRAINT_NAME FORMAT A15"; echo "COLUMN R_CONSTRAINT_NAME FORMAT A17"
    echo "COLUMN DEFAULT_TABLESPACE FORMAT A18"; echo "COLUMN PRIVILEGE FORMAT A10"
    echo "SET ECHO ON"
    cat "sql/$file"; } | docker_ exec -i "$CONTAINER" sh -c 'cat > /tmp/script.sql'
  # Not -S: in silent mode sqlplus does not echo the statements. The login banner is cut instead.
  docker_ exec "$CONTAINER" sqlplus -L "$user/${PASSWORD[$user]}@$SERVICE" @/tmp/script.sql \
    | sed -n '/^SQL> /,$p' | grep -v '^Disconnected from\|^Version [0-9]'
}

all() {
  run_as system 1_system_users.sql
  run_as user2  2_user2_dept.sql
  run_as user1  3_user1_emp.sql
  run_as user2  4_user2_grant_insert.sql
  run_as user1  5_user1_fk_queries.sql
  run_as user2  6_user2_fk_tests.sql
}

case "${1:-}" in
  up)   up ;;
  all)  all 2>&1 | tr -d '\r' | tee resultats/sortie.txt ;;
  sql)  user=${2:-user1}; docker_ exec -it "$CONTAINER" sqlplus -L "$user/${PASSWORD[$user]}@$SERVICE" ;;
  down) docker_ stop "$CONTAINER" >/dev/null && echo "Conteneur arrete" ;;
  *)    echo "Usage: $0 up | all | sql [system|user1|user2] | down"; exit 1 ;;
esac
