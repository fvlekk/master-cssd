import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/** Partie 1 : contenu d'une table dont le nom est connu (EMP). */
public class Partie1ContenuEmp {
    public static void main(String[] args) throws SQLException {
        try (Connection conn = Db.connect();
             Statement stmt = conn.createStatement()) { // step 3: create the statement

            System.out.println("1. Noms et salaires de tous les employes");
            // Step 4: run the query, step 5: read the rows with while (rs.next()).
            try (ResultSet rs = stmt.executeQuery("SELECT ENAME, SAL FROM EMP ORDER BY ENAME")) {
                while (rs.next()) {
                    System.out.printf("  %-10s %8.2f%n", rs.getString("ENAME"), rs.getDouble("SAL"));
                }
            }

            System.out.println();
            System.out.println("2. Noms et salaires des employes ayant une commission");
            // COMM > 0 also excludes NULL; TURNER (COMM = 0) has no commission in practice.
            try (ResultSet rs = stmt.executeQuery(
                    "SELECT ENAME, SAL, COMM FROM EMP WHERE COMM > 0 ORDER BY ENAME")) {
                while (rs.next()) {
                    System.out.printf("  %-10s %8.2f  (commission %.2f)%n",
                            rs.getString("ENAME"), rs.getDouble("SAL"), rs.getDouble("COMM"));
                }
            }
        }
    }
}
