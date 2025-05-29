/* This program is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program. If not, see <http://www.gnu.org/licenses/>.
 */
package net.sf.l2j.gameserver.handler.voicedcommandhandlers;

import java.text.DecimalFormat;
import java.util.StringTokenizer;

import net.sf.l2j.commons.lang.StringUtil;

import net.sf.l2j.Config;
import net.sf.l2j.gameserver.data.xml.IconTable;
import net.sf.l2j.gameserver.data.xml.ItemData;
import net.sf.l2j.gameserver.data.xml.NpcData;
import net.sf.l2j.gameserver.enums.DropType;
import net.sf.l2j.gameserver.handler.IVoicedCommandHandler;
import net.sf.l2j.gameserver.model.actor.Player;
import net.sf.l2j.gameserver.model.actor.template.NpcTemplate;
import net.sf.l2j.gameserver.model.item.DropCategory;
import net.sf.l2j.gameserver.model.item.DropData;
import net.sf.l2j.gameserver.network.serverpackets.ActionFailed;
import net.sf.l2j.gameserver.network.serverpackets.NpcHtmlMessage;
import net.sf.l2j.gameserver.util.I18n;

public class Shiff_Mod implements IVoicedCommandHandler {
    private final static int PAGE_LIMIT = 15;
    private static final String[] _voicedCommands = {
        "shifffmodddrop",
    };

    @Override
    public boolean useVoicedCommand(String command, Player activeChar, String target) {
        if (activeChar.isDead() || activeChar.isFakeDeath() || activeChar.getKarma() > 0 || activeChar.getPvpFlag() > 0 || activeChar.isAlikeDead() || activeChar.isFestivalParticipant() || activeChar.isInJail()
            || activeChar.isInOlympiadMode() || activeChar.isInObserverMode() || activeChar.isFlying() || activeChar.isTeleporting() || activeChar.isParalyzed()
            || activeChar.isSleeping() || activeChar.isInDuel() || activeChar.isBetrayed() || activeChar.isMounted() || activeChar.isRooted()) {
            activeChar.sendMessage(I18n.get("command.cannot.use"));
            activeChar.sendPacket(ActionFailed.STATIC_PACKET);
            return false;
        }
        if (command.startsWith("shifffmodddrop")) {
            final StringTokenizer st = new StringTokenizer(command, " ");
            st.nextToken();
            int npcId = Integer.parseInt(st.nextToken());
            int page = (st.hasMoreTokens()) ? Integer.parseInt(st.nextToken()) : 1;

            ShiffNpcDropList(activeChar, npcId, page);
        }
        return true;
    }

    @Override
    public String[] getVoicedCommandList() {
        return _voicedCommands;
    }

    private static void ShiffNpcDropList(Player activeChar, int npcId, int page) {
        final NpcTemplate npcData = NpcData.getInstance().getTemplate(npcId);
        if (npcData == null) {
            activeChar.sendMessage(I18n.get("npc.template.unknown") + npcId + ".");
            return;
        }

        final StringBuilder sb = new StringBuilder(2000);

        if (!npcData.getDropData().isEmpty()) {
            StringUtil.append(sb, "<html><title> ", npcData.getName(), " ", I18n.get("npc.drop.list.title"), " ", page, "</title><body>");
            StringUtil.append(sb, "<center><img src=\"l2ui_ch3.herotower_deco\" width=256 height=32><br>");
            StringUtil.append(sb, "<img src=\"L2UI.SquareGray\" width=280 height=1>");
            StringUtil.append(sb, "<table border=0 bgcolor=000000 width=\"290\"><tr>");
            StringUtil.append(sb, "<td align=center><font color=\"LEVEL\">", I18n.get("npc.drop.list.name.item"), "</font></td>");
            StringUtil.append(sb, "<td align=center><font color=\"FF6600\">", I18n.get("npc.drop.list.quantity.drop"), "</font></td>");
            StringUtil.append(sb, "<td align=center>", I18n.get("npc.drop.list.chance.drop"), "</td>");
            StringUtil.append(sb, "</tr></table>");
            StringUtil.append(sb, "<img src=\"L2UI.SquareGray\" width=280 height=1>");
            StringUtil.append(sb, "<br><img src=\"L2UI.SquareGray\" width=280 height=1>");

            int myPage = 1;
            int i = 0;
            int shown = 0;
            boolean hasMore = false;

            for (DropCategory cat : npcData.getDropData()) {
                if (shown == PAGE_LIMIT) {
                    hasMore = true;
                    break;
                }

                for (DropData drop : cat.getDrops()) {
                    if (myPage != page) {
                        i++;
                        if (i == PAGE_LIMIT) {
                            myPage++;
                            i = 0;
                        }
                        continue;
                    }

                    if (shown == PAGE_LIMIT) {
                        hasMore = true;
                        break;
                    }

                    DecimalFormat df2 = new DecimalFormat("##.##");

                    double ChanceInt = (drop.getChance() / 10000) * 100 * Config.RATE_DROP_ITEMS;
                    ChanceInt = (ChanceInt / (100 * Config.RATE_DROP_CURRENCY)) * DropData.PERCENT_CHANCE / Config.RATE_DROP_CURRENCY;
                    String Chance = df2.format(ChanceInt);

                    int caluleAdena = (int) (Config.RATE_DROP_CURRENCY + Config.RATE_DROP_ITEMS);

                    StringUtil.append(sb, "<table bgcolor=000000><tr>");
                    StringUtil.append(sb, "<td><img src=\"" + IconTable.getInstance().getIcon(drop.getItemId()) + "\" width=32 height=32></td><td>");
                    StringUtil.append(sb, "<table><tr><td><font color=\"LEVEL\">", ItemData.getInstance().getTemplate(drop.getItemId()).getName(), "</font>");

                    if (drop.getItemId() == 57) {
                        int minDrop = (int) (drop.getMinDrop() * Config.RATE_DROP_CURRENCY);
                        int maxDrop = (int) (drop.getMaxDrop() * Config.RATE_DROP_CURRENCY);
                        StringUtil.append(sb, "<font color=\"FF6600\"> (", minDrop, "/", maxDrop, ")</font>");
                    } else {
                        int minDrop = (int) (drop.getMinDrop() * Config.RATE_DROP_ITEMS);
                        int maxDrop = (int) (drop.getMaxDrop() * Config.RATE_DROP_ITEMS);
                        StringUtil.append(sb, "<font color=\"FF6600\"> (", minDrop, "/", maxDrop, ")</font>");
                    }
                    StringUtil.append(sb, "</td></tr>");
                    StringUtil.append(sb, "<tr><td>Rate: " + String.valueOf(Chance) + "%");

                    if (drop.isQuestDrop()) {
                        StringUtil.append(sb, " <font color=\"FFD700\">", I18n.get("npc.drop.list.quest"), "</font><img src=\"L2UI.SquareGray\" width=233 height=1>");
                    } else if (cat.getDropType() == DropType.SPOIL) {
                        StringUtil.append(sb, "<font color=\"00FF00\">", I18n.get("npc.drop.list.spoil"), "</font><img src=\"L2UI.SquareGray\" width=233 height=1>");
                    } else {
                        StringUtil.append(sb, "<font color=\"3BB9FF\">", I18n.get("npc.drop.list.drop"), "</font><img src=\"L2UI.SquareGray\" width=233 height=1>");
                    }

                    StringUtil.append(sb, "</td></tr></table></td></tr>");
                    shown++;
                }
            }

            StringUtil.append(sb, "</table>");
            StringUtil.append(sb, "<img src=\"L2UI.SquareGray\" width=280 height=1><br>");
            StringUtil.append(sb, "<img src=\"L2UI.SquareGray\" width=280 height=1>");
            StringUtil.append(sb, "<table width=\"100%\" bgcolor=000000><tr>");

            if (page > 1) {
                StringUtil.append(sb, "<td width=120><a action=\"bypass -h voiced_shifffmodddrop ", npcId, " ", page - 1, "\">", I18n.get("npc.drop.list.prev.page"), "</a></td>");
                if (!hasMore)
                    StringUtil.append(sb, "<td width=100>", I18n.get("npc.drop.list.page"), " ", page, "</td><td width=70></td></tr>");
            }

            if (hasMore) {
                if (page <= 1)
                    StringUtil.append(sb, "<td width=120></td>");

                StringUtil.append(sb, "<td width=100>", I18n.get("npc.drop.list.page"), " ", page, "</td><td width=70><a action=\"bypass -h voiced_shifffmodddrop ", npcId, " ", page + 1, "\">", I18n.get("npc.drop.list.next.page"), "</a></td></tr>");
            }
            StringUtil.append(sb, "</table>");
        } else
            StringUtil.append(sb, I18n.get("npc.drop.list.no.drops"));

        StringUtil.append(sb, "</body></html>");

        final NpcHtmlMessage html = new NpcHtmlMessage(0);
        html.setHtml(sb.toString(), null);
        activeChar.sendPacket(html);
    }

    public void addRadar(Player activeChar, int x, int y, int z) {
        activeChar.getRadarList().addMarker(x, y, z);
    }
}