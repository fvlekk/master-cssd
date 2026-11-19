# TP Bases de Données Distribuées : EMP and DEPT in two Oracle schemas

M1, Bases de Données Distribuées (Paris 8). Statement: `enonce/TP BD DISTRIBUÉES.pdf`.

## Layout
- `sql/1_system_users.sql` to `sql/6_user2_fk_tests.sql`: one script per step, run by the user in its name
  (SYSTEM, USER1 or USER2). Expected errors (ORA-00942, 02291, 02292, 02449) are part of the TP.
- `reponses.md`: answers to Q1 to Q9, in French (the deliverable).
- `resultats/sortie.txt`: full trace of `./run.sh all` (each statement echoed with its result).

## Run
Needs Docker Desktop running. Own container `tp-oracle-bdd` (`gvenzl/oracle-free:23-slim`), host port 1522 so it
can run next to `../tp-jdbc` (1521).
```bash
./run.sh up          # first time: creates the container (1 to 2 min)
./run.sh all         # replays the TP from scratch (drops and recreates USER1/USER2)
./run.sh sql user1   # interactive sqlplus as system, user1 or user2
./run.sh down        # stop the container
```
Passwords (local container only): `system/oracle`, `user1/user1`, `user2/user2`.
