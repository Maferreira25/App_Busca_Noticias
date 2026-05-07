import logging
import os
import sys
import subprocess
import time
import requests
from dotenv import load_dotenv
from fetcher import fetch_ai_news
from summarizer import summarize_news_for_whatsapp
from storage import save_summary_locally
from whatsapp_sender import send_whatsapp_message

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("boletim.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def ensure_environment():
    """
    Garante que o Docker e a Evolution API estejam rodando.
    """
    logger.info("Verificando ambiente (Docker e Evolution API)...")
    
    # 1. Verificar se o Docker está rodando
    docker_running = False
    try:
        subprocess.run(["docker", "ps"], check=True, capture_output=True)
        docker_running = True
    except:
        logger.warning("Docker daemon não detectado.")

    if not docker_running:
        docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if os.path.exists(docker_path):
            logger.info("Iniciando Docker Desktop automaticamente...")
            subprocess.Popen([docker_path], shell=True)
            # Esperar até 2 minutos (24 * 5s)
            for i in range(24):
                logger.info(f"Aguardando Docker iniciar... ({i*5}s)")
                time.sleep(5)
                try:
                    subprocess.run(["docker", "ps"], check=True, capture_output=True)
                    logger.info("Docker iniciado e pronto.")
                    docker_running = True
                    break
                except:
                    continue
        else:
            logger.error(f"Não foi possível encontrar o Docker Desktop em: {docker_path}")
            return False

    if docker_running:
        # 2. Subir o container da Evolution API
        logger.info("Subindo containers do docker-compose...")
        try:
            subprocess.run(["docker-compose", "up", "-d"], check=True, capture_output=True)
        except Exception as e:
            logger.error(f"Erro ao executar docker-compose: {e}")
            return False

        # 3. Esperar a API responder na porta 8080
        api_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
        for i in range(10):
            try:
                requests.get(api_url, timeout=2)
                logger.info("Evolution API está respondendo!")
                return True
            except:
                logger.info("Aguardando Evolution API ficar online...")
                time.sleep(3)
    
    return False

def main():
    logger.info("=======================================================================")
    logger.info("Iniciando sistema autônomo de busca de notícias de IA...")
    
    # 0. Garantir infraestrutura
    env_ok = ensure_environment()
    if not env_ok:
        logger.warning("Não foi possível garantir que o Docker/API estejam rodando. O envio de WhatsApp pode falhar.")

    import glob
    from datetime import datetime
    
    # 0. Verificação de segurança: Não rodar de novo se já rodou hoje.
    today_br = datetime.now().strftime("%d-%m-%Y")
    today_legacy = datetime.now().strftime("%Y-%m-%d")
    history_dir = "history"
    if os.path.exists(history_dir):
        # Verifica tanto o formato novo (BR) quanto o legado (ISO) para hoje
        existing_bulletins = glob.glob(os.path.join(history_dir, f"boletim_ia_{today_br}_*.md")) + \
                             glob.glob(os.path.join(history_dir, f"boletim_ia_{today_legacy}_*.md"))
        if existing_bulletins:
            logger.info("INFO: Um boletim ja foi gerado com sucesso no dia de hoje. Abortando execucao.")
            return

    if not os.getenv("GEMINI_API_KEY"):
        logger.error("Aviso crítico: GEMINI_API_KEY não encontrada no arquivo .env nem nas variáveis de ambiente.")
        sys.exit(1)
        
    if not os.getenv("EMAIL_ADDRESS") or not os.getenv("EMAIL_APP_PASSWORD"):
        logger.warning("Aviso Mínimo: As credenciais de E-mail não estão no .env. O script rodará, mas o e-mail não será disparado.")
        
    try:
        # 1. Buscar Notícias
        logger.info("Passo 1/3: Buscando notícias recentes via RSS do Google News...")
        articles = fetch_ai_news()
        
        # 2. Resumir e formatar com IA
        logger.info("Passo 2/3: Processando com o Gemini e formatando texto pro WhatsApp...")
        whatsapp_message = summarize_news_for_whatsapp(articles)
        
        # 3. Salvar localmente
        logger.info("Passo 3/4: Salvando o material final gerado na pasta de histórico...")
        filepath = save_summary_locally(whatsapp_message)
        
        # 4. Enviar E-mail
        logger.info("Passo 4/4: Disparando notificação por e-mail via SMTP...")
        from emailer import send_email_notification
        import json
        
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                emails_target = json.load(f).get("emails", ["michel.aires2013@gmail.com"])
        except:
            emails_target = ["michel.aires2013@gmail.com"]
            
        for email in emails_target:
            send_email_notification(filepath, to_email=email)
            
        # 5. Enviar WhatsApp (via Evolution API Profissional)
        logger.info("Passo 5/5: Disparando notificação via WhatsApp...")
        send_whatsapp_message(whatsapp_message)
        
        logger.info("SUCESSO: Processo finalizado!")
        logger.info(f"O boletim completo está salvo em: {filepath}")
        
    except Exception as e:
        logger.error("Ocorreu um erro letal durante a execução.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
