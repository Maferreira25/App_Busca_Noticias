import feedparser
import urllib.parse
import logging
import json
import requests
from constants import DEFAULT_POSITIVE_DOMAINS, DEFAULT_IGNORED_DOMAINS

logger = logging.getLogger(__name__)


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
 
def fetch_hf_trending_papers(limit: int = 5) -> list[dict]:
    """
    Busca os papers mais votados/em alta na API oficial do Hugging Face (Daily Papers).
    Possui tratamento defensivo para respostas anômalas, dicionários nulos e tipos inesperados.
    """
    if limit <= 0:
        return []

    url = "https://huggingface.co/api/daily_papers"
    logger.info("Buscando trending papers na API oficial do Hugging Face...")
    papers = []
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, list):
                logger.warning(f"Payload inesperado da API Hugging Face (esperado lista, recebido {type(data)}).")
                return []

            def get_upvotes(item):
                if not isinstance(item, dict):
                    return 0
                p_obj = item.get("paper") or {}
                if not isinstance(p_obj, dict):
                    return 0
                return p_obj.get("upvotes") or 0

            sorted_data = sorted(data, key=get_upvotes, reverse=True)
            for item in sorted_data:
                if not isinstance(item, dict):
                    continue
                p = item.get("paper") or {}
                if not isinstance(p, dict):
                    p = {}

                paper_id = p.get("id") or item.get("id") or ""
                title = p.get("title") or item.get("title") or "Paper sem título"
                summary = p.get("summary") or item.get("summary") or ""
                published = item.get("publishedAt") or p.get("publishedAt") or "Data recente"
                upvotes = p.get("upvotes") or 0
                link = f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"

                papers.append({
                    "title": f"[Paper HF] {title} ({upvotes} votos)",
                    "link": link,
                    "published": str(published),
                    "summary": str(summary)
                })
                if len(papers) >= limit:
                    break

            logger.info(f"Coletados {len(papers)} trending papers do Hugging Face com sucesso.")
        else:
            logger.warning(f"Hugging Face API retornou status code {response.status_code}")
    except Exception as e:
        logger.warning(f"Não foi possível buscar papers do Hugging Face via API: {e}")

    return papers

def fetch_ai_news() -> list[dict]:
    """
    Busca notícias sobre IA dos últimos 7 dias via Google News RSS utilizando multicritérios:
    Geral PT-BR, Exterior EN-US, Jurídico focado, Fronteira Acadêmica/Domínios Positivos
    e Trending Papers do Hugging Face.
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
    site_filters = [f"site:{d}" for d in pos_domains if any(k in d for k in ["openai", "deepmind", "anthropic", "huggingface", "mit.edu", "cmu.edu", "harvard.edu", "ox.ac.uk", "nature.com", "arxiv.org", "technologyreview", "techcrunch", "wired", "theverge", "dair.ai"])]
    if not site_filters:
        site_filters = [f"site:{d}" for d in pos_domains[:8]]
    sites_str = " OR ".join(site_filters[:10]) if site_filters else "site:openai.com OR site:deepmind.google"

    fronteira = fetch_rss(f'("AI" OR "artificial intelligence" OR "generative AI") AND ({sites_str} OR "MIT" OR "CSAIL" OR "Carnegie Mellon" OR "CMU" OR "Harvard" OR "Oxford University" OR "University of Cambridge" OR "Alan Turing Institute" OR "Nature Machine Intelligence" OR "IEEE" OR site:arxiv.org)', "en-US", "US")
    articles.extend(fronteira[:15])
    
    # 5. DAIR.AI Academy Papers (Curadoria semanal especializada em papers e arquiteturas)
    dair_articles = fetch_rss("site:academy.dair.ai OR site:dair.ai", "en-US", "US")
    articles.extend(dair_articles[:5])
    
    # 6. Trending Papers do Hugging Face (Top 5 papers com maior impacto/votos da semana)
    hf_papers = fetch_hf_trending_papers(limit=5)
    articles.extend(hf_papers)
    
    logger.info(f"Total de notícias mescladas: {len(articles)}")
    
    # Prevenção de duplicatas com prioridade para domínios positivos
    unique_articles = []
    seen_links = set()
    
    # Ordena para dar preferência a artigos que contenham algum domínio positivo configurado
    def matches_positive_domain(art):
        l = art.get('link', '').lower()
        return any(pd in l for pd in pos_domains)
        
    sorted_articles = sorted(articles, key=lambda a: 0 if matches_positive_domain(a) else 1)
    
    for article in sorted_articles:
        link = article.get('link')
        if not link:
            continue
        if link not in seen_links:
            seen_links.add(link)
            unique_articles.append(article)
            
    logger.info(f"Retornando {len(unique_articles)} notícias únicas para a IA processar.")
    return unique_articles
