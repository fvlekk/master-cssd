-- Run as USER2.
-- Q7, parent side.
-- (e) department 10 still has employees: expected ORA-02292 (child record found)
DELETE FROM DEPT WHERE DEPTNO = 10;
-- (f) changing a referenced key: expected ORA-02292
UPDATE DEPT SET DEPTNO = 11 WHERE DEPTNO = 10;
-- (g) department 40 has no employee: deletion accepted, then cancelled
DELETE FROM DEPT WHERE DEPTNO = 40;
ROLLBACK;
-- (h) the table cannot be dropped while USER1.EMP references it: expected ORA-02449
DROP TABLE DEPT;

SELECT COUNT(*) AS NB_DEPT FROM DEPT;
EXIT;
