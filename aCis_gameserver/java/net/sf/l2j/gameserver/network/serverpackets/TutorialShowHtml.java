package net.sf.l2j.gameserver.network.serverpackets;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.TextNode;
import org.jsoup.select.Elements;

import net.sf.l2j.gameserver.util.I18n;

public final class TutorialShowHtml extends L2GameServerPacket
{
	private final String _html;
	// Adicione um cache estático no início da classe
	private static final Map<String, String> HTML_CACHE = new HashMap<>();

	private final String text;
	private final int _objectId = 0;
	private final String _file = null;
	
	public TutorialShowHtml(String html)
	{
		//_html = html;
		// Processa o HTML igual ao NpcHtmlMessage
		// Processa o HTML para substituir as tags dinamicamente
		//HtmlProcessResult result = processHtml(text, _objectId, _file);

		this.text = html;
		
		//String _file = "data/html/tutorial/" + html;
		HtmlProcessResult result = processHtmltutorial(text, _objectId, _file);
		LOGGER.info("Valor de hasTranslation em processHtmlsoup: " + result.hasTranslation);
		_html = processHtmltags(result.html, _objectId, _file, result.hasTranslation);
	}
	
	@Override
	protected void writeImpl()
	{
		writeC(0xa0);
		writeS(_html);
	}

	private static class HtmlProcessResult {
		String html;
		boolean hasTranslation;
		HtmlProcessResult(String html, boolean hasTranslation) {
			this.html = html;
			this.hasTranslation = hasTranslation;
		}
	}

	private static String padronizarHtmlComJsoup(String html) {
    // 1. Parse o HTML com jsoup
    Document doc = Jsoup.parse(html);

    // 2. Remove todas as tags <font color="..."> mas mantém o texto interno
    //doc.select("font").forEach(font -> font.unwrap());

    // 3. Para cada nó de texto, aplique as substituições desejadas
    for (TextNode textNode : doc.textNodes()) {
        String text = textNode.text();
        // Padronização igual ao seu fluxo:
        //text = text.replaceAll("([A-Za-z])'s", "$1s");
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

	private static String processBodyTextsJsoup(String html, Map<String, String> translationMap, Map<String, Integer> tagCounter) {
    Document doc = Jsoup.parse(html);

    // Seleciona o elemento <body>
    Element body = doc.body();

    // Percorre todos os nós filhos diretos do <body>
    // Percorre todos os TextNodes do body, exceto os que estão dentro de <a>
    for (TextNode textNode : doc.body().select("*").not("a *, button *, edit *, combobox *, img *").textNodes()) {
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

	private static String formatLinks(String html) {
		// Se já contém <button>, <edit> ou <combobox>, não formata
		
	    // Primeiro, processa todos os <a ...>...</a> normalmente (como já está)
	    Pattern pattern = Pattern.compile("<a([^>]*)>(.*?)</a>");
	    Matcher matcher = pattern.matcher(html);
	    StringBuffer sb = new StringBuffer();

	    while (matcher.find()) {
	        String aAttributes = matcher.group(1).trim();
	        String linkText = matcher.group(2).trim();

	        // Remove <font color="...">...</font> se existir, deixando apenas o texto interno
	        if (linkText.matches("<font\\s+color\\s*=\\s*\"[^\"]+\">.*?</font>")) {
	            linkText = linkText.replaceAll("<font\\s+color\\s*=\\s*\"[^\"]+\">(.*?)</font>", "$1");
	        }
	        // Remove <font color="LEVEL">...</font> se existir
	        if (linkText.matches("<font\\s+color\\s*=\\s*\"LEVEL\">.*?</font>")) {
	            linkText = linkText.replaceAll("<font\\s+color\\s*=\\s*\"LEVEL\">(.*?)</font>", "$1");
	        }
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

			// Também cobre casos de value=""texto""
			button = button.replaceAll("value=\"\"([^\"]+)\"\"", "value=\"$1\"");

			
			matcher.appendReplacement(sb, Matcher.quoteReplacement(button));
	        
	    }
	    matcher.appendTail(sb);
	    html = sb.toString();

	    // Processa <td><button ...></td> para garantir tamanho correto do botão conforme o texto
	    return html;
	}


	private static HtmlProcessResult processHtmltutorial(String html, int objectId, String htmlFilePath) {
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
		"<html><body><center>%s<br><img src=\"L2UI.SquareWhite\" width=\"300\" height=\"1\"><!-- L2jBrasil By Dhousefe --></center></body></html>",
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

	private static boolean saveTranslationsToFile(Map<String, String> translationMap, String htmlFilePath) {
    Set<String> existingKeys = new HashSet<>();
    File file = new File("translationstuto.properties");
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