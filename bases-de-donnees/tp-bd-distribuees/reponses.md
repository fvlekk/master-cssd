# TP Bases de Données Distribuées : réponses

Base utilisée : Oracle AI Database 26ai Free (23.26), PDB `FREEPDB1`, dans un conteneur Docker.
Les scripts sont dans `sql/` (un fichier par étape, exécuté avec l'utilisateur indiqué) et la trace
complète de l'exécution est dans `resultats/sortie.txt`.

## Q1. Création des utilisateurs (`1_system_users.sql`, en SYSTEM)
`CREATE USER USER1 ... QUOTA UNLIMITED ON USERS` et pareil pour USER2. Chaque utilisateur reçoit
`CREATE SESSION` et `CREATE TABLE` ; USER1 reçoit en plus `CREATE SYNONYM` (Q8).
Le quota est nécessaire : sans lui, l'utilisateur peut créer la table mais pas y insérer de lignes.

## Q2 et Q3. Tables (`2_user2_dept.sql`, `3_user1_emp.sql`)
`DEPT(DEPTNO PK, DNAME, LOC)` dans le schéma USER2, `EMP(EMPNO PK, ..., DEPTNO)` dans le schéma USER1.

## Q4. Clé étrangère entre deux schémas
Première tentative en USER1, avant toute autorisation :
```
ALTER TABLE EMP ADD CONSTRAINT FK_EMP_DEPT FOREIGN KEY (DEPTNO) REFERENCES USER2.DEPT (DEPTNO);
ORA-00942: table or view "USER2"."DEPT" does not exist
```
Pour USER1, la table d'un autre schéma n'existe pas tant que son propriétaire ne lui a donné aucun droit dessus.
USER2 accorde donc le privilège objet `REFERENCES`, qui autorise à créer une clé étrangère vers la table,
ainsi que `SELECT` pour les jointures :
```sql
GRANT REFERENCES (DEPTNO), SELECT ON DEPT TO USER1;   -- en USER2
```
La même commande `ALTER TABLE`, relancée en USER1, réussit. `USER_CONSTRAINTS` montre alors
`FK_EMP_DEPT` de type `R`, avec `R_OWNER = USER2` et `R_CONSTRAINT_NAME = PK_DEPT`.

## Q5. Données
Les 4 départements et 14 employés du cours, en convertissant `HIREDATE` en vrai type `DATE`.
USER2 insère les départements, USER1 insère les employés : chacun écrit dans sa propre table.

## Q6. Employés et leur département
```sql
SELECT E.EMPNO, E.ENAME, E.JOB, E.SAL, D.DEPTNO, D.DNAME, D.LOC
FROM EMP E JOIN USER2.DEPT D ON E.DEPTNO = D.DEPTNO
ORDER BY D.DEPTNO, E.ENAME;
```
Résultat : 14 lignes. Le département 40 (OPERATIONS) n'apparaît pas, car aucun employé n'y est rattaché.

## Q7. Tests de la clé étrangère
| Test | Utilisateur | Résultat |
|---|---|---|
| Insérer un employé dans le département 99 (inexistant) | USER1 | ORA-02291 parent key not found |
| Déplacer SMITH dans le département 99 | USER1 | ORA-02291 |
| Insérer un employé dans le département 40 | USER1 | accepté (annulé ensuite par ROLLBACK) |
| Insérer un employé avec `DEPTNO` NULL | USER1 | accepté : une clé étrangère ne vérifie que les valeurs renseignées |
| Supprimer le département 10 (il a des employés) | USER2 | ORA-02292 child record found |
| Changer le numéro du département 10 | USER2 | ORA-02292 |
| Supprimer le département 40 (sans employé) | USER2 | accepté (annulé ensuite) |
| `DROP TABLE DEPT` | USER2 | ORA-02449 : la clé primaire est référencée par une clé étrangère |

La contrainte s'applique donc des deux côtés, alors qu'elle appartient au schéma USER1. Par exemple,
USER2 ne peut ni supprimer ni renuméroter un département qui a encore des employés.

## Q8. Synonyme
```sql
CREATE SYNONYM DEPT FOR USER2.DEPT;    -- en USER1
SELECT E.ENAME, D.DNAME, D.LOC FROM EMP E JOIN DEPT D ON E.DEPTNO = D.DEPTNO WHERE D.DEPTNO = 10;
```
USER1 écrit maintenant `DEPT` au lieu de `USER2.DEPT`, et la requête n'a plus besoin de connaître le
propriétaire de la table. Le synonyme ne donne aucun droit : il fonctionne seulement parce que USER1 a déjà
le `SELECT` de la Q4. Un synonyme `PUBLIC` (privilège `CREATE PUBLIC SYNONYM`, réservé à un administrateur)
rendrait ce nom visible pour tous les utilisateurs.

## Q9. Répartition entre schémas ou entre bases distinctes

**Entre schémas d'une même base (ce TP).** Il n'y a qu'une instance, un seul dictionnaire de données
et un seul moteur de transactions. La répartition est logique : elle sépare les propriétaires et les droits,
mais les données restent au même endroit physique.
- Accès par `proprietaire.table`, sous réserve des privilèges objet (`SELECT`, `REFERENCES`...).
- Les contraintes d'intégrité entre schémas sont déclaratives : la clé étrangère de la Q4 est vérifiée
  par le moteur à chaque ordre SQL.
- Une transaction qui modifie EMP et DEPT est une transaction locale ordinaire : un seul `COMMIT`, sans
  protocole particulier.
- Les jointures sont optimisées localement, sans trafic réseau.
- Il n'y a qu'un point de panne et qu'une sauvegarde : si la base est arrêtée, les deux tables le sont aussi.

**Entre bases Oracle distinctes.** Il y a deux instances, éventuellement sur deux serveurs, chacune avec
son dictionnaire. C'est une vraie base distribuée.
- L'accès à l'autre base passe par un lien de base de données :
  `CREATE DATABASE LINK lien_site2 CONNECT TO USER2 IDENTIFIED BY ... USING 'hote:1521/service';`
  puis `SELECT ... FROM DEPT@lien_site2`.
- Le synonyme sert à la transparence de localisation : avec `CREATE SYNONYM DEPT FOR DEPT@lien_site2`,
  l'application ne sait pas sur quel site se trouve la table.
- Une clé étrangère ne peut pas référencer une table distante : Oracle n'autorise pas les contraintes
  d'intégrité référentielle déclaratives entre les nœuds d'une base distribuée. Il faut les remplacer par des
  déclencheurs (triggers), par des contrôles dans l'application, ou par une réplication locale de DEPT
  (vue matérialisée).
- Une transaction qui modifie les deux sites est une transaction distribuée. Oracle la valide par un
  commit à deux phases (2PC) : préparation sur chaque site, puis validation. Si un site tombe entre les deux
  phases, la transaction reste « in-doubt » jusqu'à sa résolution.
- Les jointures entre sites font transiter des données sur le réseau. L'optimiseur doit choisir le site
  d'exécution (indice `DRIVING_SITE`).
- Chaque site est autonome (administration, sauvegarde, panne). On peut fragmenter ou répliquer les données
  au plus près de leurs utilisateurs, mais il faut alors gérer l'indisponibilité d'un site distant.

En résumé, la répartition entre schémas organise les droits dans une seule base. La répartition entre bases
distinctes déplace les données physiquement, avec ce que cela implique : liens, transparence de
localisation, intégrité non déclarative, 2PC et coût réseau.
