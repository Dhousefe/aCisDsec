package net.sf.l2j.gameserver.handler;

import java.util.HashMap;
import java.util.Map;

import net.sf.l2j.gameserver.handler.voicedcommandhandlers.LanguageCommand;
import net.sf.l2j.gameserver.handler.voicedcommandhandlers.Shiff_Mod;

public class VoicedCommandHandler
{
	private final Map<Integer, IVoicedCommandHandler> _datatable = new HashMap<>();
	
	
	/**
	 * Singleton instance Dhousefe.
	 */
	private static VoicedCommandHandler _instance;

	public static VoicedCommandHandler getInstance()
	{
		if (SingletonHolder._instance == null)
		{
			_instance = new VoicedCommandHandler();
		}
		
		return _instance = SingletonHolder._instance;
	}
	
	protected VoicedCommandHandler()
	{
		// Register your Voiced Command Handlers here
		// Example: registerHandler(new MyVoicedCommandHandler());
		// registerHandler(new BankingSystem());
		registerHandler(new Shiff_Mod());
		registerHandler(new LanguageCommand());
	}
	
	public void registerHandler(IVoicedCommandHandler handler)
	{
		String[] ids = handler.getVoicedCommandList();
		
		for (int i = 0; i < ids.length; i++)
			_datatable.put(ids[i].hashCode(), handler);
	}
	
	/*public IVoicedCommandHandler getHandler(String voicedCommand)
	{
		String command = voicedCommand;
		
		if (voicedCommand.indexOf(" ") != -1)
			command = voicedCommand.substring(0, voicedCommand.indexOf(" "));
			VoicedCommandHandler.getInstance().getHandler(command.substring(7));
		
		return _datatable.get(command.hashCode());
	}*/

	public IVoicedCommandHandler getHandler(String voicedCommand)
	{
		String command = voicedCommand;

		// Protege contra comandos curtos ou vazios
		if (voicedCommand == null || voicedCommand.isEmpty())
			return null;

		int idx = voicedCommand.indexOf(" ");
		if (idx != -1)
			command = voicedCommand.substring(0, idx);

		return _datatable.get(command.hashCode());
	}
	
	public int size()
	{
		return _datatable.size();
	}
	
	private static class SingletonHolder
	{
		protected static final VoicedCommandHandler _instance = new VoicedCommandHandler();
	}
}
 