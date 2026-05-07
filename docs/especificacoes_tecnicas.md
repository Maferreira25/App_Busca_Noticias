# Especificações Técnicas - Central de Automação de Notícias de IA

## 1. Visão Geral
O sistema é um agente autônomo projetado para coletar, filtrar, sumarizar e disparar boletins informativos semanais sobre Inteligência Artificial Generativa. O foco é fornecer conteúdos curados de alta relevância para grupos de WhatsApp e listas de e-mail, de forma totalmente automatizada.

## 2. Arquitetura do Sistema
O projeto segue uma arquitetura modular em Python:

- **`interface.py`**: Painel de controle gráfico (Tkinter) para configuração de e-mails, filtros de domínio, agendamento e execução manual.
- **`main.py`**: Orquestrador principal que executa o fluxo de trabalho (coleta -> resumo -> salvamento -> disparo).
- **`fetcher.py`**: Motor de busca e scraping que utiliza Google News RSS para encontrar notícias recentes em diferentes pautas (Geral, Jurídico e Internacional).
- **`summarizer.py`**: Integração com a API do Google Gemini (2.5 Flash) para transformar os metadados brutos das notícias em um texto narrativo e engajador formatado para WhatsApp.
- **`storage.py`**: Módulo de persistência local que organiza o histórico de boletins em formato Markdown na pasta `history/`.
- **`emailer.py`**: Módulo de comunicação que utiliza SMTP (Gmail) para enviar o relatório final.

## 3. Tecnologias Utilizadas
- **Linguagem**: Python 3.x
- **Interface**: Tkinter (nativa)
- **Inteligência Artificial**: Google Gemini API (gemini-2.5-flash)
- **Scraping/Coleta**: Feedparser (RSS)
- **Automação de Agendamento**: Windows Task Scheduler (via Powershell/schtasks)
- **Segurança**: Variáveis de ambiente (.env) para proteção de credenciais.

## 4. Funcionalidades Detalhadas

### 4.1 Coleta de Notícias (Fetcher)
- Varredura em 4 frentes: IA Generativa Geral (Brasil), Mundo da Tecnologia (Inglês), Impactos Jurídicos (Brasil) e Fronteira da IA (Canais oficiais como OpenAI e DeepMind).
- Sistema de filtragem por domínios ignorados (negativação de sites indesejados).

### 4.2 Inteligência e Sumarização (Summarizer)
- Uso de Engenharia de Prompt para garantir que a IA selecione ao menos 10 notícias.
- Expansão de conteúdo (3 a 5 linhas por notícia) para que o leitor não precise sair do WhatsApp.
- Inclusão automática de links de referência.

### 4.3 Agendamento
- Interface gráfica para configurar o Windows Task Scheduler.
- Execução semanal recorrente.
- Lógica de prevenção de duplicidade (verifica se um boletim já foi enviado na data atual antes de rodar).

## 5. Estrutura de Pastas
```text
Automação Busca Noticias de IA/
├── app/ api-client (em desenvolvimento)
├── .venv/            # Ambiente virtual Python
├── docs/             # Documentação e especificações
├── history/          # Histórico de boletins gerados (.md)
├── scripts/          # scripts auxiliares
├── config.json       # Configurações de filtros e destinatários
├── .env              # Chaves de API e senhas (ignorado pelo Git)
├── interface.py      # Executável do Painel de Controle
└── main.py           # Script de execução autônoma
```

## 6. Configuração de Variáveis (Exemplo de .env)
```env
GEMINI_API_KEY=sua_chave_aqui
EMAIL_ADDRESS=seu_email@gmail.com
EMAIL_APP_PASSWORD=sua_senha_de_app_google
```

---
*Documento atualizado em 22/04/2026.*
