# TP4 JDBC : accès aux bases relationnelles en Java

M1, Bases de données avancées (Paris 8). Statement: `enonce/TP_JDBC.pdf`, course: `enonce/COURS JDBC.pdf`.

## Layout
- `sql/init.sql`: EMP and DEPT of the course (`CreationTables.txt`), dropped and reloaded on each reset.
- `src/Db.java`: connection (driver load + `DriverManager`) and a generic table printer (`ResultSetMetaData`).
- `src/Partie1ContenuEmp.java`: names and salaries, then employees with a commission.
- `src/Partie2Metadonnees.java`: tables and columns read from `DatabaseMetaData`, no name written in the code.
- `src/Partie3Manipulation.java`: questions 1 to 8 (UPDATE, INSERT, CREATE, TRUNCATE, DROP, CREATE AS SELECT).
- `lib/ojdbc11.jar`: Oracle JDBC driver 23.5, downloaded by `run.sh` from Maven Central (SHA1 checked), not in git.
- `resultats/sortie_all.txt`: output of `./run.sh all`.

## Run
Needs Java 17+ and Docker Desktop running. The SGBD is Oracle Free 23 (`gvenzl/oracle-free:23-slim`), user `tp/tp`,
service `localhost:1521/FREEPDB1`.
```bash
./run.sh up        # first time: pulls the image, creates the container, loads EMP/DEPT
./run.sh 1         # partie 1
./run.sh 2 EMP     # partie 2 (table optional, default: first table found)
./run.sh 3         # partie 3, reloads EMP/DEPT first so it can be run again
./run.sh all       # reset + the three parts
./run.sh down      # stop the container (data kept; ./run.sh up restarts it)
```

## Remarks on the statement
- Q4: `JOB CHAR(10)` cannot hold `COORDINATRICE` (13 characters), Oracle raises ORA-12899. The program runs both
  inserts in one transaction, rolls back, widens `JOB` to `CHAR(13)` and retries.
- Partie 1 Q2: "having a commission" is read as `COMM > 0`, so TURNER (`COMM = 0`) is left out. Partie 3 Q8
  ("commission renseignée") uses `COMM IS NOT NULL` and keeps him.
- Q8 uses `CREATE TABLE ... AS SELECT` with `CAST`s so PROMOTION keeps the types of Q3.
