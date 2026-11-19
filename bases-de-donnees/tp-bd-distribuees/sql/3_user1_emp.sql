-- Run as USER1.
-- Q3. EMP in the USER1 schema.
CREATE TABLE EMP (
  EMPNO    NUMBER(4)    CONSTRAINT PK_EMP PRIMARY KEY,
  ENAME    VARCHAR2(10),
  JOB      VARCHAR2(9),
  MGR      NUMBER(4),
  HIREDATE DATE,
  SAL      NUMBER(7,2),
  COMM     NUMBER(7,2),
  DEPTNO   NUMBER(2)
);

-- Q4, first attempt: USER1 has no privilege on USER2.DEPT yet, so Oracle refuses the foreign key
-- (expected error ORA-00942: USER2.DEPT is invisible to USER1).
ALTER TABLE EMP ADD CONSTRAINT FK_EMP_DEPT FOREIGN KEY (DEPTNO) REFERENCES USER2.DEPT (DEPTNO);
EXIT;
