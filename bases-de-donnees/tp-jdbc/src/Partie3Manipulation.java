import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Partie 3 : manipulation des donnees (UPDATE, INSERT, CREATE, TRUNCATE, DROP).
 * Changes the base: run "./run.sh reset" to reload EMP/DEPT before running it again.
 */
public class Partie3Manipulation {
    private static final int ORA_VALUE_TOO_LARGE = 12899;

    public static void main(String[] args) throws SQLException {
        try (Connection conn = Db.connect(); Statement stmt = conn.createStatement()) {

            step("1. Augmenter de 100 EUR le salaire de tous les employes");
            int n = stmt.executeUpdate("UPDATE EMP SET SAL = SAL + 100");
            System.out.println("  " + n + " employe(s) mis a jour");
            Db.printQuery(conn, "SELECT ENAME, SAL FROM EMP ORDER BY ENAME");

            step("2. Inserer (60, INFORMATIQUE, PARIS) dans DEPT");
            try (PreparedStatement ps = conn.prepareStatement("INSERT INTO DEPT (DEPTNO, DNAME, LOC) VALUES (?, ?, ?)")) {
                ps.setInt(1, 60);
                ps.setString(2, "INFORMATIQUE");
                ps.setString(3, "PARIS");
                System.out.println("  " + ps.executeUpdate() + " ligne inseree");
            }
            Db.printQuery(conn, "SELECT * FROM DEPT ORDER BY DEPTNO");

            step("3. Creer la table PROMOTION");
            stmt.executeUpdate("CREATE TABLE PROMOTION (NOM CHAR(10), JOB CHAR(10), "
                    + "SALAIRE NUMBER(7,2), COMM NUMBER(7,2))");
            System.out.println("  table PROMOTION creee");

            step("4. Inserer (MALIKA, DIRECTRICE, 5000) et (RAFIKA, COORDINATRICE, 5000)");
            insererPromotions(conn, stmt);
            Db.printQuery(conn, "SELECT * FROM PROMOTION");

            step("5. Vider la table PROMOTION");
            stmt.executeUpdate("TRUNCATE TABLE PROMOTION");
            Db.printQuery(conn, "SELECT COUNT(*) AS NB FROM PROMOTION");

            step("6. Inserer les employes dont la commission depasse 25 % du salaire");
            n = stmt.executeUpdate("INSERT INTO PROMOTION (NOM, JOB, SALAIRE, COMM) "
                    + "SELECT ENAME, JOB, SAL, COMM FROM EMP WHERE COMM > 0.25 * SAL");
            System.out.println("  " + n + " ligne(s) inseree(s)");
            Db.printQuery(conn, "SELECT * FROM PROMOTION ORDER BY NOM");

            step("7. Supprimer la table PROMOTION");
            stmt.executeUpdate("DROP TABLE PROMOTION");
            System.out.println("  table PROMOTION supprimee");

            step("8. Recreer PROMOTION avec les employes dont la commission est renseignee");
            // CREATE TABLE ... AS SELECT; the CASTs keep the column types of question 3.
            stmt.executeUpdate("CREATE TABLE PROMOTION AS SELECT CAST(ENAME AS CHAR(10)) AS NOM, "
                    + "CAST(JOB AS CHAR(10)) AS JOB, CAST(SAL AS NUMBER(7,2)) AS SALAIRE, "
                    + "CAST(COMM AS NUMBER(7,2)) AS COMM FROM EMP WHERE COMM IS NOT NULL");
            Db.printQuery(conn, "SELECT * FROM PROMOTION ORDER BY NOM");
        }
    }

    /**
     * 'COORDINATRICE' has 13 characters and JOB is CHAR(10): Oracle rejects it (ORA-12899).
     * Both rows go in one transaction, so MALIKA is not left alone on failure; then JOB is widened and we retry.
     */
    private static void insererPromotions(Connection conn, Statement stmt) throws SQLException {
        String sql = "INSERT INTO PROMOTION (NOM, JOB, SALAIRE) VALUES (?, ?, ?)";
        for (int attempt = 1; ; attempt++) {
            conn.setAutoCommit(false);
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ajouter(ps, "MALIKA", "DIRECTRICE", 5000);
                ajouter(ps, "RAFIKA", "COORDINATRICE", 5000);
                ps.executeBatch();
                conn.commit();
                System.out.println("  2 lignes inserees");
                return;
            } catch (SQLException e) {
                conn.rollback();
                if (attempt > 1 || !isValueTooLarge(e)) throw e;
                System.out.println("  Refus d'Oracle : " + e.getMessage().lines().findFirst().orElse(""));
                System.out.println("  -> rollback, puis JOB passe en CHAR(13) et on reessaie");
                stmt.executeUpdate("ALTER TABLE PROMOTION MODIFY (JOB CHAR(13))");
            } finally {
                conn.setAutoCommit(true);
            }
        }
    }

    private static void ajouter(PreparedStatement ps, String nom, String job, double salaire) throws SQLException {
        ps.setString(1, nom);
        ps.setString(2, job);
        ps.setDouble(3, salaire);
        ps.addBatch();
    }

    /** The error may come wrapped in a BatchUpdateException, so walk the chain. */
    private static boolean isValueTooLarge(SQLException e) {
        for (SQLException cur = e; cur != null; cur = cur.getNextException()) {
            if (cur.getErrorCode() == ORA_VALUE_TOO_LARGE) return true;
        }
        Throwable cause = e.getCause();
        return cause instanceof SQLException s && s.getErrorCode() == ORA_VALUE_TOO_LARGE;
    }

    private static void step(String title) {
        System.out.println();
        System.out.println(title);
    }
}
