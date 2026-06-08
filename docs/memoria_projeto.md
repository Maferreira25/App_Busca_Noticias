# Memória Técnica do Projeto - Automação de Notícias de IA

Este documento registra as correções, melhorias e planos de expansão realizados no sistema de busca e sumarização de notícias de IA.

## 🟢 Status Atual
- **Interface**: Corrigida e estabilizada, com indicadores visuais de status em tempo real.
- **Scraper (Fetcher)**: Corrigido (erro de sintaxe removido).
- **Sumarização**: Configurada para usar Gemini 2.5 Flash.
- **Integração WhatsApp**: Migrada de CallMeBot para Evolution API local via Docker, com recurso de reconexão de 1 clique.
- **Configuração**: Usando `.env` para chaves sensíveis e `config.json` para preferências.

## 🛠️ Alterações Recentes (07/06/2026)

### 1. Migração para Evolution API (WhatsApp)
- **Problema**: O serviço anterior (CallMeBot) apresentou limitações e falta de flexibilidade.
- **Solução**: 
    - Transição da stack para utilizar a **Evolution API (v1.8.2)** hospedada localmente no Docker.
    - O módulo `whatsapp_sender.py` foi reescrito para enviar mensagens fatiadas usando o endpoint nativo com a `apikey` configurada no `.env`.

### 2. Reconexão e Autogeração de QR Code
- **Problema**: Se a sessão da API perder a conexão com o WhatsApp, recriar a instância demandava chamadas técnicas e manuais por linha de comando.
- **Solução**: 
    - Criação do script `reconectar_whatsapp.py` que limpa instâncias corrompidas e gera o `qrcode.png`/`qrcode.html` automaticamente.
    - Botão "Reconectar WhatsApp (Gerar QR Code)" integrado nativamente na `interface.py` para gerar a nova conexão em apenas um clique e abrir no navegador.

### 3. Autostart do Docker (Interface)
- **Melhoria**: A interface `interface.py` agora invoca uma thread de background (`iniciar_docker_background`) que valida e liga o Docker Desktop se estiver desligado e inicializa o `docker-compose`. Foi adicionado um indicador visual "Serviços (Docker/API): Online" para garantir ao usuário que o envio funcionará perfeitamente.

## 🛠️ Alterações Recentes (21/04/2026)

### 1. Correção de Erros de Subprocesso (`interface.py`)
- Implementação de `BASE_DIR` absoluto para resolver o erro `[WinError 2]`.

### 2. Correção de Erro de Sintaxe (`fetcher.py`)
- Remoção de bloco `finally` órfão no script de scrape.

### 3. Melhoria na Robustez dos Caminhos
- Caminhos baseados em `__file__` para suporte ao Windows Task Scheduler.

---
*Documento atualizado em 07/06/2026.*
