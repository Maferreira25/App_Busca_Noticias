import feedparser
import urllib.parse
import logging

logger = logging.getLogger(__name__)

import json

def get_ignored_domains():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("ignored_domains", [])
    except Exception:
        return []

def fetch_rss(query: str, lang: str = "pt-BR", country: str = "BR") -> list[dict]:
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl={lang}&gl={country}"
    
    logger.info(f"Buscando na gringa/RSS: {query}")
    feed = feedparser.parse(url)
    
    articles = []
    # Domínios que não queremos incluir nas pesquisas
    ignored_domains = get_ignored_domains()
    
    for entry in feed.entries:
        link = entry.link.lower()
        if any(domain in link for domain in ignored_domains):
            continue
            
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published if hasattr(entry, 'published') else "Data desconhecida",
            "summary": entry.summary if hasattr(entry, 'summary') else ""
        })
    return articles

def fetch_ai_news() -> list[dict]:
    """
    Busca notícias sobre IA dos últimos 7 dias via Google News RSS utilizando multicritérios:
    Geral PT-BR, Exterior EN-US, e Jurídico focado.
    """
    articles = []
    
    # 1. Geral Brasil focando nas principais empresas de IA (15 notícias)
    brazil = fetch_rss('("inteligência artificial" OR "IA generativa" OR ChatGPT OR OpenAI OR Anthropic OR Google Gemini) -uol -passagens -aéreas -"companhias aéreas" -decolar', "pt-BR", "BR")
    articles.extend(brazil[:15])
    
    # 2. Exterior / Relevantes em inglês e portais de tecnologia mundiais (15 notícias)
    exterior = fetch_rss('("generative AI technology" OR ChatGPT OR OpenAI OR Anthropic OR "Google DeepMind" OR TechCrunch OR Wired OR "The Verge" OR "Ars Technica") -airlines -flights', "en-US", "US")
    articles.extend(exterior[:15])
    
    # 3. Jurídico focado, academia e portais especializados (15 notícias)
    juridico = fetch_rss('("inteligência artificial" OR "IA generativa") AND (direito OR jurídico OR advocacia OR tribunais OR ConJur OR STF OR STJ OR CNJ OR Migalhas OR JOTA OR Jusbrasil OR LexisNexis OR "Direito Digital" OR LegalTech OR LawTech OR "DSA ACADEMY" OR "FGV Direito SP" OR "Revista do Direito" OR "Atitus" OR "Virtualjus" OR "PUC Minas" OR "Data Privacy Brasil")', "pt-BR", "BR")
    articles.extend(juridico[:15])
    
    # 4. Fronteira da IA e portais de tecnologia de referência (15 notícias)
    fronteira = fetch_rss('"AI" OR "artificial intelligence" AND (site:openai.com OR site:deepmind.google OR site:anthropic.com OR site:huggingface.co OR site:ai.meta.com OR site:technologyreview.com OR site:stanford.edu OR site:techcrunch.com OR site:wired.com OR site:theverge.com)', "en-US", "US")
    articles.extend(fronteira[:15])
    
    logger.info(f"Total de notícias mescladas: {len(articles)}")
    
    # Prevenção de duplicatas
    unique_articles = []
    seen_links = set()
    for article in articles:
        if article['link'] not in seen_links:
            seen_links.add(article['link'])
            unique_articles.append(article)
            
    logger.info(f"Retornando {len(unique_articles)} notícias únicas para a IA processar.")
    return unique_articles
