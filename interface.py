import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys
import subprocess
import threading
import logging
import re
import time
import base64
import requests
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
        self.root.geometry("680x760")
        
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
        self.tab_contatos = ttk.Frame(self.notebook)
        self.tab_whatsapp = ttk.Frame(self.notebook)
        self.tab_agendamento = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_geral, text="Geral & Fontes")
        self.notebook.add(self.tab_agentes, text="🤖 Feed de Agentes de IA")
        self.notebook.add(self.tab_contatos, text="E-mails & WhatsApp")
        self.notebook.add(self.tab_whatsapp, text="📲 Conexão WhatsApp")
        self.notebook.add(self.tab_agendamento, text="Agendamentos")
        
        self.construir_tab_geral()
        self.construir_tab_agentes()
        self.construir_tab_contatos()
        self.construir_tab_whatsapp()
        self.construir_tab_agendamento()

    def construir_tab_geral(self):
        btn_frame = tk.Frame(self.tab_geral)
        btn_frame.pack(pady=(12, 6))
        
        self.btn_gerar = tk.Button(
            btn_frame,
            text="⚡ Gerar & Enviar Boletim Geral Agora",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#3e8e41",
            activeforeground="white",
            disabledforeground="white",
            command=lambda: self.gerar_agora("geral")
        )
        self.btn_gerar.pack()

        # 1. Domínios Positivos
        lbl_pos = tk.Label(self.tab_geral, text="✅ Domínios Positivos (Fontes monitoradas nas buscas - 1 por linha):", font=("Arial", 10, "bold"), fg="#27ae60")
        lbl_pos.pack(pady=(8, 2), anchor="w", padx=20)
        
        lbl_pos_sub = tk.Label(self.tab_geral, text="Todas as fontes de alto relevo (Jurídicas, Acadêmicas e Tecnologia). Edite, adicione ou remova conforme desejar:", font=("Arial", 8), fg="#7f8c8d")
        lbl_pos_sub.pack(anchor="w", padx=20, pady=(0, 4))
        
        self.text_positive_domains = scrolledtext.ScrolledText(self.tab_geral, width=70, height=8)
        self.text_positive_domains.pack(padx=20, fill="x")
        self.text_positive_domains.insert("1.0", "\n".join(self.config.get("positive_domains", DEFAULT_POSITIVE_DOMAINS)))
        
        # 2. Domínios Negativados
        lbl_neg = tk.Label(self.tab_geral, text="⛔ Domínios Negativados (Excluir da busca - 1 por linha):", font=("Arial", 10, "bold"), fg="#c0392b")
        lbl_neg.pack(pady=(10, 2), anchor="w", padx=20)
        
        lbl_neg_sub = tk.Label(self.tab_geral, text="Sites que devem ser excluídos mesmo que mencionem termos de IA (ex: passagens aéreas, fofocas):", font=("Arial", 8), fg="#7f8c8d")
        lbl_neg_sub.pack(anchor="w", padx=20, pady=(0, 4))
        
        self.text_domains = scrolledtext.ScrolledText(self.tab_geral, width=70, height=6)
        self.text_domains.pack(padx=20, fill="x")
        self.text_domains.insert("1.0", "\n".join(self.config.get("ignored_domains", DEFAULT_IGNORED_DOMAINS)))
        
        # Botões de ação
        frame_btn_fontes = tk.Frame(self.tab_geral)
        frame_btn_fontes.pack(pady=12)
        
        btn_salvar_fontes = tk.Button(frame_btn_fontes, text="💾 Salvar Configurações de Fontes", font=("Arial", 10, "bold"), bg="#2980b9", fg="white", command=self.salvar_fontes)
        btn_salvar_fontes.pack(side="left", padx=10)
        
        btn_restaurar = tk.Button(frame_btn_fontes, text="🔄 Restaurar Fontes Padrão", font=("Arial", 9), command=self.restaurar_fontes_padrao)
        btn_restaurar.pack(side="left", padx=10)

    def construir_tab_agentes(self):
        btn_frame = tk.Frame(self.tab_agentes)
        btn_frame.pack(pady=15)
        
        self.btn_gerar_agentes = tk.Button(
            btn_frame,
            text="🤖 Gerar & Enviar Boletim de Agentes Agora",
            font=("Arial", 12, "bold"),
            bg="#1a365d",
            fg="white",
            activebackground="#0f2544",
            activeforeground="white",
            disabledforeground="white",
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
            fg="#1a365d"
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

    def construir_tab_contatos(self):
        # 1. Destinatários de E-mails
        lbl_emails = tk.Label(self.tab_contatos, text="📧 Destinatários de E-mails (1 por linha):", font=("Arial", 10, "bold"), fg="#2c3e50")
        lbl_emails.pack(pady=(15, 3), anchor="w", padx=20)
        
        lbl_emails_sub = tk.Label(self.tab_contatos, text="Lista de e-mails que receberão as edições automáticas dos boletins:", font=("Arial", 8), fg="#7f8c8d")
        lbl_emails_sub.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.text_emails = scrolledtext.ScrolledText(self.tab_contatos, width=70, height=9)
        self.text_emails.pack(padx=20, fill="x")
        self.text_emails.insert("1.0", "\n".join(self.config.get("emails", [])))
        
        btn_salvar = tk.Button(self.tab_contatos, text="💾 Salvar Lista de E-mails", font=("Arial", 10, "bold"), bg="#2980b9", fg="white", command=self.salvar_emails)
        btn_salvar.pack(pady=(8, 20))

        # 2. Configurações de WhatsApp
        lbl_wa = tk.Label(self.tab_contatos, text="📲 Configurações WhatsApp (Evolution API):", font=("Arial", 10, "bold"), fg="#2c3e50")
        lbl_wa.pack(pady=(5, 5), anchor="w", padx=20)

        frame_wa = tk.Frame(self.tab_contatos)
        frame_wa.pack(padx=20, fill="x")

        tk.Label(frame_wa, text="Número com DDI e DDD (Ex: 55629...):", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_wa_phone = tk.Entry(frame_wa, width=32)
        self.entry_wa_phone.insert(0, os.getenv("WHATSAPP_PHONE", ""))
        self.entry_wa_phone.grid(row=0, column=1, padx=8, pady=5)

        frame_btn_wa = tk.Frame(self.tab_contatos)
        frame_btn_wa.pack(pady=10)

        btn_salvar_wa = tk.Button(frame_btn_wa, text="💾 Salvar Número de WhatsApp", font=("Arial", 9, "bold"), command=self.salvar_wa_config)
        btn_salvar_wa.pack(side="left", padx=8)

        btn_reconectar_wa = tk.Button(frame_btn_wa, text="📲 Reconectar WhatsApp (Gerar QR Code)", bg="#3498db", fg="white", font=("Arial", 9, "bold"), command=self.reconectar_whatsapp)
        btn_reconectar_wa.pack(side="left", padx=8)

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
        
        self.lbl_status_agentes = tk.Label(frame_agentes, text=f"📅 Programação Agentes: Toda {dia_pt_a} às {hora_config_a}", font=("Arial", 10, "bold"), fg="#1a365d")
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
        
        btn_agendar_agentes = tk.Button(
            frame_agentes,
            text="💾 Atualizar Tarefa de Agentes no Windows",
            font=("Arial", 9, "bold"),
            bg="#1a365d",
            fg="white",
            activebackground="#0f2544",
            activeforeground="white",
            disabledforeground="white",
            command=lambda: self.atualizar_agendamento("agentes")
        )
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
        self.notebook.select(self.tab_whatsapp)
        self.resetar_e_gerar_qrcode()

    def obter_credenciais_evolution(self):
        url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
        key = os.getenv("EVOLUTION_API_KEY", "")
        instance = os.getenv("EVOLUTION_INSTANCE", "BoletimIA")
        return url, key, instance

    def construir_tab_whatsapp(self):
        container = tk.Frame(self.tab_whatsapp)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Header
        lbl_header = tk.Label(
            container, 
            text="📲 Central de Conexão WhatsApp (Evolution API)", 
            font=("Arial", 11, "bold"), 
            fg="#2c3e50"
        )
        lbl_header.pack(pady=(2, 2), anchor="w")

        lbl_header_sub = tk.Label(
            container, 
            text="Monitore a sessão, realize o reset completo e escaneie o QR Code diretamente nesta tela.", 
            font=("Arial", 8), 
            fg="#7f8c8d"
        )
        lbl_header_sub.pack(anchor="w", pady=(0, 10))

        # 2. Card de Status
        frame_status = ttk.LabelFrame(container, text=" Status da Conexão ", padding=10)
        frame_status.pack(fill="x", pady=(0, 10))

        frame_status_inner = tk.Frame(frame_status)
        frame_status_inner.pack(fill="x")

        self.lbl_wa_status_icon = tk.Label(frame_status_inner, text="⏳", font=("Arial", 16))
        self.lbl_wa_status_icon.pack(side="left", padx=(5, 12))

        frame_status_text = tk.Frame(frame_status_inner)
        frame_status_text.pack(side="left", fill="x", expand=True)

        self.lbl_wa_status_title = tk.Label(
            frame_status_text, 
            text="Consultando Evolution API...", 
            font=("Arial", 10, "bold"), 
            fg="#2c3e50"
        )
        self.lbl_wa_status_title.pack(anchor="w")

        self.lbl_wa_status_desc = tk.Label(
            frame_status_text, 
            text="Aguarde enquanto verificamos a conexão do WhatsApp...", 
            font=("Arial", 9), 
            fg="#7f8c8d"
        )
        self.lbl_wa_status_desc.pack(anchor="w")

        btn_verificar = tk.Button(
            frame_status, 
            text="🔄 Atualizar Status", 
            font=("Arial", 9), 
            command=self.verificar_status_whatsapp
        )
        btn_verificar.pack(anchor="e", pady=(4, 0))

        # 3. Botões de Ação
        frame_acoes = tk.Frame(container)
        frame_acoes.pack(fill="x", pady=(0, 10))

        self.btn_reset_qr = tk.Button(
            frame_acoes,
            text="🔄 Resetar Sessão & Gerar Novo QR Code",
            font=("Arial", 10, "bold"),
            bg="#e67e22",
            fg="white",
            activebackground="#d35400",
            activeforeground="white",
            padx=12,
            pady=6,
            command=self.resetar_e_gerar_qrcode
        )
        self.btn_reset_qr.pack(side="left", padx=(0, 10))

        self.btn_teste_wa = tk.Button(
            frame_acoes,
            text="✉️ Enviar Mensagem de Teste",
            font=("Arial", 9, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#219150",
            activeforeground="white",
            padx=10,
            pady=6,
            command=self.enviar_teste_whatsapp
        )
        self.btn_teste_wa.pack(side="left")

        # 4. Área de Exibição do QR Code
        self.frame_qr_display = ttk.LabelFrame(container, text=" Pareamento via QR Code ", padding=10)
        self.frame_qr_display.pack(fill="both", expand=True)

        self.lbl_qr_msg = tk.Label(
            self.frame_qr_display,
            text="Se a sessão estiver desconectada ou instável, clique no botão acima para resetar e gerar o QR Code.",
            font=("Arial", 9, "italic"),
            fg="#555",
            wraplength=580
        )
        self.lbl_qr_msg.pack(pady=(0, 6))

        # Moldura do QR Code
        self.frame_qr_box = tk.Frame(self.frame_qr_display, bg="#ffffff", bd=2, relief="groove")
        self.frame_qr_box.pack(pady=4)

        self.lbl_qr_image = tk.Label(
            self.frame_qr_box, 
            text="Nenhum QR Code ativo no momento.", 
            bg="#ffffff", 
            font=("Arial", 9), 
            width=36, 
            height=13
        )
        self.lbl_qr_image.pack(padx=8, pady=8)
        self.qr_photo = None

        self.lbl_instrucao_qr = tk.Label(
            self.frame_qr_display,
            text="Instruções: Abra o WhatsApp no celular > Aparelhos Conectados > Conectar um aparelho > Escaneie o QR Code.",
            font=("Arial", 8),
            fg="#7f8c8d",
            justify="center",
            wraplength=560
        )
        self.lbl_instrucao_qr.pack(pady=(6, 2))

        # Checagem inicial de status após abrir
        self.root.after(1200, self.verificar_status_whatsapp)

    def verificar_status_whatsapp(self):
        def tarefa():
            url, key, inst = self.obter_credenciais_evolution()
            headers = {"apikey": key, "Content-Type": "application/json"}
            try:
                r_state = requests.get(f"{url}/instance/connectionState/{inst}", headers=headers, timeout=5)
                if r_state.status_code == 200:
                    state = r_state.json().get("instance", {}).get("state", "").lower()
                    if state == "open":
                        detalhes = ""
                        try:
                            r_inst = requests.get(f"{url}/instance/fetchInstances", headers=headers, timeout=5)
                            if r_inst.status_code == 200:
                                for item in r_inst.json():
                                    dados_inst = item.get("instance", {})
                                    if dados_inst.get("instanceName") == inst:
                                        owner = dados_inst.get("owner", "").split("@")[0]
                                        name = dados_inst.get("profileName", "")
                                        detalhes = f" | {name} ({owner})" if owner else ""
                                        break
                        except Exception:
                            pass

                        self.root.after(0, lambda: self._atualizar_ui_status(
                            "🟢",
                            "WhatsApp Conectado com Sucesso! ✅",
                            f"Instância: {inst}{detalhes} - Sessão ativa e pronta para envios.",
                            "#27ae60",
                            is_open=True
                        ))
                        return
                    elif state == "connecting":
                        self.root.after(0, lambda: self._atualizar_ui_status(
                            "🟡",
                            "WhatsApp Conectando... ⏳",
                            f"Instância: {inst} - Estabelecendo sincronização com o WhatsApp.",
                            "#f39c12",
                            is_open=False
                        ))
                        return

                self.root.after(0, lambda: self._atualizar_ui_status(
                    "🔴",
                    "WhatsApp Desconectado ❌",
                    f"Instância: {inst} - Sessão desconectada. Clique em 'Resetar Sessão & Gerar Novo QR Code'.",
                    "#c0392b",
                    is_open=False
                ))
            except Exception as e:
                self.root.after(0, lambda: self._atualizar_ui_status(
                    "⚠️",
                    "Evolution API Indisponível ⚠️",
                    f"Não foi possível conectar em {url} ({e}). Verifique se o Docker está online.",
                    "#e74c3c",
                    is_open=False
                ))

        threading.Thread(target=tarefa, daemon=True).start()

    def _atualizar_ui_status(self, icon, title, desc, color, is_open=False):
        self.lbl_wa_status_icon.config(text=icon)
        self.lbl_wa_status_title.config(text=title, fg=color)
        self.lbl_wa_status_desc.config(text=desc)
        if is_open and self.qr_photo is not None:
            self.qr_photo = None
            self.lbl_qr_image.config(
                image="",
                text="✅ Sessão ativa!\nSeu WhatsApp já está conectado e pronto para uso.",
                fg="#27ae60",
                font=("Arial", 11, "bold"),
                width=36,
                height=11
            )
            self.lbl_qr_msg.config(
                text="Tudo pronto! Caso precise trocar de aparelho ou reiniciar a sessão, clique em Resetar.",
                fg="#27ae60"
            )

    def resetar_e_gerar_qrcode(self):
        if not messagebox.askyesno(
            "Confirmar Reset",
            "Deseja resetar a sessão do WhatsApp na Evolution API e gerar um novo QR Code diretamente na tela?\n\n"
            "Isso deslogará a sessão anterior para limpar eventuais erros de cache."
        ):
            return

        self.btn_reset_qr.config(state="disabled", text="⏳ Resetando sessão...")
        self.lbl_qr_msg.config(text="Limpando sessão antiga e gerando novo QR Code... Aguarde alguns instantes.", fg="#e67e22")
        self.lbl_qr_image.config(image="", text="Gerando QR Code... Aguarde.", fg="#555", width=36, height=11)

        def tarefa():
            url, key, inst = self.obter_credenciais_evolution()
            headers = {"apikey": key, "Content-Type": "application/json"}

            try:
                try:
                    requests.delete(f"{url}/instance/logout/{inst}", headers=headers, timeout=6)
                except Exception:
                    pass

                try:
                    requests.delete(f"{url}/instance/delete/{inst}", headers=headers, timeout=6)
                except Exception:
                    pass

                time.sleep(2)

                payload = {
                    "instanceName": inst,
                    "token": key,
                    "qrcode": True
                }
                requests.post(f"{url}/instance/create", json=payload, headers=headers, timeout=10)
                time.sleep(1)

                base64_str = None
                for _ in range(5):
                    try:
                        r_qr = requests.get(f"{url}/instance/connect/{inst}", headers=headers, timeout=10)
                        if r_qr.status_code == 200:
                            data = r_qr.json()
                            base64_str = data.get("base64") or (data.get("qrcode", {}).get("base64") if isinstance(data.get("qrcode"), dict) else None)
                            if base64_str:
                                break
                    except Exception:
                        pass
                    time.sleep(2)

                if base64_str:
                    if "," in base64_str:
                        base64_str = base64_str.split(",")[1]

                    try:
                        with open(os.path.join(BASE_DIR, "qrcode.png"), "wb") as f:
                            f.write(base64.b64decode(base64_str))
                    except Exception:
                        pass

                    def atualizar_qr_ui(b64_data):
                        # Usa o suporte nativo do Tkinter a PNG em base64 (sem depender de PIL/Pillow)
                        raw_photo = tk.PhotoImage(data=b64_data)
                        if raw_photo.width() > 250:
                            self.qr_photo = raw_photo.subsample(3, 3).zoom(2, 2)
                        else:
                            self.qr_photo = raw_photo
                        self.lbl_qr_image.config(image=self.qr_photo, text="", width=0, height=0)
                        self.lbl_qr_msg.config(
                            text="📲 QR Code gerado! Aponte a câmera do seu WhatsApp para o código abaixo:",
                            fg="#27ae60",
                            font=("Arial", 9, "bold")
                        )
                        self.lbl_wa_status_icon.config(text="📱")
                        self.lbl_wa_status_title.config(text="Aguardando Leitura do QR Code", fg="#f39c12")
                        self.lbl_wa_status_desc.config(text="Escaneie o código abaixo com o WhatsApp do seu celular.")
                        self.btn_reset_qr.config(state="normal", text="🔄 Resetar Sessão & Gerar Novo QR Code")

                    self.root.after(0, lambda: atualizar_qr_ui(base64_str))
                    self._monitorar_leitura_qrcode()
                else:
                    def falha_qr():
                        self.lbl_qr_image.config(
                            image="",
                            text="⚠️ Não foi possível obter o QR Code da Evolution API.\nVerifique se o container está online.",
                            fg="#c0392b",
                            width=36,
                            height=11
                        )
                        self.lbl_qr_msg.config(text="Falha na obtenção do QR Code.", fg="#c0392b")
                        self.btn_reset_qr.config(state="normal", text="🔄 Resetar Sessão & Gerar Novo QR Code")
                        messagebox.showwarning("Aviso", "A Evolution API demorou para responder com o QR Code. Tente novamente em instantes.")

                    self.root.after(0, falha_qr)

            except Exception as e:
                logger.error(f"Erro no reset do WhatsApp: {e}")
                self.root.after(0, lambda: (
                    self.btn_reset_qr.config(state="normal", text="🔄 Resetar Sessão & Gerar Novo QR Code"),
                    messagebox.showerror("Erro no Reset", f"Falha ao se comunicar com a Evolution API:\n{e}")
                ))

        threading.Thread(target=tarefa, daemon=True).start()

    def _monitorar_leitura_qrcode(self):
        def monitor():
            url, key, inst = self.obter_credenciais_evolution()
            headers = {"apikey": key, "Content-Type": "application/json"}
            for _ in range(40):
                time.sleep(3)
                try:
                    r = requests.get(f"{url}/instance/connectionState/{inst}", headers=headers, timeout=5)
                    if r.status_code == 200:
                        state = r.json().get("instance", {}).get("state", "").lower()
                        if state == "open":
                            self.root.after(0, self.verificar_status_whatsapp)
                            self.root.after(0, lambda: messagebox.showinfo(
                                "WhatsApp Conectado!",
                                "Parabéns! O WhatsApp foi conectado com sucesso à Evolution API."
                            ))
                            break
                except Exception:
                    pass

        threading.Thread(target=monitor, daemon=True).start()

    def enviar_teste_whatsapp(self):
        phone = os.getenv("WHATSAPP_PHONE", "").strip()
        if not phone and hasattr(self, 'entry_wa_phone'):
            phone = self.entry_wa_phone.get().strip()

        if not phone:
            messagebox.showwarning("Aviso", "Nenhum número de WhatsApp configurado! Salve o número na aba 'E-mails & WhatsApp'.")
            return

        self.btn_teste_wa.config(state="disabled", text="⏳ Enviando...")

        def tarefa():
            try:
                from whatsapp_sender import send_whatsapp_message
                msg = (
                    "🤖 *Teste da Central de Automação de IA*\n\n"
                    "Olá! Sua conexão via Evolution API está *100% ativa e funcional*.\n"
                    "Os próximos boletins serão entregues diretamente por aqui!"
                )
                sucesso = send_whatsapp_message(msg)
                if sucesso:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Teste Enviado!", 
                        f"Mensagem de teste enviada com SUCESSO para o número {phone}!"
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Falha no Envio", 
                        "A Evolution API não conseguiu concluir o envio. Verifique se o número possui DDD válido e se a sessão está aberta."
                    ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao disparar mensagem de teste: {e}"))
            finally:
                self.root.after(0, lambda: self.btn_teste_wa.config(state="normal", text="✉️ Enviar Mensagem de Teste"))

        threading.Thread(target=tarefa, daemon=True).start()

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
                self.root.after(0, lambda: btn.config(state="normal", text=btn_label, fg="white"))
        
        btn.config(state="disabled", text="⏳ Gerando Boletim (aguarde cerca de 1 min)...", disabledforeground="white")
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