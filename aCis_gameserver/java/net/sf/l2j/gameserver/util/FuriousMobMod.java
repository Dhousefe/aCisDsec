package net.sf.l2j.gameserver.util;

import java.io.FileInputStream;
import java.util.Properties;

public class FuriousMobMod {
    public static boolean ENABLED = true;
    public static double CHANCE = 0.05;
    public static String TITLE = "Furioso";
    public static int TITLE_COLOR = 0xFFA500;
    public static double HP_MULT = 2.0;
    public static double ATK_MULT = 2.0;
    public static int DROP_ITEM_ID = 57;
    public static int DROP_AMOUNT = 10000;

    static {
        try {
            Properties props = new Properties();
            props.load(new FileInputStream("config/CustomMods/SpecialMods.ini"));
            ENABLED = Boolean.parseBoolean(props.getProperty("FuriousMobEnabled", "true"));
            CHANCE = Double.parseDouble(props.getProperty("FuriousMobChance", "0.05"));
            TITLE = props.getProperty("FuriousMobTitle", "Furioso");
            TITLE_COLOR = Integer.parseInt(props.getProperty("FuriousMobTitleColor", "FFA500"), 16);
            HP_MULT = Double.parseDouble(props.getProperty("FuriousMobHpMultiplier", "2.0"));
            ATK_MULT = Double.parseDouble(props.getProperty("FuriousMobAtkMultiplier", "2.0"));
            String[] drop = props.getProperty("FuriousMobDrop", "57,10000").split(",");
            if (drop.length == 2) {
                DROP_ITEM_ID = Integer.parseInt(drop[0].trim());
                DROP_AMOUNT = Integer.parseInt(drop[1].trim());
            }
        } catch (Exception e) {
            System.err.println("Erro ao carregar FuriousMobMod: " + e.getMessage());
        }
    }
}