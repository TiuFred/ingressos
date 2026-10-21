import hashlib
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path

import requests

API_KEY = os.environ['TICKETMASTER_API_KEY']
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
STATE_FILE = Path('state/events.json')

EVENT_IDS = ['ZFIMVHtnMZ17a4r3', 'ZFIMVHtnMZ17a4rK']
PAGES = {
    'santander': 'https://www.ticketmaster.com.br/event/pv-santander-u2',
    'venda_geral': 'https://www.ticketmaster.com.br/event/vg-u2',
}

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'U2AvailabilityWatcher/1.0 (+status checking)'})

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def notify(message):
    response = SESSION.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        json={'chat_id': CHAT_ID, 'text': message}, timeout=20)
    response.raise_for_status()
    if not response.json().get('ok'):
        raise RuntimeError('Telegram recusou a mensagem')


def event_state(event):
    dates = event.get('dates') or {}
    sales = event.get('sales') or {}
    public = sales.get('public') or {}
    presales = []
    for p in sales.get('presales') or []:
        name = p.get('name') or ''
        if 'santander' in name.casefold():
            presales.append({
                'name': name,
                'start': p.get('startDateTime'),
                'end': p.get('endDateTime'),
            })
    presales.sort(key=lambda p: (p['name'], p['start'] or ''))
    return {
        'name': event.get('name'),
        'date': (dates.get('start') or {}).get('localDate'),
        'status': (dates.get('status') or {}).get('code'),
        'sales_start': public.get('startDateTime'),
        'sales_end': public.get('endDateTime'),
        'presales': presales,
        'url': event.get('url'),
    }


def check_events(state):
    for event_id in EVENT_IDS:
        resp = SESSION.get(
            f'https://app.ticketmaster.com/discovery/v2/events/{event_id}.json',
            params={'apikey': API_KEY}, timeout=20)
        resp.raise_for_status()
        current = event_state(resp.json())
        previous = state.get(event_id)
        if previous is not None and current != previous:
            changes = [
                f'{key}: {previous.get(key)} -> {value}'
                for key, value in current.items()
                if previous.get(key) != value
            ]
            notify('🎸 U2: MUDANÇA NOS DADOS DE VENDA (NÃO CONFIRMA ESTOQUE)\n'
                   + f"Show: {current['date']}\n" + '\n'.join(changes)
                   + '\n' + (current['url'] or ''))
        state[event_id] = current
        print(f"Evento {current['date']}: {current['status']}")


def check_pages(state):
    page_state = state.setdefault('_pages', {})
    for label, url in PAGES.items():
        try:
            response = SESSION.get(url, timeout=20)
            response.raise_for_status()
            parser = VisibleText()
            parser.feed(response.text)
            text = re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()
            if len(text) < 250:
                print(f'Página {label}: conteúdo insuficiente para comparar')
                continue
            # Remove sequências voláteis comuns, mas alterações de layout ainda podem alertar.
            normalized = re.sub(r'\s+', ' ', text)
            fingerprint = hashlib.sha256(normalized.encode()).hexdigest()
            previous = page_state.get(label)
            if previous is not None and previous != fingerprint:
                notify(f'🔎 U2: A PÁGINA OFICIAL FOI ALTERADA\n'
                       f'Modalidade: {label.replace("_", " ").title()}\n'
                       'Verifique manualmente setores e ingressos. '
                       'Mudança na página NÃO confirma estoque.\n'
                       f'{url}')
            page_state[label] = fingerprint
            print(f'Página {label}: verificada')
        except (requests.RequestException, ValueError) as exc:
            print(f'Página {label}: não foi possível verificar ({type(exc).__name__})')


def main():
    state = json.loads(STATE_FILE.read_text(encoding='utf-8')) if STATE_FILE.exists() else {}
    check_events(state)
    check_pages(state)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Verificação concluída.')


if __name__ == '__main__':
    main()
