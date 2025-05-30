package net.sf.l2j.gameserver.handler;

import net.sf.l2j.gameserver.model.actor.Player;

/**
 * @author Anarchy
 */
public interface IBypassHandler
{
	public boolean handleBypass(String bypass, Player activeChar);
	
	public String[] getBypassHandlersList();
}