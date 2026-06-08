import os
from whatsapp_sender import send_whatsapp_message

def main():
    filepath = r"c:\Automações\Automação Busca Noticias de IA\history\boletim_ia_07-06-2026_21-04-47.md"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        print("Enviando o boletim de hoje pelo WhatsApp...")
        success = send_whatsapp_message(content)
        if success:
            print("Enviado com SUCESSO!")
        else:
            print("FALHA ao enviar.")
    else:
        print(f"Arquivo não encontrado: {filepath}")

if __name__ == "__main__":
    main()
