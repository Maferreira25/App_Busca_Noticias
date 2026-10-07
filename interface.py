import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys
import subprocess
import threading
import logging
import re
import dotenv
from dotenv import load_dotenv, set_key

from constants import (
    DEFAULT_POSITIVE_DOMAINS,
    DEFAULT_IGNORED_DOMAINS,
    DEFAULT_AGENT_DOMAINS,
    SCHEDULE_TASK_NAME,
    SCHEDULE_TASK_NAME_AGENTS,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
SCHEDULE_SCRIPT = os.path.join(BASE_DIR, "setup_scheduler.ps1")


def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "emails": [],
            "ignored_domains": DEFAULT_IGNORED_DOMAINS,
            "positive_domains": DEFAULT_POSITIVE_DOMAINS,
            "schedule_day": "SUN",
            "schedule_time": "22:00",
            "agent_schedule_day": "MON",
            "agent_schedule_time": "08:00",
            "agent_domains": DEFAULT_AGENT_DOMAINS
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)
        if "positive_domains" not in dados:
            dados["positive_domains"] = DEFAULT_POSITIVE_DOMAINS
        if "agent_domains" not in dados:
            dados["agent_domains"] = DEFAULT_AGENT_DOMAINS
        if "agent_schedule_day" not in dados:
            dados["agent_schedule_day"] = "MON"
        if "agent_schedule_time" not in dados:
            dados["agent_schedule_time"] = "08:00"
        return dados

def salvar_config(dados):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

class BoletimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel de Automação - Notícias IA")
        self.root.geometry("680x740")
        
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
        self.tab_agentes = ttk.Frame(self.notebook)
        self.tab_fontes = ttk.Frame(self.notebook)
        self.tab_agendamento = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_geral, text="Geral & E-mails")
        self.notebook.add(self.tab_agentes, text="🤖 Feed de Agentes de IA")
        self.notebook.add(self.tab_fontes, text="Fontes & Filtros")
        self.notebook.add(self.tab_agendamento, text="Agendamentos")
        
        self.construir_tab_geral()
        self.construir_tab_agentes()
        self.construir_tab_fontes()
        self.construir_tab_agendamento()

    def construir_tab_geral(self):
        btn_frame = tk.Frame(self.tab_geral)
        btn_frame.pack(pady=20)
        
        self.btn_gerar = tk.Button(btn_frame, text="⚡ Gerar & Enviar Boletim Geral Agora", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=lambda: self.gerar_agora("geral"))
        self.btn_gerar.pack()

    def construir_tab_agentes(self):
        btn_frame = tk.Frame(self.tab_agentes)
        btn_frame.pack(pady=15)
        
        self.btn_gerar_agentes = tk.Button(
            btn_frame,
            text="🤖 Gerar & Enviar Boletim de Agentes Agora",
            font=("Arial", 12, "bold"),
            bg="#8e44ad",
            fg="white",
            command=lambda: self.gerar_agora("agentes")
        )
        self.btn_gerar_agentes.pack()
        
        lbl_info = tk.Label(
            self.tab_agentes,
            text="Curadoria técnica de 15 papers e inovações em desenvolvimento com Agentes de IA e sistemas multi-agentes.",
            font=("Arial", 9, "italic"),
            fg="#555"
        )
        lbl_info.pack(pady=(0, 10))

        # Fontes de Agentes
        lbl_fontes_ag = tk.Label(
            self.tab_agentes,
            text="🌐 Fontes de Referência em Agentes & Pesquisa (1 por linha):",
            font=("Arial", 10, "bold"),
            fg="#8e44ad"
        )
        lbl_fontes_ag.pack(pady=(10, 3), anchor="w", padx=20)
        
        lbl_fontes_sub = tk.Label(
            self.tab_agentes,
            text="Hugging Face, DAIR.AI, arXiv, OpenAI, Anthropic, DeepMind, Stanford, MIT, BAIR, Microsoft, LangChain, etc:",
            font=("Arial", 8),
            fg="#7f8c8d"
        )
        lbl_fontes_sub.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.text_agent_domains = scrolledtext.ScrolledText(self.tab_agentes, width=70, height=11)
        self.text_agent_domains.pack(padx=20, fill="x")
        self.text_agent_domains.insert("1.0", "\n".join(self.config.get("agent_domains", DEFAULT_AGENT_DOMAINS)))
        
        frame_btn_ag = tk.Frame(self.tab_agentes)
        frame_btn_ag.pack(pady=15)
        
        btn_salvar_ag = tk.Button(
            frame_btn_ag,
            text="💾 Salvar Fontes de Agentes",
            font=("Arial", 10, "bold"),
            bg="#2980b9",
            fg="white",
            command=self.salvar_fontes_agentes
        )
        btn_salvar_ag.pack(side="left", padx=10)
        
        btn_restaurar_ag = tk.Button(
            frame_btn_ag,
            text="🔄 Restaurar Fontes Padrão de Agentes",
            font=("Arial", 9),
            command=self.restaurar_fontes_agentes_padrao
        )
        btn_restaurar_ag.pack(side="left", padx=10)
        
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
        # 1. Domínios Positivos
        lbl_pos = tk.Label(self.tab_fontes, text="✅ Domínios Positivos (Fontes monitoradas nas buscas - 1 por linha):", font=("Arial", 10, "bold"), fg="#27ae60")
        lbl_pos.pack(pady=(15, 3), anchor="w", padx=20)
        
        lbl_pos_sub = tk.Label(self.tab_fontes, text="Todas as fontes de alto relevo (Jurídicas, Acadêmicas e Tecnologia). Edite, adicione ou remova conforme desejar:", font=("Arial", 8), fg="#7f8c8d")
        lbl_pos_sub.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.text_positive_domains = scrolledtext.ScrolledText(self.tab_fontes, width=70, height=10)
        self.text_positive_domains.pack(padx=20, fill="x")
        self.text_positive_domains.insert("1.0", "\n".join(self.config.get("positive_domains", DEFAULT_POSITIVE_DOMAINS)))
        
        # 2. Domínios Negativados
        lbl_neg = tk.Label(self.tab_fontes, text="⛔ Domínios Negativados (Excluir da busca - 1 por linha):", font=("Arial", 10, "bold"), fg="#c0392b")
        lbl_neg.pack(pady=(15, 3), anchor="w", padx=20)
        
        lbl_neg_sub = tk.Label(self.tab_fontes, text="Sites que devem ser excluídos mesmo que mencionem termos de IA (ex: passagens aéreas, fofocas):", font=("Arial", 8), fg="#7f8c8d")
        lbl_neg_sub.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.text_domains = scrolledtext.ScrolledText(self.tab_fontes, width=70, height=7)
        self.text_domains.pack(padx=20, fill="x")
        self.text_domains.insert("1.0", "\n".join(self.config.get("ignored_domains", DEFAULT_IGNORED_DOMAINS)))
        
        # Botões de ação
        frame_btn_fontes = tk.Frame(self.tab_fontes)
        frame_btn_fontes.pack(pady=15)
        
        btn_salvar_fontes = tk.Button(frame_btn_fontes, text="💾 Salvar Configurações de Fontes", font=("Arial", 10, "bold"), bg="#2980b9", fg="white", command=self.salvar_fontes)
        btn_salvar_fontes.pack(side="left", padx=10)
        
        btn_restaurar = tk.Button(frame_btn_fontes, text="🔄 Restaurar Fontes Padrão", font=("Arial", 9), command=self.restaurar_fontes_padrao)
        btn_restaurar.pack(side="left", padx=10)

    def salvar_fontes_agentes(self):
        lista = self.text_agent_domains.get("1.0", tk.END).strip().split('\n')
        lista = [d.strip().lower() for d in lista if d.strip()]
        self.config["agent_domains"] = lista
        salvar_config(self.config)
        messagebox.showinfo("Sucesso", f"Fontes de agentes atualizadas!\n\n🌐 {len(lista)} fontes de referência monitoradas.")

    def restaurar_fontes_agentes_padrao(self):
        if messagebox.askyesno("Restaurar Padrões", "Deseja redefinir as fontes de agentes para os padrões recomendados?"):
            self.text_agent_domains.delete("1.0", tk.END)
            self.text_agent_domains.insert("1.0", "\n".join(DEFAULT_AGENT_DOMAINS))
            self.salvar_fontes_agentes()

    def construir_tab_agendamento(self):
        self.dias_map = {
            "MON": "Segunda-feira", "TUE": "Terça-feira", "WED": "Quarta-feira",
            "THU": "Quinta-feira", "FRI": "Sexta-feira", "SAT": "Sábado", "SUN": "Domingo"
        }
        self.dias_reverse = {v: k for k, v in self.dias_map.items()}
        
        container = tk.Frame(self.tab_agendamento)
        container.pack(pady=10, fill="both", expand=True, padx=20)
        
        # 1. Seção Boletim Geral
        frame_geral = ttk.LabelFrame(container, text=" 📰 1. Agendamento - Boletim Geral (Notícias & Jurídico) ", padding=10)
        frame_geral.pack(fill="x", pady=8)
        
        dia_config_g = self.config.get("schedule_day", "SUN")
        hora_config_g = self.config.get("schedule_time", "22:00")
        dia_pt_g = self.dias_map.get(dia_config_g, "Domingo")
        
        self.lbl_status_geral = tk.Label(frame_geral, text=f"📅 Programação Geral: Toda {dia_pt_g} às {hora_config_g}", font=("Arial", 10, "bold"), fg="#27ae60")
        self.lbl_status_geral.grid(row=0, columnspan=2, pady=(0, 10), sticky="w")
        
        tk.Label(frame_geral, text="Dia da Semana:").grid(row=1, column=0, padx=5, pady=4, sticky="e")
        self.combo_dia_geral = ttk.Combobox(frame_geral, values=list(self.dias_map.values()), state="readonly", width=18)
        self.combo_dia_geral.set(dia_pt_g)
        self.combo_dia_geral.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        
        tk.Label(frame_geral, text="Horário (HH:MM):").grid(row=2, column=0, padx=5, pady=4, sticky="e")
        self.entry_hora_geral = tk.Entry(frame_geral, width=12)
        self.entry_hora_geral.insert(0, hora_config_g)
        self.entry_hora_geral.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        self.entry_hora_geral.bind("<KeyRelease>", lambda e: self.formatar_hora_campo(self.entry_hora_geral, e))
        
        btn_agendar_geral = tk.Button(frame_geral, text="💾 Atualizar Tarefa Geral no Windows", font=("Arial", 9, "bold"), bg="#27ae60", fg="white", command=lambda: self.atualizar_agendamento("geral"))
        btn_agendar_geral.grid(row=3, columnspan=2, pady=10)

        # 2. Seção Boletim Agentes de IA
        frame_agentes = ttk.LabelFrame(container, text=" 🤖 2. Agendamento - Boletim Técnico (Agentes de IA & Papers) ", padding=10)
        frame_agentes.pack(fill="x", pady=8)
        
        dia_config_a = self.config.get("agent_schedule_day", "MON")
        hora_config_a = self.config.get("agent_schedule_time", "08:00")
        dia_pt_a = self.dias_map.get(dia_config_a, "Segunda-feira")
        
        self.lbl_status_agentes = tk.Label(frame_agentes, text=f"📅 Programação Agentes: Toda {dia_pt_a} às {hora_config_a}", font=("Arial", 10, "bold"), fg="#8e44ad")
        self.lbl_status_agentes.grid(row=0, columnspan=2, pady=(0, 10), sticky="w")
        
        tk.Label(frame_agentes, text="Dia da Semana:").grid(row=1, column=0, padx=5, pady=4, sticky="e")
        self.combo_dia_agentes = ttk.Combobox(frame_agentes, values=list(self.dias_map.values()), state="readonly", width=18)
        self.combo_dia_agentes.set(dia_pt_a)
        self.combo_dia_agentes.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        
        tk.Label(frame_agentes, text="Horário (HH:MM):").grid(row=2, column=0, padx=5, pady=4, sticky="e")
        self.entry_hora_agentes = tk.Entry(frame_agentes, width=12)
        self.entry_hora_agentes.insert(0, hora_config_a)
        self.entry_hora_agentes.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        self.entry_hora_agentes.bind("<KeyRelease>", lambda e: self.formatar_hora_campo(self.entry_hora_agentes, e))
        
        btn_agendar_agentes = tk.Button(frame_agentes, text="💾 Atualizar Tarefa de Agentes no Windows", font=("Arial", 9, "bold"), bg="#8e44ad", fg="white", command=lambda: self.atualizar_agendamento("agentes"))
        btn_agendar_agentes.grid(row=3, columnspan=2, pady=10)

        lbl_info = tk.Label(container, text="* O agendamento gerencia as tarefas independentes 'BoletimIANews' e 'BoletimIAAgentes' no Windows.", fg="gray", font=("Arial", 8))
        lbl_info.pack(pady=5)

    def formatar_hora_campo(self, entry_widget, event):
        if event.keysym == "BackSpace":
            return
        texto = entry_widget.get().replace(":", "")
        if len(texto) >= 2:
            novo_texto = texto[:2] + ":" + texto[2:4]
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, novo_texto)

    def salvar_emails(self):
        lista = self.text_emails.get("1.0", tk.END).strip().split('\n')
        lista = [e.strip() for e in lista if e.strip()]
        self.config["emails"] = lista
        salvar_config(self.config)
        messagebox.showinfo("Sucesso", "Lista de e-mails atualizada!")

    def salvar_fontes(self):
        # Domínios Positivos
        lista_pos = self.text_positive_domains.get("1.0", tk.END).strip().split('\n')
        lista_pos = [d.strip().lower() for d in lista_pos if d.strip()]
        self.config["positive_domains"] = lista_pos
        
        # Domínios Negativos
        lista_neg = self.text_domains.get("1.0", tk.END).strip().split('\n')
        lista_neg = [d.strip().lower() for d in lista_neg if d.strip()]
        self.config["ignored_domains"] = lista_neg
        
        salvar_config(self.config)
        messagebox.showinfo("Sucesso", f"Configurações de fontes atualizadas!\n\n✅ {len(lista_pos)} domínios positivos monitorados.\n⛔ {len(lista_neg)} domínios negativados.")

    def restaurar_fontes_padrao(self):
        if messagebox.askyesno("Restaurar Padrões", "Deseja redefinir as listas de domínios positivos e negativos para os padrões recomendados?"):
            self.text_positive_domains.delete("1.0", tk.END)
            self.text_positive_domains.insert("1.0", "\n".join(DEFAULT_POSITIVE_DOMAINS))
            self.text_domains.delete("1.0", tk.END)
            self.text_domains.insert("1.0", "\n".join(DEFAULT_IGNORED_DOMAINS))
            self.salvar_fontes()

    def salvar_wa_config(self):
        phone = self.entry_wa_phone.get().strip()
        env_path = os.path.join(BASE_DIR, ".env")
        try:
            set_key(env_path, "WHATSAPP_PHONE", phone)
            os.environ["WHATSAPP_PHONE"] = phone
            messagebox.showinfo("Sucesso", "Número de WhatsApp salvo com sucesso no .env!")
        except Exception as e:
            logger.error(f"Erro ao salvar WHATSAPP_PHONE no .env: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar o número no .env: {e}")

    def reconectar_whatsapp(self):
        script_path = os.path.join(BASE_DIR, "reconectar_whatsapp.py")
        if not os.path.exists(script_path):
            messagebox.showerror("Erro", "Script de reconexão não encontrado!")
            return
            
        messagebox.showinfo("Aviso", "O processo será iniciado. Aguarde alguns segundos até o navegador abrir com o novo QR Code.")
        python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python"
        subprocess.Popen(["cmd.exe", "/c", f'"{python_exe}" "{script_path}"'], cwd=BASE_DIR)

    def gerar_agora(self, tipo="geral"):
        btn = self.btn_gerar_agentes if tipo == "agentes" else self.btn_gerar
        btn_label = "🤖 Gerar & Enviar Boletim de Agentes Agora" if tipo == "agentes" else "⚡ Gerar & Enviar Boletim Geral Agora"
        prefixo = "boletim_ia_agentes" if tipo == "agentes" else "boletim_ia"
        titulo_dialogo = "Boletim de Agentes de IA" if tipo == "agentes" else "Boletim Geral de IA"

        def tarefa():
            try:
                python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python"
                main_script = os.path.join(BASE_DIR, "main.py")
                
                # Limpeza prévia segura usando biblioteca nativa do Python
                import glob
                history_dir = os.path.join(BASE_DIR, "history")
                if os.path.exists(history_dir):
                    patterns = [
                        os.path.join(history_dir, f"{prefixo}_{self.get_today_br()}*.md"),
                        os.path.join(history_dir, f"{prefixo}_{self.get_today()}*.md"),
                    ]
                    for pattern in patterns:
                        for fpath in glob.glob(pattern):
                            try:
                                os.remove(fpath)
                            except OSError:
                                pass
                
                creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                res = subprocess.run(
                    [python_exe, main_script, "--type", tipo],
                    capture_output=True,
                    text=True,
                    cwd=BASE_DIR,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=creation_flags
                )
                
                if res.returncode != 0:
                    detalhe_erro = ""
                    log_file = os.path.join(BASE_DIR, "boletim.log")
                    if os.path.exists(log_file):
                        try:
                            with open(log_file, "r", encoding="utf-8", errors="replace") as lf:
                                lines = [l.strip() for l in lf.readlines() if l.strip()]
                                err_lines = [l for l in lines[-25:] if "ERROR" in l or "Traceback" in l or "Exception" in l]
                                if err_lines:
                                    detalhe_erro = "\n".join(err_lines[-4:])
                        except Exception:
                            pass
                    if not detalhe_erro:
                        if res.stderr and res.stderr.strip():
                            detalhe_erro = res.stderr.strip()
                        else:
                            detalhe_erro = f"O processo foi finalizado com código {res.returncode}."
                    
                    self.root.after(0, lambda msg=detalhe_erro: messagebox.showerror(
                        "Erro na Geração", 
                        f"Ocorreu um erro durante a execução do {titulo_dialogo}:\n\n{msg}"
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Sucesso Total!", 
                        f"O {titulo_dialogo} foi gerado e enviado com sucesso!\n\n"
                        "✅ Destinatários de e-mail notificados.\n"
                        "✅ Mensagem enviada para o WhatsApp."
                    ))
            except Exception as e:
                self.root.after(0, lambda msg=str(e): messagebox.showerror("Erro", f"Aconteceu um erro durante a geração:\n{msg}"))
            finally:
                self.root.after(0, lambda: btn.config(state="normal", text=btn_label))
        
        btn.config(state="disabled", text="⏳ Gerando Boletim (aguarde cerca de 1 min)...")
        threading.Thread(target=tarefa, daemon=True).start()

    def iniciar_docker_background(self):
        try:
            from docker_manager import ensure_environment
            logger.info("Iniciando rotina de garantia do Docker via Interface...")
            self.root.after(0, lambda: self.lbl_docker_status.config(text="Serviços (Docker/API): Iniciando (aguarde)...", fg="#f39c12"))
            
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

    def get_today_br(self):
        from datetime import datetime
        return datetime.now().strftime("%d-%m-%Y")

    def atualizar_agendamento(self, tipo="geral"):
        if tipo == "agentes":
            dia_pt = self.combo_dia_agentes.get()
            hora = self.entry_hora_agentes.get().strip()
            task_name = SCHEDULE_TASK_NAME_AGENTS
            task_desc = "Envio semanal de papers e inovacoes com Agentes de IA"
            dia_key = "agent_schedule_day"
            hora_key = "agent_schedule_time"
            lbl_widget = self.lbl_status_agentes
            lbl_prefix = "📅 Programação Agentes: Toda"
            arg_flag = "--type agentes"
            log_name = "debug_agendador_agentes.log"
        else:
            dia_pt = self.combo_dia_geral.get()
            hora = self.entry_hora_geral.get().strip()
            task_name = SCHEDULE_TASK_NAME
            task_desc = "Envio semanal de noticias gerais e juridicas de IA"
            dia_key = "schedule_day"
            hora_key = "schedule_time"
            lbl_widget = self.lbl_status_geral
            lbl_prefix = "📅 Programação Geral: Toda"
            arg_flag = "--type geral"
            log_name = "debug_agendador.log"

        if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", hora):
            messagebox.showerror(
                "Horário Inválido",
                "Por favor, insira o horário no formato válido HH:MM (ex: 08:00, 22:30)."
            )
            return

        dia_en = self.dias_reverse.get(dia_pt, "MON")
        self.config[dia_key] = dia_en
        self.config[hora_key] = hora
        salvar_config(self.config)

        script_path = os.path.join(BASE_DIR, 'main.py')
        python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python"

        ps_cmd = (
            f"$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c \"\"{python_exe}\" \"{script_path}\" {arg_flag} > \"{os.path.join(BASE_DIR, log_name)}\" 2>&1\"' -WorkingDirectory '{BASE_DIR}'; "
            f"$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {dia_en} -At {hora}; "
            f"Register-ScheduledTask -Action $action -Trigger $trigger -TaskName '{task_name}' -Description '{task_desc}' -Force"
        )

        try:
            subprocess.run(["powershell", "-Command", ps_cmd], check=True, cwd=BASE_DIR, capture_output=True)
            lbl_widget.config(text=f"{lbl_prefix} {dia_pt} às {hora}")
            messagebox.showinfo("Sucesso", f"Tarefa '{task_name}' agendada no Windows para toda {dia_pt} às {hora} horas!")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('latin-1', errors='replace')
            logger.error(f"Erro ao agendar tarefa {task_name}: {error_msg}")
            messagebox.showerror(
                "Erro de Permissão", 
                f"Não foi possível agendar a tarefa '{task_name}'.\n\n"
                "SOLUÇÃO: Execute o programa ou terminal como Administrador."
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = BoletimApp(root)
    root.mainloop()