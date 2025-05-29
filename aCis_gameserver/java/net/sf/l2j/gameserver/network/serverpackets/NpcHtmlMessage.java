package net.sf.l2j.gameserver.network.serverpackets;

import net.sf.l2j.gameserver.data.cache.HtmCache;
import net.sf.l2j.gameserver.enums.SayType;
import net.sf.l2j.gameserver.model.actor.Player;
import net.sf.l2j.gameserver.util.I18n;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.File;
//import javax.xml.parsers.DocumentBuilder;
//import javax.xml.parsers.DocumentBuilderFactory;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.TextNode;
import org.jsoup.select.Elements;
//import org.w3c.dom.Document;
//import org.w3c.dom.Element;
//import org.w3c.dom.NodeList;
import java.util.Set;
import java.util.HashSet;
import java.util.List;
import java.util.ArrayList;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
//import java.util.Properties;
//import java.io.FileInputStream;


public final class NpcHtmlMessage extends L2GameServerPacket
{
	// Shared "config" used by Players GMs to see file directory.
	public static boolean SHOW_FILE;
	public static boolean TRANSLATION_MOD_ENABLED = true;
		
	private final int _objectId;
	
	private String _html;
	private String _file;
	
	private int _itemId = 0;
	private boolean _validate = true;

	// Adicione um cache estático no início da classe
	private static final Map<String, String> HTML_CACHE = new HashMap<>();
	
	public NpcHtmlMessage(int objectId)
	{
		_objectId = objectId;
	}
	
	@Override
	public void runImpl()
	{
		if (!_validate)
			return;
		
		final Player player = getClient().getPlayer();
		if (player == null)
			return;
		
		if (SHOW_FILE && player.isGM() && _file != null)
			player.sendPacket(new CreatureSay(SayType.ALL, "HTML", _file));
		
		player.clearBypass();
		for (int i = 0; i < _html.length(); i++)
		{
			int start = _html.indexOf("\"bypass ", i);
			int finish = _html.indexOf("\"", start + 1);
			if (start < 0 || finish < 0)
				break;
			
			if (_html.substring(start + 8, start + 10).equals("-h"))
				start += 11;
			else
				start += 8;
			
			i = finish;
			int finish2 = _html.indexOf("$", start);
			if (finish2 < finish && finish2 > 0)
				player.addBypass2(_html.substring(start, finish2).trim());
			else
				player.addBypass(_html.substring(start, finish).trim());
		}
	}
	
	@Override
	protected final void writeImpl()
	{
		writeC(0x0f);
		
		writeD(_objectId);
		writeS(_html);
		writeD(_itemId);
	}
	
	public void disableValidation()
	{
		_validate = false;
	}
	
	public void setItemId(int itemId)
	{
		_itemId = itemId;
	}
	
	public void setHtml(String text, Player player)
	{
		
		// Limite de tamanho do HTML
		if (text.length() > 8192)
		{
			_html = "<html><body>Html was too long.</body></html>";
			LOGGER.warn("An html content was too long.");
			return;
		}

		// Se o player desabilitou a tradução, envia o HTML original
		if (player != null && !player.isTranslationEnabled()) {
			_html = text;
			return;
		}
		

		// Processa o HTML para substituir as tags dinamicamente
		//HtmlProcessResult result = processHtml(text, _objectId, _file);
		HtmlProcessResult result = processHtmlWithJsoup(text, _objectId, _file);
		LOGGER.info("Valor de hasTranslation em processHtmlsoup: " + result.hasTranslation);
		_html = processHtmltags(result.html, _objectId, _file, result.hasTranslation);
	}

		/**
	 * @return the _file
	 */
	public String getFile()
	{
		return _file;
	}
	
	/**
	 * @param _file the _file to set
	 */
	public void set_file(String _file)
	{
		this._file = _file;
	}

	
	public void setFile(String filename, Player player)
	{
		
	    // Verifica se o arquivo deve ser ignorado (não processa tradução)
	    if (isIgnoredHtmlFile(filename)) {
	        LOGGER.info("Ignorando processamento de HTML: " + filename);
	        String html = HtmCache.getInstance().getHtmForce(filename);
	        if (html == null) {
	            _html = "<html><body>My HTML is missing.</body></html>";
	            LOGGER.warn("HTML file " + filename + " is missing.");
	            return;
	        }
	        this._file = filename;
	        _html = html; // Usa o HTML original, sem processar
	        return;
	    }

	    // Se o player desabilitou a tradução, envia o HTML original
	    if (player != null && !player.isTranslationEnabled()) {
	        String html = HtmCache.getInstance().getHtmForce(filename);
	        if (html == null) {
	            _html = "<html><body>My HTML is missing.</body></html>";
	            LOGGER.warn("HTML file " + filename + " is missing.");
	            return;
	        }
	        this._file = filename;
	        _html = html;
	        return;
	    }

	    // Obtém o idioma atual do jogador
	    String lang = I18n.getCurrentLocale(); // Exemplo: "pt", "en", "es"
	    String langSuffix = "_" + lang.toLowerCase().replace("-", "_");

	    // Monta o caminho do arquivo traduzido
	    int extIndex = filename.lastIndexOf(".");
	    String translatedFile;
	    if (extIndex > 0) {
	        translatedFile = filename.substring(0, extIndex) + langSuffix + filename.substring(extIndex);
	    } else {
	        translatedFile = filename + langSuffix + ".htm";
	    }

	    // Verifica se o arquivo traduzido existe
	    File file = new File(translatedFile);
	    if (file.exists()) {
	        LOGGER.info("Carregando HTML traduzido: " + translatedFile);
	        String html = HtmCache.getInstance().getHtmForce(translatedFile);
	        if (html == null) {
	            _html = "<html><body>My HTML is missing.</body></html>";
	            LOGGER.warn("HTML file " + translatedFile + " is missing.");
	            return;
	        }
	        this._file = translatedFile;
	        _html = html; // Usa o HTML traduzido diretamente, sem processar novamente
	        return;
	    }

	    // Caso não exista arquivo traduzido, segue o fluxo padrão
	    LOGGER.info("Player is requesting HTML file: " + filename);
	    String html = HtmCache.getInstance().getHtmForce(filename);

	    if (html == null) {
	        _html = "<html><body>My HTML is missing.</body></html>";
	        LOGGER.warn("HTML file " + filename + " is missing.");
	        return;
	    }

	    this._file = filename;
	    setHtml(html, player); // Processa normalmente conforme idioma e flag do player
	}

	private static Set<String> IGNORED_HTML_FILES = null;

	private static void loadIgnoredHtmlFiles() {
		if (IGNORED_HTML_FILES != null) return;
		IGNORED_HTML_FILES = new HashSet<>();
		try {
			java.util.Properties props = new java.util.Properties();
			try (java.io.FileInputStream fis = new java.io.FileInputStream("config/traducao/config.properties")) {
				props.load(fis);
				String ignoreList = props.getProperty("npc_ignore", "");
				for (String path : ignoreList.split(",")) {
					IGNORED_HTML_FILES.add(path.trim());
				}
			}
		} catch (Exception e) {
			//LOGGER.warn("Não foi possível carregar arquivos HTML ignorados.", e);
		}
	}

	private static boolean isIgnoredHtmlFile(String filename) {
		loadIgnoredHtmlFiles();
		return IGNORED_HTML_FILES.contains(filename);
	}
	
	public void replace(String pattern, String value)
	{
		_html = _html.replaceAll(pattern, value.replaceAll("\\$", "\\\\\\$"));
	}
	
	public void replace(String pattern, int value)
	{
		_html = _html.replaceAll(pattern, String.valueOf(value));
	}
	
	public void replace(String pattern, long value)
	{
		_html = _html.replaceAll(pattern, String.valueOf(value));
	}
	
	public void replace(String pattern, double value)
	{
		_html = _html.replaceAll(pattern, String.valueOf(value));
	}
	
	public void replace(String pattern, boolean value)
	{
		_html = _html.replaceAll(pattern, String.valueOf(value));
	}

	private static String extractLooseLinesForTranslationJsoup(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
    Document doc = Jsoup.parse(html);

    for (TextNode textNode : doc.textNodes()) {
        String text = textNode.text().trim();
        // Ignora textos vazios, %tags% e especiais
        if (text.isEmpty() || text.equalsIgnoreCase("quest") || text.matches("%.*%")) {
            continue;
        }
        String translationKey = generateTranslationKey(text);
        if (!I18n.containsKey(translationKey) && !translationMap.containsKey(translationKey)) {
            translationMap.put(translationKey, text);
        }
        // Substitui apenas se ainda não foi substituído
        if (!textNode.text().equals("%" + translationKey + "%")) {
            textNode.text("%" + translationKey + "%");
        }
    }

    return doc.body().html();
	}

	private static String processBodyTextsJsoup(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
    Document doc = Jsoup.parse(html);

    // Seleciona o elemento <body>
    Element body = doc.body();

    // Percorre todos os nós filhos diretos do <body>
    // Percorre todos os TextNodes do body, exceto os que estão dentro de <a>
    for (TextNode textNode : doc.body().select("*").not("a *, button *, edit *, combobox *").textNodes()) {
        	String text = textNode.text().trim();

            // Ignora textos vazios, %tags% e especiais
            if (text.isEmpty() || text.equalsIgnoreCase("quest") || text.matches("%.*%")) {
                continue;
            }

            // Gera a chave de tradução
            String translationKey = generateTranslationKey(text);

            // Ajusta a chave se necessário
            if (translationKey.startsWith("_") && translationKey.endsWith("_")) {
                translationKey = translationKey.substring(1, translationKey.length() - 1);
            }

            // Garante unicidade da chave
            if (translationMap.containsKey(translationKey)) {
                int count = tagCounter.getOrDefault(translationKey, 1);
                translationKey = translationKey + "_" + count;
                tagCounter.put(translationKey, count + 1);
            } else {
                tagCounter.put(translationKey, 1);
            }

            // Se não existe tradução, adiciona ao mapa e não substitui
            if (!I18n.containsKey(translationKey)) {
                translationMap.put(translationKey, text);
                continue;
            }

            // Substitui o texto do body por %key%
            textNode.text("%" + translationKey + "%");
        
    }

    // Retorna o HTML processado
    return doc.body().html();
	}

	private static String processHtmlLinksJsoup(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
    Document doc = Jsoup.parse(html);

    // Seleciona todos os elementos <a>
    Elements links = doc.select("a");
    for (Element link : links) {
        String originalText = link.text().trim();

		// Não processa se já está no formato %text%
    	//if (originalText.matches("%.*%")) continue;

        // Ignora textos vazios ou especiais
        if (originalText.isEmpty() || originalText.equalsIgnoreCase("quest")) {
            continue;
        }

        // Gera a chave de tradução
        String translationKey = generateTranslationKey(originalText);

        // Ajusta a chave se necessário
        if (translationKey.startsWith("_") && translationKey.endsWith("_")) {
            translationKey = translationKey.substring(1, translationKey.length() - 1);
        }

        // Garante unicidade da chave
        if (translationMap.containsKey(translationKey)) {
            int count = tagCounter.getOrDefault(translationKey, 1);
            translationKey = translationKey + "_" + count;
            tagCounter.put(translationKey, count + 1);
        } else {
            tagCounter.put(translationKey, 1);
        }

        // Se não existe tradução, adiciona ao mapa e não substitui
        if (!I18n.containsKey(translationKey)) {
            translationMap.put(translationKey, originalText);
            continue;
        }

		// Substitui apenas se ainda não foi substituído
        if (!link.text().equals("%" + translationKey + "%")) {
            link.text("%" + translationKey + "%");
			// Substitui o texto do link por %key%
        	//link.text("%" + translationKey + "%");
        }

        
    }

    // Retorna o HTML processado
    return doc.body().html();
	}

	private static String padronizarHtmlComJsoup(String html) {
    // 1. Parse o HTML com jsoup
    Document doc = Jsoup.parse(html);

    // 2. Remove todas as tags <font color="..."> mas mantém o texto interno
    doc.select("font").forEach(font -> font.unwrap());

    // 3. Para cada nó de texto, aplique as substituições desejadas
    for (TextNode textNode : doc.textNodes()) {
        String text = textNode.text();
        // Padronização igual ao seu fluxo:
        text = text.replaceAll("([A-Za-z])'s", "$1s");
        //text = text.replace("'", "");
		// Remove vírgulas de números (ex: 50,000 -> 50000)
        //text = text.replaceAll("(\\d),(\\d)", "$1$2");
		// Remove espacos duplos (  )
        //text = text.replaceAll(" +", " ");
        textNode.text(text);
    }

    // 4. Retorne o HTML processado
    return doc.body().html();
	}

	private static HtmlProcessResult processHtmlWithJsoup(String html, int objectId, String htmlFilePath) {
    // Padronização inicial (igual ao seu fluxo atual)
    html = padronizarHtmlComJsoup(html);
	

    String lang = I18n.getCurrentLocale();
    String cacheKey = html + "#" + objectId + "#" + lang;
    if (HTML_CACHE.containsKey(cacheKey)) {
        return new HtmlProcessResult(HTML_CACHE.get(cacheKey), false);
    }

    Map<String, String> translationMap = new HashMap<>();
    Map<String, Integer> tagCounter = new HashMap<>();

    // Parse o HTML com jsoup
    Document doc = Jsoup.parse(html);

    // Remove todas as tags <font color="LEVEL">
    doc.select("font[color=LEVEL]").unwrap();

    // Substitui todos os textos visíveis por tags de tradução
    

	// Atualize o html com o conteúdo do doc após as substituições!
    html = doc.body().html();
	// Processa os links <a> para tradução
	html = processHtmlLinksJsoup(html, translationMap, tagCounter);

	// Processa os textos soltos fora de tags
	html = processBodyTextsJsoup(html, translationMap, tagCounter);

	// Processa as tags <font color="LEVEL"> para tradução
	//html = extractLooseLinesForTranslationJsoup(html, translationMap, tagCounter);

    html = formatLinks(html);
	//html = formatLinksJsoup(html);

	html = html.replace("<html>", "")
	        .replace("</html>", "")
	        .replace("<body>", "")
	        .replace("</body>", "")
			.replace("<center>", "")
	        .replace("</center>", "");

	html = String.format(
	        "<html>\n<body>\n<center>\n<title>%%title%%</title>\n%s\n<img src=\"L2UI.SquareWhite\" width=\"300\" height=\"1\">\n<!-- L2jBrasil By Dhousefe -->\n</center>\n</body>\n</html>",
	        html
	);

    boolean hasTranslation = saveTranslationsToFile(translationMap, htmlFilePath);
    LOGGER.info("Valor de hasTranslation em processHtmlWithJsoup: " + hasTranslation);

    if (hasTranslation) {
        StringBuilder logBuilder = new StringBuilder("Tags de tradução geradas em processHtmlWithJsoup: ");
        for (Map.Entry<String, String> entry : translationMap.entrySet()) {
            logBuilder.append("\n  %").append(entry.getKey()).append("% = ").append(entry.getValue());
        }
        LOGGER.info(logBuilder.toString());
    } else {
        LOGGER.info("Nenhuma tag de tradução foi gerada em processHtmlWithJsoup para este HTML.");
		// Salva no cache antes de retornar
    	HTML_CACHE.put(cacheKey, html);
    }

	//processedHtml = formatLinksJsoup(processedHtml);
   

    
    return new HtmlProcessResult(html, hasTranslation);
	}

	private static String formatLinksJsoup(String html) {
    Document doc = Jsoup.parse(html);

    // Seleciona todos os elementos <a>
    Elements links = doc.select("a");
    for (Element link : links) {
        String linkText = link.text().trim();

        // Remove <font ...> do texto do link, mantendo apenas o texto interno
        Elements fonts = link.select("font");
        for (Element font : fonts) {
            font.unwrap();
        }
        linkText = link.text().trim();

        // Remove aspas duplas no início e no final
        if (linkText.startsWith("\"") && linkText.endsWith("\"") && linkText.length() > 1) {
            linkText = linkText.substring(1, linkText.length() - 1);
        }

        // Extrai o valor do atributo action
        String action = link.hasAttr("action") ? link.attr("action") : "";
        // Se não encontrar, tenta extrair manualmente do atributo HTML
        if (action.isEmpty()) {
            String outerHtml = link.outerHtml();
            Matcher actionMatcher = Pattern.compile("action\\s*=\\s*\"([^\"]+)\"").matcher(outerHtml);
            if (actionMatcher.find()) {
                action = actionMatcher.group(1);
            }
        }

        // Define o tipo de botão conforme o tamanho do texto
        String buttonFormat;
        int len = linkText.length();
        if (len <= 8) {
            buttonFormat = "<button width=48 height=13 back=\"L2UI_ch3.smallbutton1_over\" fore=\"L2UI_ch3.smallbutton1\" action=\"%s\" value=\"%s\">";
        } else if (len <= 11) {
            buttonFormat = "<button width=65 height=13 back=\"L2UI_ch3.smallbutton2_over\" fore=\"L2UI_ch3.smallbutton2\" action=\"%s\" value=\"%s\">";
        } else if (len <= 16) {
            buttonFormat = "<button width=95 height=13 back=\"L2UI_ch3.bigbutton_over\" fore=\"L2UI_ch3.bigbutton\" action=\"%s\" value=\"%s\">";
        } else if (len <= 20) {
            buttonFormat = "<button width=133 height=13 back=\"L2butom.bigbutton3_over\" fore=\"L2butom.bigbutton3\" action=\"%s\" value=\"%s\">";
        } else if (len <= 46) {
            buttonFormat = "<button width=238 height=13 back=\"L2butom.bitbuttom7_over\" fore=\"L2butom.bitbuttom7\" action=\"%s\" value=\"%s\">";
        } else {
            buttonFormat = "<button width=238 height=19 back=\"L2butom.bitbuttom8_over\" fore=\"L2butom.bitbuttom8\" action=\"%s\" value=\"%s\">";
        }

        String button = String.format(buttonFormat, action, linkText);

        // Remove aspas duplas duplicadas em value=""
        button = button.replaceAll("value=\"\"([^\"]+)\"\"", "value=\"$1\"");
        button = button.replaceAll("value=\"\"([^\"]+)\"\"", "value=\"$1\"");

        // Substitui o <a> pelo <button>
        link.after(button);
        link.remove();
    }

    return doc.body().html();
	}
	
	private static HtmlProcessResult processHtml(String html, int objectId, String htmlFilePath) {
		// Remove todas as tags <font color="...">...</font> e deixa apenas o texto interno
		html = html.replaceAll("<font\\s+color\\s*=\\s*\"[^\"]+\">(.*?)</font>", "$1");

		// Remove 's após palavras (ex: Lord's -> Lords)
		html = html.replaceAll("([A-Za-z])'s", "$1s");

		// Remove apóstrofos isolados
		html = html.replace("'", "");

		// Remove vírgulas de números (ex: 50,000 -> 50000)
		html = html.replaceAll("(\\d),(\\d)", "$1$2");

		// Remove espaços duplos
		html = html.replaceAll(" +", " ");

	    // Usa o texto original + objectId como chave de cache (ajuste se necessário)
	    String lang = I18n.getCurrentLocale(); // Exemplo: "pt_BR", "en_US", etc.
		String cacheKey = html + "#" + objectId + "#" + lang;
	    if (HTML_CACHE.containsKey(cacheKey)) {
	        return new HtmlProcessResult(HTML_CACHE.get(cacheKey), false);
	    }

	    Map<String, String> translationMap = new HashMap<>();
	    Map<String, Integer> tagCounter = new HashMap<>();

	    html = processHtmlLinks(html, translationMap, tagCounter);
		html = processFontLevelTags(html, translationMap, tagCounter);
		//html = extractLooseLinesForTranslation(html, translationMap, tagCounter);

	    Pattern pattern = Pattern.compile(">([^<]*)<");
	    Matcher matcher = pattern.matcher(html);

	    while (matcher.find()) {
	        String originalText = matcher.group(1).trim();
	        if (originalText.isEmpty()) continue;
	        if (originalText.equalsIgnoreCase("quest")) continue;

	        int maxTagLength = 216;
	        while (originalText.length() > 0) {
	            String part = originalText.substring(0, Math.min(maxTagLength, originalText.length()));
	            originalText = originalText.length() > maxTagLength ? originalText.substring(maxTagLength) : "";
	            String translationKey = generateTranslationKey(part);
	            if (translationKey.startsWith("_") && translationKey.endsWith("_")) {
	                translationKey = translationKey.substring(1, translationKey.length() - 1);
	            }
	            if (translationMap.containsKey(translationKey)) {
	                int count = tagCounter.getOrDefault(translationKey, 1);
	                translationKey = translationKey + "_" + count;
	                tagCounter.put(translationKey, count + 1);
	            } else {
	                tagCounter.put(translationKey, 1);
	            }
	            if (!I18n.containsKey(translationKey)) {
	                //LOGGER.warn("Translation for key '" + translationKey + "' not found. Adding to translations file.");
	                translationMap.put(translationKey, part);
	                continue;
	            }
	            html = html.replace(part, "%" + translationKey + "%");
	        }
	    }
		// Remove chaves inválidas do translationMap antes de salvar
		translationMap.entrySet().removeIf(entry ->
			entry.getKey() == null ||
			entry.getKey().isEmpty() ||
			entry.getKey().equals("%") ||
			entry.getKey().equals("%%")
		);

		// Log para mostrar as tags de tradução geradas
		boolean hasTranslation = !translationMap.isEmpty();
		LOGGER.info("Valor de hasTranslation em processHtml: " + hasTranslation);
    	
		if (hasTranslation) {
			StringBuilder logBuilder = new StringBuilder("Tags de tradução geradas em processHtml: ");
			for (Map.Entry<String, String> entry : translationMap.entrySet()) {
				logBuilder.append("\n  %").append(entry.getKey()).append("% = ").append(entry.getValue());
			}
			LOGGER.info(logBuilder.toString());
		} else {
			LOGGER.info("Nenhuma tag de tradução foi gerada em processHtml para este HTML.");
		}


		saveTranslationsToFile(translationMap, htmlFilePath);

	    html = formatLinks(html);

	    html = html.replace("<html>", "")
	        .replace("</html>", "")
	        .replace("<body>", "")
	        .replace("</body>", "");

	    html = String.format(
	        "<html>\n<body>\n<center>\n<title>%%title%%</title>\n%s\n<img src=\"L2UI.SquareWhite\" width=\"300\" height=\"1\">\n<!-- L2jBrasil By Dhousefe -->\n</center>\n</body>\n</html>",
	        html
	    );

	    //LOGGER.info("Final processed HTML: " + html);

	    // Salva no cache antes de retornar
	    HTML_CACHE.put(cacheKey, html);

	    return new HtmlProcessResult(html, hasTranslation);
	}

	public static void clearHtmlCache() {
		HTML_CACHE.clear();
	}

	private static String processHtmlLinks(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
	    // Expressão regular para capturar textos dentro de tags <a>
	    Pattern pattern = Pattern.compile("<a[^>]*>(.*?)</a>");
	    Matcher matcher = pattern.matcher(html);

	    // Processa cada texto encontrado dentro das tags <a>
	    while (matcher.find()) {
	        String originalText = matcher.group(1).trim(); // Captura o texto entre <a> e </a>

	        // Ignora textos vazios ou espaços
	        if (originalText.isEmpty()) {
	            continue;
	        }

	        // Verifica se o texto é exatamente "%quest%" e ignora
	        if (originalText.equalsIgnoreCase("quest")) {
	            LOGGER.info("Ignoring tag '%quest%' inside <a> to preserve quest system functionality.");
	            continue; // Não processa a tag %quest%
	        }

	        // Gera uma chave de tradução única para o texto
	        String translationKey = generateTranslationKey(originalText);

	        // Ajusta a chave se começar e terminar com "_"
	        if (translationKey.startsWith("_") && translationKey.endsWith("_")) {
	            translationKey = translationKey.substring(1, translationKey.length() - 1);
	        }

	        // Verifica se a chave já foi gerada anteriormente
	        if (translationMap.containsKey(translationKey)) {
	            // Incrementa o contador para gerar uma nova chave única
	            int count = tagCounter.getOrDefault(translationKey, 1);
	            translationKey = translationKey + "_" + count;
	            tagCounter.put(translationKey, count + 1);
	        } else {
	            // Inicializa o contador para a nova chave
	            tagCounter.put(translationKey, 1);
	        }

	        // Verifica se a tradução existe no arquivo de propriedades
	        if (!I18n.containsKey(translationKey)) {
	            //LOGGER.warn("Translation for key '" + translationKey + "' not found. Adding to translations file.");
	            translationMap.put(translationKey, originalText); // Salva no mapa de traduções
	            continue; // Não substitui o texto original no HTML
	        }

	        // Substitui o texto original pela chave no HTML
	        html = html.replace(originalText, "%" + translationKey + "%");

	        
	    }

	    return html;
	}

	/**
	 * Captura textos entre <font color="LEVEL">...</font> e adiciona ao translationMap,
	 * seguindo o mesmo fluxo de processHtmlLinks.
	 */
	private static String processFontLevelTags(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
		Pattern pattern = Pattern.compile("<font\\s+color\\s*=\\s*\"LEVEL\">(.*?)</font>", Pattern.CASE_INSENSITIVE | Pattern.DOTALL);
		Matcher matcher = pattern.matcher(html);

		while (matcher.find()) {
			String originalText = matcher.group(1).trim();

			// Ignora textos vazios
			if (originalText.isEmpty()) {
				continue;
			}

			// Gera uma chave de tradução única para o texto
			String translationKey = generateTranslationKey(originalText);

			// Ajusta a chave se começar e terminar com "_"
			if (translationKey.startsWith("_") && translationKey.endsWith("_")) {
				translationKey = translationKey.substring(1, translationKey.length() - 1);
			}

			// Verifica se a chave já foi gerada anteriormente
			if (translationMap.containsKey(translationKey)) {
				int count = tagCounter.getOrDefault(translationKey, 1);
				translationKey = translationKey + "_" + count;
				tagCounter.put(translationKey, count + 1);
			} else {
				tagCounter.put(translationKey, 1);
			}

			// Verifica se a tradução existe no arquivo de propriedades
			if (!I18n.containsKey(translationKey)) {
				translationMap.put(translationKey, originalText); // Salva no mapa de traduções
				continue; // Não substitui o texto original no HTML
			}

			// Substitui o texto original pela chave no HTML
			html = html.replace(matcher.group(0), "%" + translationKey + "%");
		}

		return html;
	}

	/**
	 * Extrai frases soltas (inclusive as que começam com - ou estão fora de tags) para tradução.
	 * Substitui no HTML por %key% se ainda não foi substituído.
	 */
	private static String extractLooseLinesForTranslation(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
		// Divide por <br1>, <br> ou quebra de linha
		String[] lines = html.split("<br1>|<br>|\\n");
		for (String line : lines) {
			// Remove tags HTML e espaços extras
			String cleanLine = line.replaceAll("<[^>]+>", "").trim();
			if (!cleanLine.isEmpty() && !cleanLine.equalsIgnoreCase("quest")) {
				String translationKey = generateTranslationKey(cleanLine);
				if (!I18n.containsKey(translationKey) && !translationMap.containsKey(translationKey)) {
					translationMap.put(translationKey, cleanLine);
				}
				// Substitui apenas se ainda não foi substituído
				if (html.contains(cleanLine)) {
					html = html.replace(cleanLine, "%" + translationKey + "%");
				}
			}
		}
		return html;
	}

	private static final String BUTTON_CONFIG_FILE = "config/traducao/config.properties";
	private static int[] BUTTON_LENGTHS = {8, 11, 14, 18, 46, Integer.MAX_VALUE};
	private static List<ButtonConfig> BUTTON_CONFIGS = null;

	private static class ButtonConfig {
		int width, height;
		String imgBack, imgFore;
		ButtonConfig(int width, int height, String imgBack, String imgFore) {
			this.width = width;
			this.height = height;
			this.imgBack = imgBack;
			this.imgFore = imgFore;
		}
	}

	private static void loadButtonConfigs() {
		if (BUTTON_CONFIGS != null) return;
		BUTTON_CONFIGS = new ArrayList<>();
		List<Integer> lengths = new ArrayList<>();
		try {
			java.util.Properties props = new java.util.Properties();
			try (java.io.FileInputStream fis = new java.io.FileInputStream(BUTTON_CONFIG_FILE)) {
				props.load(fis);
				for (int i = 1; i <= 6; i++) {
					int width = Integer.parseInt(props.getProperty("botao_" + i + "_width", "48"));
					int height = Integer.parseInt(props.getProperty("botao_" + i + "_height", "13"));
					String imgBack = props.getProperty("botao_" + i + "_img_back", "");
					String imgFore = props.getProperty("botao_" + i + "_img_fore", "");
					int length = Integer.parseInt(props.getProperty("botao_" + i + "_length", String.valueOf(BUTTON_LENGTHS[i-1])));
					BUTTON_CONFIGS.add(new ButtonConfig(width, height, imgBack, imgFore));
					lengths.add(length);
				}
			}
			// Atualiza BUTTON_LENGTHS com os valores do config
			BUTTON_LENGTHS = lengths.stream().mapToInt(Integer::intValue).toArray();
		} catch (Exception e) {
			LOGGER.warn("Não foi possível carregar configurações de botões.", e);
			// fallback padrão
			BUTTON_CONFIGS.clear();
			BUTTON_CONFIGS.add(new ButtonConfig(48, 13, "L2UI_ch3.smallbutton1_over", "L2UI_ch3.smallbutton1"));
			BUTTON_CONFIGS.add(new ButtonConfig(65, 13, "L2UI_ch3.smallbutton2_over", "L2UI_ch3.smallbutton2"));
			BUTTON_CONFIGS.add(new ButtonConfig(95, 13, "L2UI_ch3.bigbutton_over", "L2UI_ch3.bigbutton"));
			BUTTON_CONFIGS.add(new ButtonConfig(133, 13, "L2butom.bigbutton3_over", "L2butom.bigbutton3"));
			BUTTON_CONFIGS.add(new ButtonConfig(238, 13, "L2butom.bitbuttom7_over", "L2butom.bitbuttom7"));
			BUTTON_CONFIGS.add(new ButtonConfig(238, 19, "L2butom.bitbuttom8_over", "L2butom.bitbuttom8"));
			BUTTON_LENGTHS = new int[]{8, 11, 14, 18, 46, Integer.MAX_VALUE};
		}
	}

	private static String formatLinks(String html) {
    // Se já contém <button>, <edit> ou <combobox>, não formata
    if (html.contains("<button") || html.contains("<edit") || html.contains("<combobox")) {
        return html;
    }

    loadButtonConfigs();

    Pattern pattern = Pattern.compile("<a([^>]*)>(.*?)</a>");
    Matcher matcher = pattern.matcher(html);
    StringBuffer sb = new StringBuffer();

    while (matcher.find()) {
        String aAttributes = matcher.group(1).trim();
        String linkText = matcher.group(2).trim();

        // Remove <font color="...">...</font> se existir, deixando apenas o texto interno
        linkText = linkText.replaceAll("<font\\s+color\\s*=\\s*\"[^\"]+\">(.*?)</font>", "$1");
        linkText = linkText.replaceAll("<font\\s+color\\s*=\\s*\"LEVEL\">(.*?)</font>", "$1");

        // Remove aspas duplas no início e no final
        if (linkText.startsWith("\"") && linkText.endsWith("\"") && linkText.length() > 1) {
            linkText = linkText.substring(1, linkText.length() - 1);
        }

        // Extrai o valor do atributo action
        String action = "";
        Matcher actionMatcher = Pattern.compile("action\\s*=\\s*\"([^\"]+)\"").matcher(aAttributes);
        if (actionMatcher.find()) {
            action = actionMatcher.group(1);
        }

        // Escolhe o botão conforme o tamanho do texto
        int len = linkText.length();
        ButtonConfig btnCfg = BUTTON_CONFIGS.get(0);
        int[] limits = BUTTON_LENGTHS;
        for (int i = 0; i < limits.length; i++) {
            if (len <= limits[i]) {
                btnCfg = BUTTON_CONFIGS.get(i);
                break;
            }
        }

        String button = String.format(
            "<button width=%d height=%d back=\"%s\" fore=\"%s\" action=\"%s\" value=\"%s\">",
            btnCfg.width, btnCfg.height, btnCfg.imgBack, btnCfg.imgFore, action, linkText
        );

        // Remove aspas duplas duplicadas em value=""
        button = button.replaceAll("value=\"\"([^\"]+)\"\"", "value=\"$1\"");
        button = button.replaceAll("value=\"\"([^\"]+)\"\"", "value=\"$1\"");

        matcher.appendReplacement(sb, Matcher.quoteReplacement(button));
    }
    matcher.appendTail(sb);
    html = sb.toString();

    return html;
}
	
	private static String generateTranslationKey(String originalText) {
    // Padroniza números e apóstrofos
    originalText = originalText.replaceAll("(\\d),(\\d)", "$1$2")
                               .replace("'", "")
                               .replace("-", "")
                               .replace("<br1>", "<br>");

    // Permite números e pontos no início da chave
    String key = originalText.toLowerCase().replaceAll("[^a-z0-9\\.]", "_");

    // Remove múltiplos "_" consecutivos
    key = key.replaceAll("_+", "_");

    // Remove "_" do início e do final da chave
    if (key.startsWith("_")) {
        key = key.substring(1);
    }
    if (key.endsWith("_")) {
        key = key.substring(0, key.length() - 1);
    }

    // Ajuste para transformar "1._qualifying_to_participate" em "1. qualifying_to_participate"
    key = key.replaceAll("\\._", "_");

	// Ajuste para transformar "1._qualifying_to_participate" em "1. qualifying_to_participate"
    key = key.replaceAll("\\.", "");

    return key;
	}

	/**
 * Gera uma chave de tradução preservando o máximo da originalidade do texto,
 * removendo apenas o que pode causar bugs (acentos, caracteres especiais perigosos, etc).
 * Mantém números, pontos, espaços e letras.
 */
private static String generateTranslationKeyJsoup(String originalText) {
    if (originalText == null) return "";

    // Remove tags HTML, se houver
    originalText = originalText.replaceAll("<[^>]+>", "");

    // Remove acentos e normaliza para ASCII puro
    originalText = java.text.Normalizer.normalize(originalText, java.text.Normalizer.Form.NFD)
        .replaceAll("[\\p{InCombiningDiacriticalMarks}]", "");

    // Remove aspas simples e duplas
    originalText = originalText.replace("'", "").replace("\"", "");

    // Remove caracteres de controle e invisíveis
    originalText = originalText.replaceAll("[\\p{Cntrl}]", "");

    // Mantém letras, números, pontos, espaços e underline
    // Remove outros caracteres especiais (exceto ponto e espaço)
    String key = originalText.replaceAll("[^a-zA-Z0-9\\.\\s]", "");

    // Troca múltiplos espaços por um só e trim
    key = key.replaceAll("\\s+", " ").trim();

    // Converte para minúsculo
    key = key.toLowerCase();

    // Troca espaços por underline para ser seguro como chave
    key = key.replace(" ", "_");

    // Remove underlines duplicados
    key = key.replaceAll("_+", "_");

    // Remove underline do início e fim
    if (key.startsWith("_")) key = key.substring(1);
    if (key.endsWith("_")) key = key.substring(0, key.length() - 1);

    return key;
	}
	
	private static String generateShorterKey(String originalText) {
	    // Gera uma chave mais curta baseada no hash do texto original
	    return "key_" + originalText.hashCode();
	}
	
	private static boolean saveTranslationsToFile(Map<String, String> translationMap, String htmlFilePath) {
    Set<String> existingKeys = new HashSet<>();
    File file = new File("translations.properties");
    boolean hasTranslation = false;

    // Carrega as chaves já existentes no arquivo
    if (file.exists()) {
        try {
            List<String> lines = Files.readAllLines(file.toPath());
            for (String line : lines) {
                line = line.trim();
                if (!line.isEmpty() && !line.startsWith("#") && line.contains("=")) {
                    String key = line.substring(0, line.indexOf('=')).trim();
                    String value = line.substring(line.indexOf('=') + 1).trim();
                    existingKeys.add(key);
                    // Se a chave existe mas o valor está vazio, ainda precisa traduzir
                    if (translationMap.containsKey(key) && (value.isEmpty() || value.equals(translationMap.get(key)))) {
                        hasTranslation = true;
                    }
                }
            }
        } catch (IOException e) {
            //LOGGER.warn("Failed to read existing translations.", e);
        }
    }

    // Filtra apenas as chaves novas
    Map<String, String> newTranslations = new HashMap<>();
    for (Map.Entry<String, String> entry : translationMap.entrySet()) {
        if (!existingKeys.contains(entry.getKey())) {
            newTranslations.put(entry.getKey(), entry.getValue());
            hasTranslation = true; // Vai salvar algo novo, então precisa traduzir
        }
    }

    // Se não há novas traduções, só retorna se precisa traduzir algo
    if (newTranslations.isEmpty()) {
        return hasTranslation;
    }

    // Salva apenas as novas traduções
    try (BufferedWriter translationsWriter = new BufferedWriter(new FileWriter(file, true))) {
        if (htmlFilePath != null && !htmlFilePath.isEmpty()) {
            translationsWriter.write("# Extracted from: " + htmlFilePath);
            translationsWriter.newLine();
        }
        for (Map.Entry<String, String> entry : newTranslations.entrySet()) {
            String key = entry.getKey();
            String value = entry.getValue();
            if (key == null || key.isEmpty()) continue;
            translationsWriter.write(key + "=" + value);
            translationsWriter.newLine();
        }
    } catch (IOException e) {
        //LOGGER.warn("Failed to save translations to file.", e);
    }
    return true;
	}

	private static String processHtmltags(String html, int objectId, String _file, boolean hasTranslation) {
	    // Expressão regular para encontrar as chaves no formato %chave%
	    Pattern pattern = Pattern.compile("%(.*?)%");
	    Matcher matcher = pattern.matcher(html);

	    // Conjunto para rastrear tags já processadas
	    Set<String> processedKeys = new HashSet<>();

	    // Lista para armazenar tags não processadas
	    List<String> unprocessedKeys = new ArrayList<>();

	    // Itera sobre todas as chaves encontradas no HTML
	    while (matcher.find()) {
	        String key = matcher.group(1); // Exemplo: npc_name

	        // Ignora a tag %quest% para não afetar o sistema de quests
	        if (key.equalsIgnoreCase("quest")) {
	            continue; // Não processa a tag %quest%
	        }

	        // Ignora a tag %objectId% para preservar seu funcionamento
	        if (key.equalsIgnoreCase("objectId")) {
	            continue; // Não processa a tag %objectId%
	        }

	        // Verifica se a tag já foi processada
	        if (processedKeys.contains(key)) {
	            continue; // Ignora se já foi processada
	        }

	        // Busca a tradução diretamente no I18n
	        String translatedValue = I18n.get(key);

			// Remove aspas duplas no início e no final, se existirem
			if (translatedValue != null && translatedValue.length() > 1) {
				if ((translatedValue.startsWith("\"") && translatedValue.endsWith("\"")) ||
					(translatedValue.startsWith("[\"") && translatedValue.endsWith("\"]"))) {
					translatedValue = translatedValue.substring(1, translatedValue.length() - 1);
				}
				// Remove colchetes [texto] ou ["texto"]
				if ((translatedValue.startsWith("[") && translatedValue.endsWith("]"))) {
					translatedValue = translatedValue.substring(1, translatedValue.length() - 1);
					// Se após remover colchetes ainda houver aspas, remova também
					if (translatedValue.startsWith("\"") && translatedValue.endsWith("\"") && translatedValue.length() > 1) {
						translatedValue = translatedValue.substring(1, translatedValue.length() - 1);
					}
				}
			}

	        if (translatedValue.equals("!" + key + "!")) {
	            unprocessedKeys.add(key); // Adiciona à lista de tags não processadas
	        } else {
	            //LOGGER.info("Replacing tag: %" + key + "% with value: " + translatedValue);
	            html = html.replace("%" + key + "%", translatedValue); // Substitui a chave pelo valor traduzido
	            processedKeys.add(key); // Marca a tag como processada
	        }
	    }

	    // Processa as tags não processadas
	    for (String key : unprocessedKeys) {
	        //LOGGER.info("Processing unprocessed tag: %" + key + "%");
	        String translatedValue = I18n.get(key);

	        if (!translatedValue.equals("!" + key + "!")) {
	            //LOGGER.info("Replacing unprocessed tag: %" + key + "% with value: " + translatedValue);
	            html = html.replace("%" + key + "%", translatedValue); // Substitui a chave pelo valor traduzido
	            processedKeys.add(key); // Marca a tag como processada
	        } else {
	            //LOGGER.warn("Translation for unprocessed key '" + key + "' still not found.");
	        }
	    }

		// Remove <font color="LEVEL">...</font> e deixa apenas o texto interno em todas as mensagens
		html = html.replaceAll("<font\\s+color\\s*=\\s*\"LEVEL\">(.*?)</font>", "$1");
		// Remove todas as tags <br1> do texto
		html = html.replaceAll("<br1>", "");
		// Após formatar o HTML, insere <br1> em mensagens maiores que 50 caracteres quebra antes do limite
		Pattern msgPattern = Pattern.compile(">([^<]{50,})<");
		Matcher msgMatcher = msgPattern.matcher(html);
		StringBuffer sb = new StringBuffer();
		while (msgMatcher.find()) {
			String msg = msgMatcher.group(1);
			StringBuilder newMsg = new StringBuilder();
			int idx = 0;
			while (idx < msg.length()) {
				int end = Math.min(idx + 49, msg.length());
				// Procura o espaço mais próximo antes do limite
				if (end < msg.length()) {
					int lastSpace = msg.lastIndexOf(' ', end);
					if (lastSpace > idx) {
						end = lastSpace;
					}
				}
				newMsg.append(msg, idx, end);
				if (end < msg.length()) newMsg.append("<br1> ");
				idx = end;
				// Pula espaços extras
				while (idx < msg.length() && msg.charAt(idx) == ' ') idx++;
			}
			msgMatcher.appendReplacement(sb, ">" + newMsg + "<");
		}
		msgMatcher.appendTail(sb);
		html = sb.toString();

		// Limita o texto dos links para até 45 caracteres antes do log final
		Pattern linkTextPattern = Pattern.compile("<button[^>]*value=\"([^\"]+)\"");
		Matcher linkTextMatcher = linkTextPattern.matcher(html);
		StringBuffer limitedHtml = new StringBuffer();
		while (linkTextMatcher.find()) {
			String valueText = linkTextMatcher.group(1);
			if (valueText.length() > 45) {
				valueText = valueText.substring(0, 45);
			}
			// Substitui apenas o valor do atributo value
			String safeValueText = Matcher.quoteReplacement(valueText);
			String replaced = linkTextMatcher.group(0).replaceFirst(
			"value=\"[^\"]+\"",
			Matcher.quoteReplacement("value=\"" + safeValueText + "\"")
		);
		linkTextMatcher.appendReplacement(limitedHtml, Matcher.quoteReplacement(replaced));
		}
		linkTextMatcher.appendTail(limitedHtml);
		html = limitedHtml.toString();

		// Remove todas as tags <font color="...">...</font> e deixa apenas o texto interno
    	html = html.replaceAll("<font\\s+color\\s*=\\s*\"[^\"]+\">(.*?)</font>", "$1");

		// Log para verificar o HTML final após as substituições
	    //LOGGER.info("HTML after processHtmltags: " + html);

		
		// Só salva se hasTranslation for false
		LOGGER.info("Valor de hasTranslation em processHtml_Tags: " + hasTranslation);
		if (!hasTranslation) {
			saveTranslatedHtmlToFile(_file, html, I18n.getCurrentLocale());
		}

		

	    return html;
	}

	private static class HtmlProcessResult {
		String html;
		boolean hasTranslation;
		HtmlProcessResult(String html, boolean hasTranslation) {
			this.html = html;
			this.hasTranslation = hasTranslation;
		}
	}

	/**
	 * Salva o HTML já traduzido para cada idioma na raiz do arquivo solicitado,
	 * adicionando o sufixo do idioma (_pt, _en, _es, etc) ao nome do arquivo.
	 * Exemplo: data/html/seven_signs/festival/desc_2_pt.htm
	 */
	public static void saveTranslatedHtmlToFile(String originalFilePath, String translatedHtml, String lang) {
		if (originalFilePath == null || originalFilePath.isEmpty()) {
		LOGGER.warn("Caminho do arquivo HTML original está nulo ou vazio. Não foi possível salvar o HTML traduzido. HTML está no Java!");
		return;
		}
	    try {
	        
	        // Garante que o idioma está em minúsculo e sem traços
	        String langSuffix = "_" + lang.toLowerCase().replace("-", "_");

	        // Encontra a extensão do arquivo original
	        int extIndex = originalFilePath.lastIndexOf(".");
	        String newFilePath;
	        if (extIndex > 0) {
	            newFilePath = originalFilePath.substring(0, extIndex) + langSuffix + originalFilePath.substring(extIndex);
	        } else {
	            newFilePath = originalFilePath + langSuffix + ".htm";
	        }

	        // Cria os diretórios se não existirem
	        Files.createDirectories(Paths.get(newFilePath).getParent());

	        // Salva o HTML traduzido no novo arquivo
	        Files.write(Paths.get(newFilePath), translatedHtml.getBytes("UTF-8"), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);

	        LOGGER.info("Arquivo HTML traduzido salvo em: " + newFilePath);
	    } catch (Exception e) {
	        LOGGER.warn("Falha ao salvar HTML traduzido para o idioma " + lang + " em arquivo.", e);
	    }
	}

		
}