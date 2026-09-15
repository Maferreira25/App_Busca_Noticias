import requests
import urllib.parse
import logging
import os
import time
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def split_message_into_chunks(text: str, max_chars: int = 15000) -> list[str]:
    """
    Divide a mensagem respeitando quebras de parágrafos para não cortar
    links, tags markdown ou frases no meio.
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para) + 2  # compensa o \n\n
        if current_length + para_len > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = len(para)
        else:
            current_chunk.append(para)
            current_length += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def send_whatsapp_message(content: str):
    """
    Envia a mensagem via Evolution API local (v1.8.2)
    """
    url = os.getenv("EVOLUTION_API_URL")
    apikey = os.getenv("EVOLUTION_API_KEY")
    instance = os.getenv("EVOLUTION_INSTANCE")
    phone = os.getenv("WHATSAPP_PHONE")

    if not all([url, apikey, instance, phone]):
        logger.warning("Configurações da Evolution API incompletas no .env. Pulando envio.")
        return False

    # Header de impacto
    header = "🚀 *NOVO BOLETIM DE IA GERATIVA*\n\n"
    full_message = header + content
    
    # Endpoint da v1.8.2 para envio de texto
    endpoint = f"{url}/message/sendText/{instance}"
    
    headers = {
        "apikey": apikey,
        "Content-Type": "application/json"
    }

    # Divisão contextual e inteligente de mensagens
    parts = split_message_into_chunks(full_message, max_chars=15000)
    
    success_count = 0
    for index, part in enumerate(parts):
        # Se houver mais de uma parte, adiciona um marcador
        msg_to_send = part
        if len(parts) > 1:
            msg_to_send = (f"--- Parte {index+1}/{len(parts)} ---\n\n" if index > 0 else "") + part

        payload = {
            "number": phone,
            "options": {
                "delay": 1200,
                "presence": "composing",
                "linkPreview": False
            },
            "textMessage": {
                "text": msg_to_send
            }
        }

        try:
            logger.info(f"Enviando parte {index+1} para {phone}...")
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"Parte {index+1} enviada com sucesso.")
                success_count += 1
            else:
                logger.error(f"Erro no envio da parte {index+1}: {response.status_code} - {response.text}")
            
            # Pequeno delay entre partes para naturalidade
            if len(parts) > 1:
                time.sleep(2)

        except Exception as e:
            logger.error(f"Falha critica ao conectar com a Evolution API: {e}")
            break

    if success_count == len(parts):
        logger.info("Boletim enviado integralmente via Evolution API!")
        return True
    
    return False
