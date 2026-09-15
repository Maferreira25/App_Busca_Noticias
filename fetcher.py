import feedparser
import urllib.parse
import logging

logger = logging.getLogger(__name__)

import json
from constants import DEFAULT_POSITIVE_DOMAINS, DEFAULT_IGNORED_DOMAINS


def get_ignored_domains() -> list[str]:
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("ignored_domains", DEFAULT_IGNORED_DOMAINS)
    except Exception:
        return DEFAULT_IGNORED_DOMAINS


def get_positive_domains() -> list[str]:
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("positive_domains", DEFAULT_POSITIVE_DOMAINS)
    except Exception:
        return DEFAULT_POSITIVE_DOMAINS

def fetch_rss(query: str, lang: str = "pt-BR", country: str = "BR") -> list[dict]:
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl={lang}&gl={country}"
    
    logger.info(f"Buscando na gringa/RSS: {query}")
    feed = feedparser.parse(url)
    
    articles = []
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
    Geral PT-BR, Exterior EN-US, Jurídico focado e Fronteira Acadêmica/Domínios Positivos.
    """
    articles = []
    pos_domains = get_positive_domains()
    
    # 1. Geral Brasil focando nas principais empresas de IA (15 notícias)
    brazil = fetch_rss('("inteligência artificial" OR "IA generativa" OR ChatGPT OR OpenAI OR Anthropic OR Google Gemini) -uol -passagens -aéreas -"companhias aéreas" -decolar', "pt-BR", "BR")
    articles.extend(brazil[:15])
    
    # 2. Exterior / Relevantes em inglês e portais de tecnologia mundiais (15 notícias)
    exterior = fetch_rss('("generative AI technology" OR ChatGPT OR OpenAI OR Anthropic OR "Google DeepMind" OR TechCrunch OR Wired OR "The Verge" OR "Ars Technica") -airlines -flights', "en-US", "US")
    articles.extend(exterior[:15])
    
    # 3. Jurídico focado, tribunais, academia e portais especializados (15 notícias)
    juridico = fetch_rss('("inteligência artificial" OR "IA generativa") AND (direito OR jurídico OR advocacia OR tribunais OR ConJur OR STF OR STJ OR CNJ OR Migalhas OR JOTA OR Jusbrasil OR LexisNexis OR "Direito Digital" OR LegalTech OR LawTech OR "DSA ACADEMY" OR "FGV Direito SP" OR "Revista do Direito" OR "Atitus" OR "Virtualjus" OR "PUC Minas" OR "Data Privacy Brasil" OR "ANPD" OR "OAB Nacional" OR "CFOAB" OR "TJSP" OR "TST" OR "ITS Rio" OR "IDP" OR "Law.com" OR "Legaltech News" OR "Reuters Legal")', "pt-BR", "BR")
    articles.extend(juridico[:15])
    
    # 4. Fronteira da IA, centros acadêmicos mundiais e institutos de pesquisa (15 notícias)
    # Seleciona domínios configurados pelo usuário para montar a cláusula de busca
    site_filters = [f"site:{d}" for d in pos_domains if any(k in d for k in ["openai", "deepmind", "anthropic", "huggingface", "mit.edu", "cmu.edu", "harvard.edu", "ox.ac.uk", "nature.com", "arxiv.org", "technologyreview", "techcrunch", "wired", "theverge"])]
    if not site_filters:
        site_filters = [f"site:{d}" for d in pos_domains[:8]]
    sites_str = " OR ".join(site_filters[:10]) if site_filters else "site:openai.com OR site:deepmind.google"

    fronteira = fetch_rss(f'("AI" OR "artificial intelligence" OR "generative AI") AND ({sites_str} OR "MIT" OR "CSAIL" OR "Carnegie Mellon" OR "CMU" OR "Harvard" OR "Oxford University" OR "University of Cambridge" OR "Alan Turing Institute" OR "Nature Machine Intelligence" OR "IEEE" OR site:arxiv.org)', "en-US", "US")
    articles.extend(fronteira[:15])
    
    logger.info(f"Total de notícias mescladas: {len(articles)}")
    
    # Prevenção de duplicatas com prioridade para domínios positivos
    unique_articles = []
    seen_links = set()
    
    # Ordena para dar preferência a artigos que contenham algum domínio positivo configurado
    def matches_positive_domain(art):
        l = art['link'].lower()
        return any(pd in l for pd in pos_domains)
        
    sorted_articles = sorted(articles, key=lambda a: 0 if matches_positive_domain(a) else 1)
    
    for article in sorted_articles:
        if article['link'] not in seen_links:
            seen_links.add(article['link'])
            unique_articles.append(article)
            
    logger.info(f"Retornando {len(unique_articles)} notícias únicas para a IA processar.")
    return unique_articles
