-- TP Hadoop et Spark, Part 3: Hive on the cleaned BAAC 2024 files.
-- Run from ~/hive_work: hive -v -f lab.hql
SET hive.cli.print.header=true;

CREATE DATABASE IF NOT EXISTS baac;
USE baac;

DROP TABLE IF EXISTS caracteristiques;
DROP TABLE IF EXISTS lieux;
DROP TABLE IF EXISTS vehicules;
DROP TABLE IF EXISTS usagers;
DROP TABLE IF EXISTS usagers_orc;

CREATE EXTERNAL TABLE caracteristiques (
  num_acc STRING, jour INT, mois INT, an INT, hrmn STRING, lum INT,
  dep STRING, com STRING, agg INT, `int` INT, atm INT, col INT,
  adr STRING, lat STRING, `long` STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/user/falek/accidents/caracteristiques'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE lieux (
  num_acc STRING, catr INT, voie STRING, v1 STRING, v2 STRING, circ INT,
  nbv INT, vosp INT, prof INT, pr STRING, pr1 STRING, `plan` INT,
  lartpc STRING, larrout STRING, surf INT, infra INT, situ INT, vma INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/user/falek/accidents/lieux'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE vehicules (
  num_acc STRING, id_vehicule STRING, num_veh STRING, senc INT, catv INT,
  obs INT, obsm INT, choc INT, manv INT, motor INT, occutc STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/user/falek/accidents/vehicules'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE usagers (
  num_acc STRING, id_usager STRING, id_vehicule STRING, num_veh STRING,
  place INT, catu INT, grav INT, sexe INT, an_nais INT, trajet INT,
  secu1 INT, secu2 INT, secu3 INT, locp INT, actp STRING, etatp INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ';'
STORED AS TEXTFILE
LOCATION '/user/falek/accidents/usagers'
TBLPROPERTIES ('skip.header.line.count'='1');

SHOW TABLES;
DESCRIBE FORMATTED usagers;

-- Q1: accidents, vehicles and road users
SELECT 'accidents' AS tbl, COUNT(*) AS nb FROM caracteristiques
UNION ALL SELECT 'vehicules', COUNT(*) FROM vehicules
UNION ALL SELECT 'usagers', COUNT(*) FROM usagers;

-- Q2: accidents per month
SELECT mois, COUNT(*) AS nb FROM caracteristiques GROUP BY mois ORDER BY mois;

-- Q3: road users per severity, with the percentage
SELECT grav, COUNT(*) AS nb, ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM usagers GROUP BY grav ORDER BY grav;

-- Q4: top 10 departments
SELECT dep, COUNT(*) AS nb FROM caracteristiques GROUP BY dep ORDER BY nb DESC, dep LIMIT 10;

-- Q5: accidents and people killed per light condition
SELECT c.lum, COUNT(*) AS accidents, SUM(COALESCE(k.killed, 0)) AS killed
FROM caracteristiques c
LEFT JOIN (SELECT num_acc, COUNT(*) AS killed FROM usagers WHERE grav = 2 GROUP BY num_acc) k
  ON c.num_acc = k.num_acc
GROUP BY c.lum ORDER BY c.lum;

-- Q6: top 5 vehicle categories by people killed
SELECT v.catv, COUNT(*) AS killed
FROM usagers u JOIN vehicules v ON u.id_vehicule = v.id_vehicule
WHERE u.grav = 2
GROUP BY v.catv ORDER BY killed DESC, v.catv LIMIT 5;

-- Q7: average age of people killed, per sex
SELECT sexe, ROUND(AVG(2024 - an_nais), 2) AS age_moyen
FROM usagers
WHERE grav = 2 AND sexe IN (1, 2) AND an_nais > 0
GROUP BY sexe ORDER BY sexe;

-- Q8: per road category. lieux has several rows per accident, so both counts differ
SELECT l.catr, COUNT(*) AS nb_lignes, COUNT(DISTINCT l.num_acc) AS nb_accidents,
       ROUND(AVG(l.vma), 2) AS vma_moyenne
FROM caracteristiques c JOIN lieux l ON c.num_acc = l.num_acc
WHERE l.vma > 0
GROUP BY l.catr ORDER BY l.catr;

-- Q9: vehicles without any road user
SELECT COUNT(*) AS nb
FROM vehicules v LEFT JOIN usagers u ON v.id_vehicule = u.id_vehicule
WHERE u.id_vehicule IS NULL;

-- Part 3.4: ORC against CSV
CREATE TABLE usagers_orc STORED AS ORC AS SELECT * FROM usagers;
SELECT COUNT(*), AVG(2024 - an_nais) FROM usagers;
SELECT COUNT(*), AVG(2024 - an_nais) FROM usagers_orc;
EXPLAIN SELECT grav, COUNT(*) FROM usagers_orc GROUP BY grav;
