import os
from dotenv import load_dotenv
import logging
from google import genai
from google.genai import types

import requests

load_dotenv()
logger = logging.getLogger(__name__)

def shorten_url(url):
    """
    Encurta uma URL usando o serviço gratuito TinyURL e garante HTTPS
    """
    try:
        api_url = f"http://tinyurl.com/api-create.php?url={url}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            link = response.text
            # Garante que comece com https:// para maior aceitacao no celular
            if link.startswith("http://"):
                link = link.replace("http://", "https://", 1)
            return f" {link} " # Adiciona espaços nas bordas para o Zap não "colar" o link
    except Exception as e:
        logger.warning(f"Nao foi possivel encurtar o link {url}: {e}")
    return f" {url} "

def summarize_news_for_whatsapp(articles: list[dict]) -> str:
    """
    Recebe os artigos e utiliza a API do Google Gemini para gerar um resumo atraente
    em linguagem simples e acessível, com pelo menos 10 notícias relevantes,
    focado para grupos de WhatsApp.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    if not articles:
        return "Não encontrei notícias relevantes sobre IA Generativa nesta semana."
        
    # Enviando em torno de 35 noticias das variadas fontes que o fetcher entregou 
    top_articles = articles[:35]
    
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    period_str = f"{start_date.strftime('%d/%m')} a {end_date.strftime('%d/%m/%Y')}"

    news_text = ""
    for i, article in enumerate(top_articles, 1):
        # Encurtando o link antes de passar para a IA
        short_link = shorten_url(article['link'])
        news_text += f"{i}. Título: {article['title']}\nLink: {short_link}\nData de Publicação: {article['published']}\n\n"
        
    prompt_system = (
        "Você é um especialista em jornalismo e tecnologia, encarregado de criar boletins "
        "informativos semanais sobre Inteligência Artificial Generativa para grupos de WhatsApp.\n"
        "Seu público é leigo - evite termos muito técnicos ou, se usar, explique-os de forma muito didática.\n"
        "Seja entusiasmado, útil e com um tom amigável."
    )
    
    prompt_user = (
        f"Crie um resumo dinâmico e expansivo das principais notícias sobre Inteligência Artificial Generativa da última semana (Período: {period_str}).\n"
        "Regras vitais e estritas:\n"
        "1. O texto DEVE ser escrito inteiramente em português do Brasil (pt-BR).\n"
        "2. Dê SEMPRE preferência máxima na adoção da pauta para as notícias MAIS RELEVANTES, comentadas e reproduzidas em outros sites no mundo e no Brasil. Ignore e exclua notícias de impacto menor e isoladas.\n"
        "3. Você tem que selecionar obrigatoriamente NO MÍNIMO 10 notícias desta elite global e nacional com base na lista fornecida (trazendo um equilíbrio entre notícias do exterior, tecnologia em geral e da área jurídica/direito).\n"
        "4. EXPANDA BEM o resumo de cada notícia. O leitor precisa entender o contexto completo, as motivações e os resultados com base apenas no seu texto (escreva em média de 3 a 5 linhas cheias de conteúdo para cada notícia).\n"
        "5. Formate usando o padrão do WhatsApp: negrito (*texto*) para os títulos das notícias, itálicos (_texto_) e adicione emojis atrativos e apropriados sem poluir demais.\n"
        "6. Inclua SEMPRE o link original de cada notícia logo após o resumo explicativo estendido, para que as pessoas possam acessar a fonte e se aprofundar.\n"
        "7. O título do boletim DEVE ser chamativo e incluir obrigatoriamente o período da semana (ex: 🚀 *BOLETIM IA: {period_str}*).\n"
        "8. SEMPRE QUE POSSÍVEL, mencione a data do evento ou o dia em que a notícia foi gerada dentro do texto do resumo (ex: 'No último dia 22...', 'Nesta quarta-feira...', etc), usando a 'Data de Publicação' fornecida como referência.\n"
        "9. Inicie com uma saudação calorosa e um texto introdutório comentando brevemente as tendências vistas na área jurídica e internacional do compilado antes das notícias.\n"
        "10. Finalize com uma mensagem de encerramento inovadora, inteligente e criativa, convidando o grupo a dar opinião sobre alguma dessas polêmicas discutidas. PROIBIDO usar clichês ou bordões batidos como 'Ufa! Que semana...', 'Quanta coisa, não é mesmo?' ou similares. Varie sempre o fechamento para não ficar cansativo nos boletins semanais.\n\n"
        f"Aqui está o compilado bruto de dezenas de notícias coletadas (exterior, geral e área jurídica) para selecionar os pesos pesados e expandir:\n\n{news_text}"
    )
    
    logger.info("Enviando solicitação de sumarização para a Gemini API (gemini-2.5-flash)...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_user,
            config=types.GenerateContentConfig(
                system_instruction=prompt_system,
                temperature=0.7
            )
        )
        
        if response.candidates and response.candidates[0].finish_reason:
            logger.info(f"Finish Reason retornado pelo Gemini: {response.candidates[0].finish_reason}")
        
        content = response.text
                
        logger.info("Resumo gerado com sucesso pelo Gemini.")
        return content
        
    except Exception as e:
        logger.error(f"Erro ao conversar com a API do Gemini: {str(e)}")
        raise e
