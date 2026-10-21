"""Monitor de eventos U2 com alertas verificáveis, via GitHub Actions.

A Discovery API NÃO confirma ingressos disponíveis por setor ou modalidade.
Opcionalmente, INVENTORY_FEED_URL pode apontar a um feed JSON autorizado
que informe disponibilidade real no esquema documentado abaixo.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import requests

API_KEY = os.environ['TICKETMASTER_API_KEY']
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
INVENTORY_FEED_URL = os.getenv('INVENTORY_FEED_URL', '').strip()
INVENTORY_FEED_TOKEN = os.getenv('INVENTORY_FEED_TOKEN', '').strip()
STATE_FILE = Path('state/events.json')

EVENTS = {'ZFIMVHtnMZ17a4r3': '10/03/2027', 'ZFIMVHtnMZ17a4rK': '12/03/2027'}
SECTORS = {'pista premium a', 'pista premium b', 'gold circle'}
SALE_TYPES = {'santander', 'venda_geral'}
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'U2TicketMonitor/2.0'


def send_telegram(message):
    r = SESSION.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                     json={'chat_id': CHAT_ID, 'text': message}, timeout=20)
    r.raise_for_status()
    if not r.json().get('ok'):
        raise RuntimeError('Telegram recusou mensagem')


def get_events(state):
    statuses = state.setdefault('_event_status', {})
    for event_id, date in EVENTS.items():
        r = SESSION.get(f'https://app.ticketmaster.com/discovery/v2/events/{event_id}.json',
                        params={'apikey': API_KEY}, timeout=20)
        r.raise_for_status()
        event = r.json()
        status = (event.get('dates', {}).get('status') or {}).get('code')
        previous = statuses.get(event_id)
        if previous and previous != status:
            send_telegram(f'🎸 U2 — MUDANÇA NO STATUS DE VENDA\n'
                          f'Data: {date}\n{previous} → {status}\n'
                          f'Isso NÃO confirma ingressos disponíveis nos setores procurados.\n'
                          f'https://www.ticketmaster.com.br/event/u2')
        statuses[event_id] = status
        print(f'{date}: status geral={status}')


def read_authorized_inventory():
    """Feed autorizado do operador, sem scraping de checkout ou bypass.

    Contrato esperado:
    {"offers": [{"event_id": "ZFIMVHtnMZ17a4r3",
                 "sale_type": "santander", "sector": "Gold Circle",
                 "full_available": 2, "half_available": 1,
                 "url": "https://www.ticketmaster.com.br/..."}]}
    Os números devem representar estoque efetivamente transacionável,
    não apenas o fato de que a venda está aberta.
    """
    if not INVENTORY_FEED_URL:
        print('Sem feed autorizado de estoque: não é possível confirmar reposição por setor.')
        return None
    headers = {'Authorization': f'Bearer {INVENTORY_FEED_TOKEN}'} if INVENTORY_FEED_TOKEN else {}
    r = SESSION.get(INVENTORY_FEED_URL, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get('offers'), list):
        raise ValueError('Feed de estoque inválido: esperado objeto com offers[]')
    return data['offers']


def check_inventory(state):
    offers = read_authorized_inventory()
    if offers is None:
        return
    last = state.setdefault('_confirmed_stock', {})
    totals = {}
    for offer in offers:
        event_id = str(offer.get('event_id', ''))
        sale = str(offer.get('sale_type', '')).strip().casefold()
        sector = str(offer.get('sector', '')).strip().casefold()
        if event_id not in EVENTS or sale not in SALE_TYPES or sector not in SECTORS:
            continue
        full = offer.get('full_available')
        half = offer.get('half_available')
        if type(full) is not int or type(half) is not int or full < 0 or half < 0:
            print('Oferta ignorada: quantidade não verificável')
            continue
        key = '|'.join((event_id, sale))
        aggregate = totals.setdefault(key, {'full': 0, 'half': 0, 'sectors': set()})
        aggregate['full'] += full
        aggregate['half'] += half
        if full or half:
            aggregate['sectors'].add(str(offer['sector']))
    # Contrato: offers[] é um snapshot completo, não somente mudanças.
    # Ao sumir a disponibilidade, o estado volta a false para uma futura reposição.
    for event_id, date in EVENTS.items():
        for sale in sorted(SALE_TYPES):
            key = '|'.join((event_id, sale))
            current = totals.get(key, {'full': 0, 'half': 0, 'sectors': set()})
            qualifies = current['full'] >= 2 and current['half'] >= 1
            if qualifies and last.get(key) is not True:
                send_telegram(
                    '🚨 U2 — ESTOQUE CONFIRMADO PELO FEED AUTORIZADO\n'
                    f'Show: {date}\nVenda: {sale}\n'
                    f'Setores: {", ".join(sorted(current["sectors"]))}\n'
                    f'Inteiras: {current["full"]} | Meias: {current["half"]}\n'
                    'Verifique imediatamente: https://www.ticketmaster.com.br/event/u2\n'
                    'Os ingressos podem esgotar antes da compra.'
                )
            last[key] = qualifies


def main():
    state = json.loads(STATE_FILE.read_text('utf-8')) if STATE_FILE.exists() else {}
    get_events(state)
    check_inventory(state)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print('Verificação finalizada:', datetime.now(timezone.utc).isoformat())


if __name__ == '__main__':
    main()
