import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;

/** Connection to the Oracle container and a generic table printer shared by the three parts. */
final class Db {
    // Local Docker container (see run.sh). Override with DB_URL / DB_USER / DB_PASSWORD.
    static final String URL = env("DB_URL", "jdbc:oracle:thin:@//localhost:1521/FREEPDB1");
    static final String USER = env("DB_USER", "tp");
    static final String PASSWORD = env("DB_PASSWORD", "tp");

    private Db() {}

    static Connection connect() throws SQLException {
        try {
            // Step 1: load the driver. Optional since JDBC 4 (the jar registers itself), kept as the course shows it.
            Class.forName("oracle.jdbc.OracleDriver");
        } catch (ClassNotFoundException e) {
            throw new SQLException("Driver Oracle introuvable : lib/ojdbc11.jar est-il dans le classpath ?", e);
        }
        // Step 2: open the connection.
        return DriverManager.getConnection(URL, USER, PASSWORD);
    }

    /** Runs a SELECT and prints every row, whatever the columns (names read from ResultSetMetaData). */
    static void printQuery(Connection conn, String sql) throws SQLException {
        System.out.println("  SQL> " + sql);
        try (Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(sql)) {
            ResultSetMetaData md = rs.getMetaData();
            int n = md.getColumnCount();
            StringBuilder header = new StringBuilder("  ");
            for (int i = 1; i <= n; i++) header.append(String.format("%-14s", md.getColumnLabel(i)));
            System.out.println(header);
            int rows = 0;
            while (rs.next()) {
                StringBuilder line = new StringBuilder("  ");
                for (int i = 1; i <= n; i++) {
                    String v = rs.getString(i);
                    line.append(String.format("%-14s", v == null ? "NULL" : v.strip()));
                }
                System.out.println(line);
                rows++;
            }
            System.out.println("  (" + rows + " ligne(s))");
        }
    }

    private static String env(String name, String fallback) {
        String v = System.getenv(name);
        return v == null || v.isBlank() ? fallback : v;
    }
}
