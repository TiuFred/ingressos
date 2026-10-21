import logging
import time

from config import API_KEY, BOT_TOKEN, CHAT_ID, INTERVAL, NOTIFY_EXISTING
from database import connect, get_status, save_status
from telegram_notifier import send_message
from ticketmaster import find_events

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def run_once(conn):
    events = find_events(API_KEY)
    logging.info('Eventos encontrados: %d', len(events))
    for event in events:
        event_id = event['id']
        status = event.get('dates', {}).get('status', {}).get('code', 'unknown')
        previous = get_status(conn, event_id)
        if previous == status:
            continue
        if previous is not None or NOTIFY_EXISTING:
            date = event.get('dates', {}).get('start', {}).get('localDate', 'a confirmar')
            message = f'U2 Brasil — evento novo ou atualizado!\n{event.get("name", "U2")}\nData: {date}\nStatus: {status}\n{event.get("url", "Link indisponível")}'
            send_message(BOT_TOKEN, CHAT_ID, message)
        save_status(conn, event_id, status)

if __name__ == '__main__':
    conn = connect()
    logging.info('Monitor iniciado; intervalo: %ds', INTERVAL)
    while True:
        try:
            run_once(conn)
        except Exception:
            logging.exception('Falha na consulta ou notificação; tentando novamente depois')
        time.sleep(INTERVAL)
