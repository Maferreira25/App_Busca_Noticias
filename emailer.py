import smtplib
from email.message import EmailMessage
import os
import logging

logger = logging.getLogger(__name__)

def send_email_notification(filepath: str, to_email: str):
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_APP_PASSWORD")
    
    if not email_address or not email_password:
        logger.warning("Credenciais de email (EMAIL_ADDRESS ou EMAIL_APP_PASSWORD) ausentes no .env. E-mail nao enviado.")
        return
        
    msg = EmailMessage()
    msg['Subject'] = '🚀 Novo Boletim de IA Generativa Disponível!'
    msg['From'] = email_address
    msg['To'] = to_email
    
    filename = os.path.basename(filepath)
    
    # Lê todo o arquivo Markdown para enviar no corpo do e-mail também
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        file_content = f"Não foi possível ler o arquivo local. Erro: {e}"
        
    corpo_email = f"""Olá!

Seu novo boletim autônomo semanal contendo as últimas novidades de Inteligência Artificial ('{filename}') acabou de ser gerado com sucesso!

O sistema varreu fontes do exterior, meios jurídicos e da fronteira de IA (OpenAI, DeepMind, Stanford, etc).
Confira abaixo o compilado desta semana:

=============================================

{file_content}

=============================================

O sistema continuará rodando de forma autônoma a cada 7 dias através do agendador automático configurado.
"""

    msg.set_content(corpo_email)
    
    try:
        logger.info(f"Conectando ao SMTP do Gmail (Porta 465) para {to_email}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as smtp:
            logger.info("Realizando login no Gmail...")
            smtp.login(email_address, email_password)
            logger.info("Enviando mensagem...")
            smtp.send_message(msg)
        logger.info(f"E-mail de notificacao enviado com sucesso para {to_email}!")
    except Exception as e:
        logger.error(f"Falha ao enviar o e-mail para {to_email}: {e}")
