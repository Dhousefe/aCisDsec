package net.sf.l2j.gameserver.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Properties;

public class I18n {
    private static Locale locale = new Locale("pt", "BR"); // Idioma padrão
    private static Properties translations;

    static {
        loadTranslations();
    }

    private static void loadTranslations() {
        try {
            // Caminho para a pasta de traduções
            File translationFile = new File("config/traducao/messages_" + locale.toString() + ".properties");
            translations = new Properties();
            try (FileInputStream fis = new FileInputStream(translationFile);
                 InputStreamReader isr = new InputStreamReader(fis, "UTF-8")) {
                translations.load(isr);
            }
        } catch (Exception e) {
            e.printStackTrace();
            translations = new Properties(); // Carrega um objeto vazio em caso de erro
        }
    }

    public static String get(String key) {
        return translations.getProperty(key, "!" + key + "!"); // Retorna a tradução ou a chave caso não encontre
    }

    public static boolean containsKey(String key) {
        // Verifica se a chave existe no mapa de traduções
        return translations.containsKey(key);
    }

    public static void setLocale(String language, String country) {
        try {
            // Valida os parâmetros
            if (language == null || language.isEmpty()) {
                throw new IllegalArgumentException("Invalid language or country parameters.");
            }

            // Define o país padrão com base no idioma, se o país não for fornecido
            if (country == null || country.isEmpty()) {
                country = switch (language.toLowerCase()) {
                    case "pt" -> "BR"; // Português do Brasil
                    case "en" -> "US"; // Inglês dos Estados Unidos
                    case "de" -> "DE"; // Alemão
                    case "fr" -> "FR"; // Francês
                    case "it" -> "IT"; // Italiano
                    case "es" -> "ES"; // Espanhol
                    case "ja" -> "JP"; // Japonês
                    case "ko" -> "KR"; // Coreano
                    case "ru" -> "RU"; // Russo
                    case "pl" -> "PL"; // Polonês
                    case "zh_tw" -> "TW"; // Chinês Tradicional
                    default -> throw new IllegalArgumentException("Unsupported language: " + language);
                };
            }

            // Define o novo idioma
            locale = new Locale(language, country);

            // Caminho do arquivo de tradução
            File translationFile = new File("config/traducao/messages_" + locale.toString() + ".properties");

            // Verifica se o arquivo existe
            if (!translationFile.exists()) {
                throw new FileNotFoundException("Translation file not found: " + translationFile.getPath());
            }

            // Recarrega as traduções
            loadTranslations();
        } catch (Exception e) {
            System.err.println("Failed to set locale: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static void setLocalel(String language) throws FileNotFoundException {
        try {
            // Define o país padrão com base no idioma
            String country = switch (language.toLowerCase()) {
            case "pt" -> "BR"; // Português do Brasil
            case "en" -> "US"; // Inglês dos Estados Unidos
            default -> throw new IllegalArgumentException("Unsupported language: " + language);
            };

            // Obtém o país correspondente ao idioma
            //String country = languageToCountry.get(language.toLowerCase());

            // Verifica se o idioma é suportado
            //if (country == null) {
                //throw new IllegalArgumentException("Unsupported language: " + language);
            //}

            // Define o novo idioma e país
            locale = new Locale(language, country);

            // Caminho do arquivo de tradução
            File translationFile = new File("config/traducao/messages_" + locale.toString() + ".properties");

            // Verifica se o arquivo existe
            if (!translationFile.exists()) {
                throw new FileNotFoundException("Translation file not found: " + translationFile.getPath());
            }

            // Recarrega as traduções
            loadTranslations();
        } catch (Exception e) {
            System.err.println("Failed to set locale: " + e.getMessage());
            throw e;
        }
    }

    public static String getCurrentLocale() {
        return locale.toString();
    }
}