import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import subprocess
import threading
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
SCHEDULE_SCRIPT = os.path.join(BASE_DIR, "setup_scheduler.ps1")

def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        return {"emails": [], "ignored_domains": [], "schedule_day": "MON", "schedule_time": "08:00"}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_config(dados):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

class BoletimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel de Automação - Notícias IA")
        self.root.geometry("600x650")
        
        lbl_title = tk.Label(root, text="🚀 Central de Automação de Notícias de IA", font=("Arial", 16, "bold"), fg="#2c3e50")
        lbl_title.pack(pady=(15, 0))
        
        lbl_desc = tk.Label(root, text="Configure destinatários, fontes e agende o envio dos boletins automáticos.", font=("Arial", 10), fg="#7f8c8d")
        lbl_desc.pack(pady=(0, 10))
        
        self.lbl_docker_status = tk.Label(root, text="Serviços (Docker/API): Verificando...", font=("Arial", 10, "italic"), fg="#f39c12")
        self.lbl_docker_status.pack(pady=(0, 10))
        
        # Inicia o Docker e a Evolution API em segundo plano
        threading.Thread(target=self.iniciar_docker_background, daemon=True).start()
        
        self.config = carregar_config()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Tabs
        self.tab_geral = ttk.Frame(self.notebook)
        self.tab_fontes = ttk.Frame(self.notebook)
        self.tab_agendamento = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_geral, text="Geral & E-mails")
        self.notebook.add(self.tab_fontes, text="Fontes & Filtros")
        self.notebook.add(self.tab_agendamento, text="Agendamento")
        
        self.construir_tab_geral()
        self.construir_tab_fontes()
        self.construir_tab_agendamento()

    def construir_tab_geral(self):
        btn_frame = tk.Frame(self.tab_geral)
        btn_frame.pack(pady=20)
        
        btn_gerar = tk.Button(btn_frame, text="⚡ Gerar & Enviar Boletim Agora", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.gerar_agora)
        btn_gerar.pack()
        
        lbl_emails = tk.Label(self.tab_geral, text="Destinatários de E-mails (1 por linha):")
        lbl_emails.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.text_emails = scrolledtext.ScrolledText(self.tab_geral, width=60, height=10)
        self.text_emails.pack(padx=20)
        self.text_emails.insert("1.0", "\n".join(self.config.get("emails", [])))
        
        btn_salvar = tk.Button(self.tab_geral, text="Salvar Lista de E-mails", command=self.salvar_emails)
        btn_salvar.pack(pady=10)

        # Configuracoes de WhatsApp
        lbl_wa = tk.Label(self.tab_geral, text="Configuracoes WhatsApp (Evolution API):", font=("Arial", 10, "bold"))
        lbl_wa.pack(pady=(20, 5), anchor="w", padx=20)

        frame_wa = tk.Frame(self.tab_geral)
        frame_wa.pack(padx=20, fill="x")

        tk.Label(frame_wa, text="Numero (Ex: 55629...):").grid(row=0, column=0, sticky="w")
        self.entry_wa_phone = tk.Entry(frame_wa, width=30)
        self.entry_wa_phone.insert(0, os.getenv("WHATSAPP_PHONE", ""))
        self.entry_wa_phone.grid(row=0, column=1, padx=5, pady=2)

        btn_salvar_wa = tk.Button(self.tab_geral, text="Salvar Numero de WhatsApp", command=self.salvar_wa_config)
        btn_salvar_wa.pack(pady=(10, 5))

        btn_reconectar_wa = tk.Button(self.tab_geral, text="📲 Reconectar WhatsApp (Gerar QR Code)", bg="#3498db", fg="white", font=("Arial", 10, "bold"), command=self.reconectar_whatsapp)
        btn_reconectar_wa.pack(pady=5)

    def construir_tab_fontes(self):
        lbl_domains = tk.Label(self.tab_fontes, text="Domínios Negativados (Excluir da busca - 1 por linha):")
        lbl_domains.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.text_domains = scrolledtext.ScrolledText(self.tab_fontes, width=60, height=15)
        self.text_domains.pack(padx=20)
        self.text_domains.insert("1.0", "\n".join(self.config.get("ignored_domains", [])))
        
        btn_salvar_fontes = tk.Button(self.tab_fontes, text="Salvar Filtros e Fontes", command=self.salvar_fontes)
        btn_salvar_fontes.pack(pady=10)

    def construir_tab_agendamento(self):
        self.dias_map = {
            "MON": "Segunda-feira", "TUE": "Terça-feira", "WED": "Quarta-feira",
            "THU": "Quinta-feira", "FRI": "Sexta-feira", "SAT": "Sábado", "SUN": "Domingo"
        }
        self.dias_reverse = {v: k for k, v in self.dias_map.items()}
        
        frame = tk.Frame(self.tab_agendamento)
        frame.pack(pady=20)
        
        dia_config = self.config.get("schedule_day", "MON")
        hora_config = self.config.get("schedule_time", "08:00")
        dia_pt = self.dias_map.get(dia_config, "Segunda-feira")
        
        self.lbl_status = tk.Label(frame, text=f"📅 Programação Atual: Toda {dia_pt} às {hora_config}", font=("Arial", 11, "bold"), fg="#2980b9")
        self.lbl_status.grid(row=0, columnspan=2, pady=(0, 20))
        
        tk.Label(frame, text="Configurar Dia:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.combo_dia = ttk.Combobox(frame, values=list(self.dias_map.values()), state="readonly")
        self.combo_dia.set(dia_pt)
        self.combo_dia.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(frame, text="Horário (HH:MM):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.entry_hora = tk.Entry(frame)
        self.entry_hora.insert(0, hora_config)
        self.entry_hora.grid(row=2, column=1, padx=10, pady=10)
        self.entry_hora.bind("<KeyRelease>", self.formatar_hora)
        
        btn_agendar = tk.Button(frame, text="Atualizar Tarefa no Windows", command=self.atualizar_agendamento)
        btn_agendar.grid(row=3, columnspan=2, pady=20)
        
        lbl_info = tk.Label(self.tab_agendamento, text="* O agendamento criará/substituirá uma tarefa no Windows Task Scheduler\nchamada 'BoletimIANews'.", fg="gray")
        lbl_info.pack(pady=10)

    def formatar_hora(self, event):
        # Ignorar se for backspace para permitir apagar
        if event.keysym == "BackSpace":
            return
            
        texto = self.entry_hora.get().replace(":", "")
        if len(texto) >= 2:
            novo_texto = texto[:2] + ":" + texto[2:4]
            self.entry_hora.delete(0, tk.END)
            self.entry_hora.insert(0, novo_texto)

    def salvar_emails(self):
        lista = self.text_emails.get("1.0", tk.END).strip().split('\n')
        lista = [e.strip() for e in lista if e.strip()]
        self.config["emails"] = lista
        salvar_config(self.config)
        messagebox.showinfo("Sucesso", "Lista de e-mails atualizada!")

    def salvar_fontes(self):
        lista = self.text_domains.get("1.0", tk.END).strip().split('\n')
        lista = [d.strip() for d in lista if d.strip()]
        self.config["ignored_domains"] = lista
        salvar_config(self.config)
        messagebox.showinfo("Sucesso", "Lista de domínios negativados atualizada!")

    def salvar_wa_config(self):
        phone = self.entry_wa_phone.get().strip()
        
        # Atualizar o .env
        env_path = os.path.join(BASE_DIR, ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        new_lines = []
        found_phone = False
        for line in lines:
            if line.startswith("WHATSAPP_PHONE="):
                new_lines.append(f"WHATSAPP_PHONE={phone}\n")
                found_phone = True
            else:
                new_lines.append(line)
        
        if not found_phone: new_lines.append(f"WHATSAPP_PHONE={phone}\n")
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        # Atualizar variavel de ambiente na sessao atual
        os.environ["WHATSAPP_PHONE"] = phone
        
        messagebox.showinfo("Sucesso", "Numero de WhatsApp salvo com sucesso!")

    def reconectar_whatsapp(self):
        script_path = os.path.join(BASE_DIR, "reconectar_whatsapp.py")
        if not os.path.exists(script_path):
            messagebox.showerror("Erro", "Script de reconexão não encontrado!")
            return
            
        messagebox.showinfo("Aviso", "O processo será iniciado. Aguarde alguns segundos até o navegador abrir com o novo QR Code.")
        python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python"
        
        # Executa o script de reconexão e não bloqueia a interface
        subprocess.Popen(["cmd.exe", "/c", f'"{python_exe}" "{script_path}"'], cwd=BASE_DIR)

    def gerar_agora(self):
        def tarefa():
            try:
                # Usar caminhos absolutos e garantir o cwd correto
                python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python"
                main_script = os.path.join(BASE_DIR, "main.py")
                history_pattern = os.path.join(BASE_DIR, "history", f"boletim_ia_{self.get_today()}*.md")

                # Limpeza prévia (PowerShell de forma mais segura)
                subprocess.run(["powershell", "-Command", f'Remove-Item -Path "{history_pattern}" -ErrorAction SilentlyContinue'], check=False)
                
                # Execucao do script principal
                subprocess.run([python_exe, main_script], check=True, cwd=BASE_DIR)
                
                messagebox.showinfo("Sucesso Total!", 
                    "O Boletim foi gerado e enviado com sucesso!\n\n"
                    "✅ Destinatarios de e-mail notificados.\n"
                    "✅ Mensagem enviada para o WhatsApp.")
            except Exception as e:
                messagebox.showerror("Erro", f"Aconteceu um erro durante a geracao:\n{e}")
        
        messagebox.showinfo("Aviso", "O processo foi iniciado em segundo plano.\nAguarde, isso pode levar até 1 minuto. Você será avisado quando terminar.")
        threading.Thread(target=tarefa, daemon=True).start()

    def iniciar_docker_background(self):
        try:
            from main import ensure_environment
            logger.info("Iniciando rotina de garantia do Docker via Interface...")
            
            self.root.after(0, lambda: self.lbl_docker_status.config(text="Serviços (Docker/API): Iniciando (aguarde)...", fg="#f39c12"))
            
            # A função ensure_environment verifica se o Docker está rodando, inicia o Docker Desktop se não estiver, e sobe os containers.
            success = ensure_environment()
            
            if success:
                self.root.after(0, lambda: self.lbl_docker_status.config(text="Serviços (Docker/API): Online ✅", fg="#27ae60", font=("Arial", 10, "bold")))
            else:
                self.root.after(0, lambda: self.lbl_docker_status.config(text="Serviços (Docker/API): Falha ao Iniciar ❌", fg="#c0392b", font=("Arial", 10, "bold")))
        except Exception as e:
            logger.error(f"Erro ao tentar iniciar Docker via interface: {e}")
            self.root.after(0, lambda: self.lbl_docker_status.config(text="Serviços (Docker/API): Erro Crítico ❌", fg="#c0392b", font=("Arial", 10, "bold")))

    def get_today(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    def atualizar_agendamento(self):
        dia_pt = self.combo_dia.get()
        hora = self.entry_hora.get().strip()
        
        dia_en = self.dias_reverse.get(dia_pt, "MON")
        
        self.config["schedule_day"] = dia_en
        self.config["schedule_time"] = hora
        salvar_config(self.config)
        
        script_path = os.path.join(BASE_DIR, 'main.py')
        python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python"
        
        # Usando PowerShell + CMD para garantir redirecionamento de logs e permissões
        ps_cmd = (
            f"$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c \"\"{python_exe}\" \"{script_path}\" > \"{os.path.join(BASE_DIR, 'debug_agendador.log')}\" 2>&1\"' -WorkingDirectory '{BASE_DIR}'; "
            f"$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {dia_en} -At {hora}; "
            f"Register-ScheduledTask -Action $action -Trigger $trigger -TaskName 'BoletimIANews' -Description 'Envio semanal de noticias de IA' -Force"
        )
        
        try:
            subprocess.run(["powershell", "-Command", ps_cmd], check=True, cwd=BASE_DIR, capture_output=True)
            self.lbl_status.config(text=f"📅 Programação Atual: Toda {dia_pt} às {hora}")
            messagebox.showinfo("Sucesso", f"Tarefa agendada no Windows para toda {dia_pt} às {hora} horas!")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('latin-1', errors='replace')
            logger.error(f"Erro ao agendar tarefa: {error_msg}")
            messagebox.showerror("Erro de Permissao", 
                "Nao foi possivel agendar a tarefa.\n\n"
                "SOLUCAO: Clique com o botao direito no programa (ou no VS Code) e escolha 'Executar como Administrador'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BoletimApp(root)
    root.mainloop()