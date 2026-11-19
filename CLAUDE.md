# Master CSSD: labs and projects

Public repo `fvlekk/master-cssd`. Answers and code only: teachers' PDFs go in an `enonce/` (or `sujet/`) folder, git-ignored.

## Layout (every new lab or project goes in its subject folder)
- `bases-de-donnees/`: SQL, PL/SQL, JDBC, distributed DB. Oracle Free in Docker, one `run.sh` per lab.
- `data/`: Hadoop, Hive, Spark, big data.
- `machine-learning/`: ML projects. Team projects stay in their own repo, added here as a git submodule.
- `python/`: Python labs (optimisation: simplex, simulated annealing, PSO, genetic algorithms...).
- A subject that fits none of them gets its own folder, added to the table in `README.md`.

## Working preferences
- New lab: folder `tp-<subject>` in the right subject folder, statement copied to `enonce/`, a short `README.md`
  (layout + how to run), results of the real run in `resultats/`. Add it to the root `README.md`.
- Docker Desktop has no WSL integration here: scripts fall back to `docker.exe` (see `bases-de-donnees/tp-jdbc/run.sh`).
