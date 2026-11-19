import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

/**
 * Partie 2 : contenu d'une base sans connaissance a priori.
 * Everything comes from DatabaseMetaData, no table name is written in the code.
 * Usage: java Partie2Metadonnees [TABLE]  (default: the first table found)
 */
public class Partie2Metadonnees {
    public static void main(String[] args) throws SQLException {
        try (Connection conn = Db.connect()) {
            DatabaseMetaData meta = conn.getMetaData();
            // In Oracle a schema is the user, stored in upper case.
            String schema = meta.getUserName().toUpperCase();

            System.out.println("Base : " + meta.getDatabaseProductName() + " " + meta.getDatabaseMajorVersion()
                    + ", schema " + schema);
            System.out.println();

            List<String> tables = new ArrayList<>();
            try (ResultSet rs = meta.getTables(null, schema, "%", new String[] {"TABLE"})) {
                while (rs.next()) tables.add(rs.getString("TABLE_NAME"));
            }
            System.out.println("1. Nombre de tables : " + tables.size());
            for (String t : tables) System.out.println("  - " + t);
            if (tables.isEmpty()) return;

            String table = args.length > 0 ? args[0].toUpperCase() : tables.get(0);
            if (!tables.contains(table)) {
                System.out.println("Table " + table + " absente du schema " + schema);
                return;
            }

            List<String> columns = new ArrayList<>();
            try (ResultSet rs = meta.getColumns(null, schema, table, "%")) {
                while (rs.next()) {
                    String type = rs.getString("TYPE_NAME") + "(" + rs.getInt("COLUMN_SIZE")
                            + (rs.getInt("DECIMAL_DIGITS") > 0 ? "," + rs.getInt("DECIMAL_DIGITS") : "") + ")";
                    columns.add(String.format("%-10s %s", rs.getString("COLUMN_NAME"), type));
                }
            }
            System.out.println();
            System.out.println("2. Table " + table + " : " + columns.size() + " attribut(s)");
            for (String c : columns) System.out.println("  - " + c);
        }
    }
}
