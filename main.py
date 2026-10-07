import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import glob
from datetime import datetime
import json
from dotenv import load_dotenv

import argparse
from fetcher import fetch_ai_news, fetch_agent_ai_news
from summarizer import summarize_news_for_whatsapp, summarize_agent_news_for_whatsapp
from storage import save_summary_locally
from whatsapp_sender import send_whatsapp_message
from emailer import send_email_notification
from docker_manager import ensure_environment

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler("boletim.log", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Automação de Busca de Notícias e Papers de IA")
    parser.add_argument(
        "--type",
        choices=["geral", "agentes"],
        default="geral",
        help="Tipo de boletim a ser gerado ('geral' para notícias amplas e jurídicas, 'agentes' para papers e novidades técnicas de agentes)"
    )
    args = parser.parse_args()

    tipo_boletim = args.type
    prefixo = "boletim_ia_agentes" if tipo_boletim == "agentes" else "boletim_ia"
    nome_exibicao = "Agentes de IA & Papers" if tipo_boletim == "agentes" else "Geral (Notícias & Jurídico)"

    logger.info("=======================================================================")
    logger.info(f"Iniciando sistema autônomo de busca de IA - Modalidade: {nome_exibicao}...")
    
    # 0. Garantir infraestrutura (Docker e Evolution API)
    env_ok = ensure_environment()
    if not env_ok:
        logger.warning("Não foi possível garantir que o Docker/API estejam rodando. O envio de WhatsApp pode falhar.")

    # Verificação de segurança: Não rodar de novo se já rodou hoje para este tipo específico
    today_br = datetime.now().strftime("%d-%m-%Y")
    today_legacy = datetime.now().strftime("%Y-%m-%d")
    history_dir = "history"
    if os.path.exists(history_dir):
        existing_bulletins = glob.glob(os.path.join(history_dir, f"{prefixo}_{today_br}_*.md")) + \
                             glob.glob(os.path.join(history_dir, f"{prefixo}_{today_legacy}_*.md"))
        if existing_bulletins:
            logger.info(f"INFO: Um boletim de '{tipo_boletim}' já foi gerado com sucesso no dia de hoje. Abortando execução.")
            return

    if not os.getenv("GEMINI_API_KEY"):
        logger.error("Aviso crítico: GEMINI_API_KEY não encontrada no arquivo .env nem nas variáveis de ambiente.")
        sys.exit(1)
        
    if not os.getenv("EMAIL_ADDRESS") or not os.getenv("EMAIL_APP_PASSWORD"):
        logger.warning("Aviso Mínimo: As credenciais de E-mail não estão no .env. O script rodará, mas o e-mail não será disparado.")
        
    try:
        # 1. Buscar Notícias / Papers conforme a modalidade
        if tipo_boletim == "agentes":
            logger.info("Passo 1/5: Buscando papers e notícias de Agentes de IA nas 15+ fontes mundiais de referência...")
            articles = fetch_agent_ai_news()
            
            logger.info("Passo 2/5: Processando com o Gemini para selecionar os 15 principais papers e inovações com explicações simples...")
            whatsapp_message = summarize_agent_news_for_whatsapp(articles)
        else:
            logger.info("Passo 1/5: Buscando notícias recentes via RSS do Google News...")
            articles = fetch_ai_news()
            
            logger.info("Passo 2/5: Processando com o Gemini e formatando texto pro WhatsApp...")
            whatsapp_message = summarize_news_for_whatsapp(articles)
        
        # 3. Salvar localmente
        logger.info("Passo 3/5: Salvando o material final gerado na pasta de histórico...")
        filepath = save_summary_locally(whatsapp_message, prefix=prefixo)
        
        # 4. Enviar E-mail
        logger.info("Passo 4/5: Disparando notificação por e-mail via SMTP...")
        emails_target = []
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                emails_target = json.load(f).get("emails", [])
        except Exception as e:
            logger.warning(f"Não foi possível carregar destinatários de config.json: {e}")
            
        if emails_target:
            for email in emails_target:
                send_email_notification(filepath, to_email=email)
        else:
            logger.info("Nenhum destinatário de e-mail cadastrado em config.json. Pulando envio de e-mails.")
            
        # 5. Enviar WhatsApp (via Evolution API)
        logger.info("Passo 5/5: Disparando notificação via WhatsApp...")
        send_whatsapp_message(whatsapp_message)
        
        logger.info("SUCESSO: Processo finalizado!")
        logger.info(f"O boletim completo está salvo em: {filepath}")
        
    except BaseException as e:
        if isinstance(e, SystemExit) and e.code == 0:
            sys.exit(0)
        logger.error("Ocorreu um erro letal durante a execução.", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
