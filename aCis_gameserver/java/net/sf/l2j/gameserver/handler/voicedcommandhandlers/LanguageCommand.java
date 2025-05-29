package net.sf.l2j.gameserver.handler.voicedcommandhandlers;

import net.sf.l2j.gameserver.handler.IVoicedCommandHandler;
import net.sf.l2j.gameserver.model.actor.Player;
import net.sf.l2j.gameserver.network.serverpackets.NpcHtmlMessage;
import net.sf.l2j.gameserver.util.I18n;

public class LanguageCommand implements IVoicedCommandHandler {
    private static final String[] _voicedCommands = {
        "setlang", "langon", "langoff"
    };

    @Override
    public boolean useVoicedCommand(String command, Player activeChar, String target) {
        if (command.startsWith("setlang")) {
            String[] params = target.split(" ");
            if (params.length < 2) {
                activeChar.sendMessage("Usage: .setlang <language> <country>");
                return false;
            }
            String language = params[0].trim();
            String country = params[1].trim();
            try {
                I18n.setLocale(language, country);
                activeChar.sendMessage("Language changed to: " + I18n.getCurrentLocale());
                NpcHtmlMessage.clearHtmlCache();
            } catch (IllegalArgumentException e) {
                activeChar.sendMessage("Invalid language or country parameters.");
            } catch (Exception e) {
                activeChar.sendMessage("Failed to change language. Please check the input.");
            }
            return true;
        }

        if (command.equalsIgnoreCase("langon")) {
            activeChar.setTranslationEnabled(true);
            NpcHtmlMessage.clearHtmlCache();
            activeChar.sendMessage("Tradução de HTML habilitada para você.");
            return true;
        }

        if (command.equalsIgnoreCase("langoff")) {
            activeChar.setTranslationEnabled(false);
            NpcHtmlMessage.clearHtmlCache();
            activeChar.sendMessage("Tradução de HTML desabilitada para você. Agora será exibido apenas o HTML original.");
            return true;
        }

        return false;
    }

    @Override
    public String[] getVoicedCommandList() {
        return _voicedCommands;
    }
}