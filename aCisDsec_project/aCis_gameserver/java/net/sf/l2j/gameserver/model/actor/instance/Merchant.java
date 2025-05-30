package net.sf.l2j.gameserver.model.actor.instance;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.StringTokenizer;

import net.sf.l2j.Config;
import net.sf.l2j.gameserver.data.cache.HtmCache;
import net.sf.l2j.gameserver.data.manager.BuyListManager;
import net.sf.l2j.gameserver.data.xml.MultisellData;
import net.sf.l2j.gameserver.model.actor.Player;
import net.sf.l2j.gameserver.model.actor.template.NpcTemplate;
import net.sf.l2j.gameserver.model.buylist.NpcBuyList;
import net.sf.l2j.gameserver.model.item.instance.ItemInstance;
import net.sf.l2j.gameserver.network.serverpackets.BuyList;
import net.sf.l2j.gameserver.network.serverpackets.NpcHtmlMessage;
import net.sf.l2j.gameserver.network.serverpackets.SellList;
import net.sf.l2j.gameserver.network.serverpackets.ShopPreviewList;
import net.sf.l2j.gameserver.skills.L2Skill;

/**
 * An instance type extending {@link Folk}, used for merchant (regular and multisell). It got buy/sell methods.<br>
 * <br>
 * It is used as mother class for few children, such as {@link Fisherman}.
 */
public class Merchant extends Folk
{
	public Merchant(int objectId, NpcTemplate template)
	{
		super(objectId, template);
	}
	
	@Override
	public String getHtmlPath(int npcId, int val)
	{
		String filename = "";
		
		if (val == 0)
			filename = "" + npcId;
		else
			filename = npcId + "-" + val;
		
		return "data/html/merchant/" + filename + ".htm";
	}

	private static final Set<Integer> BLOCKED_SELL_ITEMS = new java.util.HashSet<>();
	private static final Set<Integer> BLOCKED_SELL_LIST_ITEMS = new java.util.HashSet<>();

	static {
		try {
			java.util.Properties props = new java.util.Properties();
			java.io.File file = new java.io.File("config/CustomMods/SpecialMods.ini");
			if (file.exists()) {
				try (java.io.FileInputStream fis = new java.io.FileInputStream(file)) {
					props.load(fis);
					// Preços zerados
					String ids = props.getProperty("Item_sell_price_block", "");
					for (String id : ids.split(",")) {
						id = id.trim();
						if (!id.isEmpty()) BLOCKED_SELL_ITEMS.add(Integer.parseInt(id));
					}
					// Itens não listados para venda
					String idsBlockList = props.getProperty("Item_sell_block_list", "");
					for (String id : idsBlockList.split(",")) {
						id = id.trim();
						if (!id.isEmpty()) BLOCKED_SELL_LIST_ITEMS.add(Integer.parseInt(id));
					}
				}
			}
		} catch (Exception e) {
			System.err.println("Erro ao carregar Item_sell_price_block ou Item_sell_block_list: " + e.getMessage());
		}
	}
	
	@Override
	public void onBypassFeedback(Player player, String command)
	{
		// Generic PK check. Send back the HTM if found and cancel current action.
		if (!Config.KARMA_PLAYER_CAN_SHOP && player.getKarma() > 0 && showPkDenyChatWindow(player, "merchant"))
			return;
		
		StringTokenizer st = new StringTokenizer(command, " ");
		String actualCommand = st.nextToken(); // Get actual command
		
		if (actualCommand.equalsIgnoreCase("Buy"))
		{
			if (st.countTokens() < 1)
				return;
			
			showBuyWindow(player, Integer.parseInt(st.nextToken()));
		}
		else if (actualCommand.equalsIgnoreCase("Sell"))
		{
			// Lista de IDs dos itens que não podem ser vendidos por adena
			final Set<Integer> blockedSellItems = BLOCKED_SELL_ITEMS;
			final Set<Integer> blockedSellListItems = BLOCKED_SELL_LIST_ITEMS;

			// Retrieve sellable items e filtra os bloqueados
			final List<ItemInstance> originalItems = player.getInventory().getSellableItems();
			final List<ItemInstance> items = new ArrayList<>(originalItems); // agora é mutável
			items.removeIf(item -> blockedSellListItems.contains(item.getItemId()));

			if (items.isEmpty())
			{
				final String content = HtmCache.getInstance().getHtm("data/html/" + ((this instanceof Fisherman) ? "fisherman" : "merchant") + "/" + getNpcId() + "-empty.htm");
				if (content != null)
				{
					final NpcHtmlMessage html = new NpcHtmlMessage(getObjectId());
					html.setHtml(content, player);
					html.replace("%objectId%", getObjectId());
					player.sendPacket(html);
					return;
				}
			}

			// Zera o valor de venda dos itens bloqueados
			for (ItemInstance item : items) {
				if (blockedSellItems.contains(item.getItemId())) {
					item.setPriceToSell(0);
				}
			}

			player.sendPacket(new SellList(player.getAdena(), items));
		}
		else if (actualCommand.equalsIgnoreCase("Wear") && Config.ALLOW_WEAR)
		{
			if (st.countTokens() < 1)
				return;
			
			showWearWindow(player, Integer.parseInt(st.nextToken()));
		}
		else if (actualCommand.equalsIgnoreCase("Multisell"))
		{
			if (st.countTokens() < 1)
				return;
			
			MultisellData.getInstance().separateAndSend(st.nextToken(), player, this, false);
		}
		else if (actualCommand.equalsIgnoreCase("Multisell_Shadow"))
		{
			final NpcHtmlMessage html = new NpcHtmlMessage(getObjectId());
			
			if (player.getStatus().getLevel() < 40)
				html.setFile("data/html/common/shadow_item-lowlevel.htm", player);
			else if (player.getStatus().getLevel() < 46)
				html.setFile("data/html/common/shadow_item_mi_c.htm", player);
			else if (player.getStatus().getLevel() < 52)
				html.setFile("data/html/common/shadow_item_hi_c.htm", player);
			else
				html.setFile("data/html/common/shadow_item_b.htm", player);
			
			html.replace("%objectId%", getObjectId());
			player.sendPacket(html);
		}
		else if (actualCommand.equalsIgnoreCase("Exc_Multisell"))
		{
			if (st.countTokens() < 1)
				return;
			
			MultisellData.getInstance().separateAndSend(st.nextToken(), player, this, true);
		}
		else if (actualCommand.equalsIgnoreCase("Newbie_Exc_Multisell"))
		{
			if (st.countTokens() < 1)
				return;
			
			if (player.isNewbie(true))
				MultisellData.getInstance().separateAndSend(st.nextToken(), player, this, true);
			else
				showChatWindow(player, "data/html/exchangelvlimit.htm");
		}
		else
			super.onBypassFeedback(player, command);
	}
	
	@Override
	public void showChatWindow(Player player, int val)
	{
		// Generic PK check. Send back the HTM if found and cancel current action.
		if (!Config.KARMA_PLAYER_CAN_SHOP && player.getKarma() > 0 && showPkDenyChatWindow(player, "merchant"))
			return;
		
		showChatWindow(player, getHtmlPath(getNpcId(), val));
	}
	
	private final void showWearWindow(Player player, int val)
	{
		final NpcBuyList buyList = BuyListManager.getInstance().getBuyList(val);
		if (buyList == null || !buyList.isNpcAllowed(getNpcId()))
			return;
		
		player.tempInventoryDisable();
		player.sendPacket(new ShopPreviewList(buyList, player.getAdena(), player.getSkillLevel(L2Skill.SKILL_EXPERTISE)));
	}
	
	protected final void showBuyWindow(Player player, int val)
	{
		final NpcBuyList buyList = BuyListManager.getInstance().getBuyList(val);
		if (buyList == null || !buyList.isNpcAllowed(getNpcId()))
			return;
		
		player.tempInventoryDisable();
		player.sendPacket(new BuyList(buyList, player.getAdena(), (getCastle() != null) ? getCastle().getTaxRate() : 0));
	}
}