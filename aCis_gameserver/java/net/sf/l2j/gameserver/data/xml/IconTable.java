package net.sf.l2j.gameserver.data.xml;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.HashMap;
import java.util.Map;

import net.sf.l2j.commons.pool.ConnectionPool;
import net.sf.l2j.commons.logging.CLogger;
// Removed unused import net.sf.l2j.commons.util.StringUtil

public class IconTable {
    private static final CLogger LOGGER = new CLogger(IconTable.class.getName());
    private static final IconTable INSTANCE = new IconTable();

    private final Map<Integer, String> _icons = new HashMap<>();

    private IconTable() {
        load();
    }

    public static IconTable getInstance() {
        return INSTANCE;
    }

    private void load() {
        try (Connection con = ConnectionPool.getConnection();
             PreparedStatement ps = con.prepareStatement("SELECT itemId, itemIcon FROM item_iconss");
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                int itemId = rs.getInt("itemId");
                String icon = rs.getString("itemIcon");
                _icons.put(itemId, icon);
            }

            LOGGER.info("Loaded {} item icons.", _icons.size());
        } catch (Exception e) {
            LOGGER.error("Failed to load item icons.", e);
        }
    }

    public String getIcon(int itemId) {
        return _icons.getOrDefault(itemId, "icon.unknown");
    }

    public void appendIconHtml(StringBuilder sb, int itemId) {
        IconTable iconTable = IconTable.getInstance(); // Obtenha a instância de IconTable
        sb.append("<td><img src=\"").append(iconTable.getIcon(itemId)).append("\" width=32 height=32></td><td>");
    }
}