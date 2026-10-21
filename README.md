# U2 Ticket Monitor (MVP)

Monitora eventos do U2 no Brasil usando a Ticketmaster Discovery API e notifica no Telegram sobre eventos novos ou mudança de status. **Não verifica estoque de ingressos nem garante cobertura da Ticketmaster Brasil.**

## Configuração

1. Instale Python 3.11+ e crie um ambiente virtual: `python -m venv .venv`.
2. Ative o ambiente virtual (`source .venv/bin/activate` no Linux/macOS ou `.venv\\Scripts\\activate` no Windows).
3. Instale dependências: `pip install -r requirements.txt`.
4. Copie `.env.example` para `.env` e preencha as credenciais.
5. Crie um bot com `@BotFather`, envie `/start` ao bot e obtenha seu chat_id com `https://api.telegram.org/bot<TOKEN>/getUpdates` (não compartilhe token).
6. Obtenha a API key em https://developer.ticketmaster.com/.
7. Execute `python main.py`.

Por padrão, eventos encontrados na primeira execução são registrados sem notificação; altere `NOTIFY_EXISTING_ON_START=true` para receber alertas iniciais. O intervalo mínimo é de 300 segundos.

Observações: a busca usa palavra-chave e filtra resultados para reduzir falsos positivos; alguns eventos podem não ser retornados. Sem resultados não significa ausência de show. Não há scraping, bypass de CAPTCHA nem compra automática.
