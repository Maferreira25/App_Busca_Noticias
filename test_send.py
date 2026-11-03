import os
from whatsapp_sender import send_whatsapp_message

def main():
    import glob
    files = sorted(glob.glob(r"c:\Automações\Automação Busca Noticias de IA\history\boletim_ia_*.md"), key=os.path.getmtime)
    filepath = files[-1] if files else r"c:\Automações\Automação Busca Noticias de IA\history\boletim_ia_25-10-2026_22-17-27.md"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"Enviando o boletim ({os.path.basename(filepath)}) pelo WhatsApp...")
        success = send_whatsapp_message(content)
        if success:
            print("Enviado com SUCESSO!")
        else:
            print("FALHA ao enviar.")
    else:
        print(f"Arquivo não encontrado: {filepath}")

if __name__ == "__main__":
    main()
