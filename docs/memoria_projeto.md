# Memória Técnica do Projeto - Automação de Notícias de IA

Este documento registra as correções, melhorias e planos de expansão realizados no sistema de busca e sumarização de notícias de IA.

## 🟢 Status Atual
- **Interface**: Corrigida e estabilizada.
- **Scraper (Fetcher)**: Corrigido (erro de sintaxe removido).
- **Sumarização**: Configurada para usar Gemini 2.5 Flash.
- **Configuração**: Usando `.env` para chaves sensíveis e `config.json` para preferências.

## 🛠️ Alterações Recentes (21/04/2026)

### 1. Correção de Erros de Subprocesso (`interface.py`)
- **Problema**: O sistema retornava `[WinError 2] O sistema não pode encontrar o arquivo especificado` ao tentar gerar o boletim.
- **Causa**: O script usava caminhos relativos e tentava chamar `powershell.exe` diretamente sem garantir que o diretório de trabalho (`cwd`) estava correto ou que os caminhos eram absolutos.
- **Solução**: 
    - Implementação de `BASE_DIR` absoluto.
    - Definição de `cwd=BASE_DIR` em todas as chamadas de `subprocess.run`.
    - Reformatação da chamada do PowerShell para ser mais robusta.

### 2. Correção de Erro de Sintaxe (`fetcher.py`)
- **Problema**: `main.py` retornava `exit status 1`.
- **Causa**: O arquivo `fetcher.py` tinha um bloco `finally` órfão no início, causando uma falha de carregamento do módulo.
- **Solução**: Remoção do código quebrado.

### 3. Melhoria na Robustez dos Caminhos
- Todos os arquivos agora utilizam caminhos baseados na localização do script (`__file__`), garantindo que o programa funcione mesmo se aberto por atalhos ou agendadores de tarefas (Windows Task Scheduler).

## 🚀 Próximos Passos: Integração com WhatsApp

### Plano: CallMeBot (Gratuito e Autônomo)
O objetivo é enviar o boletim formatado diretamente para o WhatsApp do usuário sem custo e sem precisar de infraestrutura complexa.

**Fluxo de Configuração:**
1. O usuário obtém a `APIKEY` enviando a mensagem `I allow callmebot to send me messages` para o bot atual (+34 684 72 39 62).
2. **Atualização da Interface**: Adicionados campos para "WhatsApp Number" e "CallMeBot API Key" na aba de configurações.
3. **Módulo de Envio**: Criado `whatsapp_sender.py`.
4. **Correção Erro 414 (22/04/2026)**: Implementado fatiamento de mensagens (chunks de 1500 caracteres) para evitar que o servidor do CallMeBot recuse boletins muito longos.

---
*Documento criado em 22/04/2026 às 01:21. Atualizado em 22/04/2026 às 22:14.*
