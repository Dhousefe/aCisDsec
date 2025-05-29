package net.sf.l2j.gameserver.model.item;

import net.sf.l2j.commons.random.Rnd;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Logger;

public class DropData
{
    private static final Logger LOGGER = Logger.getLogger(DropData.class.getName());

    private int itemId;
    private int minDrop;
    private int maxDrop;
    private double chance;
    private String questID;
    private String[] stateID;
    private List<DropData> drops = new ArrayList<>();

    public static final int MAX_CHANCE = 1000000;
    public static final int PERCENT_CHANCE = 1000000 / 100;

    public DropData(Integer itemId, Integer minDrop, Integer maxDrop, Double chance) {
        this.itemId = itemId;
        this.minDrop = minDrop;
        this.maxDrop = maxDrop;
        this.chance = chance;
    }

    public int getItemId() {
        return itemId;
    }

    public void setItemId(int itemId) {
        this.itemId = itemId;
    }

    public int getMinDrop() {
        return minDrop;
    }

    public void setMinDrop(int minDrop) {
        this.minDrop = minDrop;
    }

    public int getMaxDrop() {
        return maxDrop;
    }

    public void setMaxDrop(int maxDrop) {
        this.maxDrop = maxDrop;
    }

    public double getChance() {
        return chance;
    }

    public void setChance(double chance) {
        this.chance = chance;
    }

    public double chance() {
        return chance;
    }

    @Override
    public String toString()
    {
        String out = "ItemID: " + itemId + " Min: " + minDrop + " Max: " + maxDrop + " Chance: " + (chance / 10000.0) + "%";
        if (isQuestDrop())
        {
            out = out + " QuestID: " + getQuestID() + " StateID's: " + Arrays.toString(getStateIDs());
        }
        return out;
    }

    public String getQuestID()
    {
        return questID;
    }

    public String[] getStateIDs()
    {
        return stateID;
    }

    public boolean isQuestDrop()
    {
        return (questID != null) && (stateID != null);
    }

    public int getRandomDrop()
    {
        return Rnd.get(minDrop, maxDrop);
    }

    public void add(DropData dropData) {
        drops.add(dropData);
    }

    public void loadDropData(String dropAttrs) {
        final DropData data = new DropData(parseInteger(dropAttrs, "itemid"), parseInteger(dropAttrs, "min"), parseInteger(dropAttrs, "max"), parseDouble(dropAttrs, "chance"));
        LOGGER.info("Loaded drop: ItemID=" + data.getItemId() + ", Min=" + data.getMinDrop() + 
            ", Max=" + data.getMaxDrop() + ", Chance=" + data.getChance());
    }

    private Integer parseInteger(String dropAttrs, String key) {
        // Implementation for parsing integer from dropAttrs based on key
        return null;
    }

    private Double parseDouble(String dropAttrs, String key) {
        // Implementation for parsing double from dropAttrs based on key
        return null;
    }
}