import requests

def send_message(token, chat_id, message):
    response = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat_id, 'text': message, 'disable_web_page_preview': True}, timeout=20)
    response.raise_for_status()
    result = response.json()
    if not result.get('ok'):
        raise RuntimeError(f'Erro Telegram: {result.get("description", "desconhecido")}')
