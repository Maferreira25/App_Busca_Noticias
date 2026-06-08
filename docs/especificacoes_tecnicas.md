# Especificações Técnicas - Central de Automação de Notícias de IA

## 1. Visão Geral
O sistema é um agente autônomo projetado para coletar, filtrar, sumarizar e disparar boletins informativos semanais sobre Inteligência Artificial Generativa. O foco é fornecer conteúdos curados de alta relevância para grupos de WhatsApp e listas de e-mail, de forma totalmente automatizada.

## 2. Arquitetura do Sistema
O projeto segue uma arquitetura modular em Python:

- **`interface.py`**: Painel de controle gráfico (Tkinter) para configuração de e-mails, filtros, WhatsApp, agendamento e acionamento manual. Agora inicializa a infraestrutura Docker automaticamente em background.
- **`main.py`**: Orquestrador principal que executa o fluxo de trabalho.
- **`fetcher.py`**: Motor de busca (Google News RSS).
- **`summarizer.py`**: Integração com a API do Google Gemini (2.5 Flash).
- **`storage.py`**: Módulo de persistência local na pasta `history/`.
- **`emailer.py`**: Módulo de comunicação (SMTP Gmail).
- **`whatsapp_sender.py`**: Controlador de integração que se comunica com a **Evolution API local (Docker)** para disparar as mensagens formatadas.
- **`reconectar_whatsapp.py`**: Script de contingência executável via interface para reiniciar a instância da Evolution API e renderizar QR Code no navegador para re-autenticação.

## 3. Tecnologias Utilizadas
- **Linguagem**: Python 3.x
- **Interface**: Tkinter (nativa)
- **Inteligência Artificial**: Google Gemini API (gemini-2.5-flash)
- **Infraestrutura WhatsApp**: Docker, Docker Compose e Evolution API (v1.8.2)
- **Automação de Agendamento**: Windows Task Scheduler

## 4. Funcionalidades Detalhadas

### 4.1 Coleta e Sumarização
- Varredura de notícias globais, nacionais e jurídicas via RSS.
- A IA constrói as narrativas e inclui links das referências, adaptando o formato ao padrão de leitura do WhatsApp.

### 4.2 Envio e Infraestrutura (WhatsApp)
- Execução local da **Evolution API**, blindando contra quedas de terceiros e APIs instáveis.
- Autostart de infraestrutura (o programa detecta se o Docker Desktop está fechado e o inicia silenciosamente).

### 4.3 Agendamento
- Prevenção de duplicidade nativa (o mesmo boletim não roda duas vezes no mesmo dia).
- Gerenciamento simplificado de tarefas pelo Windows Task Scheduler configurado pela UI.

## 5. Estrutura de Pastas
```text
Automação Busca Noticias de IA/
├── .venv/            # Ambiente virtual Python
├── docs/             # Documentação e especificações
├── history/          # Histórico de boletins gerados (.md)
├── scripts/          # scripts auxiliares
├── config.json       # Configurações de filtros e destinatários
├── docker-compose.yml# Infraestrutura da Evolution API
├── qrcode.html / png # Renderização transitória para conexão WhatsApp
├── .env              # Chaves de API e senhas (ignorado pelo Git)
├── interface.py      # Executável do Painel de Controle
├── reconectar_whatsapp.py # Rotina de reautenticação com WhatsApp
└── main.py           # Script de execução autônoma (Orquestrador)
```

## 6. Configuração de Variáveis (Exemplo de .env)
```env
GEMINI_API_KEY=sua_chave_aqui
EMAIL_ADDRESS=seu_email@gmail.com
EMAIL_APP_PASSWORD=sua_senha_de_app_google
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=42247710-6003-490b-936b-67a6d8d65451
EVOLUTION_INSTANCE=BoletimIA
WHATSAPP_PHONE=5511999999999
```

---
*Documento atualizado em 07/06/2026.*
