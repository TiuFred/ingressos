
import json
import os
from pathlib import Path

import requests

# =====================================
# CONFIGURAÇÕES
# =====================================

API_KEY = os.environ["TICKETMASTER_API_KEY"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# IDs dos shows do U2 em São Paulo
EVENT_IDS = [
    "ZFIMVHtnMZ17a4r3",  # 10/03/2027
    "ZFIMVHtnMZ17a4rK",  # 12/03/2027
]

# Arquivo que armazena o último status
STATE_FILE = Path("state/events.json")

session = requests.Session()


# =====================================
# CONSULTAR TICKETMASTER
# =====================================

def fetch_event(event_id):
    url = (
        "https://app.ticketmaster.com/"
        f"discovery/v2/events/{event_id}.json"
    )

    response = session.get(
        url,
        params={"apikey": API_KEY},
        timeout=20,
    )

    response.raise_for_status()
    return response.json()



def get_event_state(event):
    from datetime import datetime, timezone

    dates = event.get("dates") or {}
    sales = event.get("sales") or {}
    public_sales = sales.get("public") or {}

    now = datetime.now(timezone.utc)
    presales = []

    for presale in sales.get("presales") or []:
        name = presale.get("name") or ""

        # Somente pré-vendas Santander
        if "santander" not in name.casefold():
            continue

        start = presale.get("startDateTime")
        end = presale.get("endDateTime")
        active = False

        if start and end:
            start_dt = datetime.fromisoformat(
                start.replace("Z", "+00:00")
            )
            end_dt = datetime.fromisoformat(
                end.replace("Z", "+00:00")
            )
            active = start_dt <= now < end_dt

        presales.append({
            "name": name,
            "start": start,
            "end": end,
            "active_window": active,
        })

    presales.sort(key=lambda p: (
        p["name"], p["start"] or ""
    ))

    return {
        "name": event.get("name"),
        "date": (dates.get("start") or {}).get("localDate"),
        "status": (dates.get("status") or {}).get("code"),
        "sales_start": public_sales.get("startDateTime"),
        "sales_end": public_sales.get("endDateTime"),
        "presales": presales,
        "url": event.get("url"),
    }


# =====================================
# ENVIAR ALERTA PELO TELEGRAM
# =====================================

def send_telegram(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    response = session.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=20,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError("Telegram recusou a mensagem")


# =====================================
# ARMAZENAR STATUS DOS EVENTOS
# =====================================

def load_state():
    if not STATE_FILE.exists():
        return {}

    return json.loads(
        STATE_FILE.read_text(encoding="utf-8")
    )


def save_state(state):
    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8",
    )


# =====================================
# MONITORAMENTO
# =====================================

def main():
    print("Iniciando monitoramento do U2...")

    old_state = load_state()
    new_state = old_state.copy()

    for event_id in EVENT_IDS:
        event = fetch_event(event_id)
        current = get_event_state(event)
        previous = old_state.get(event_id)

        print(
            f"Evento {event_id}: "
            f"{current['date']} - {current['status']}"
        )

        # Primeira execução: registra o estado
        if previous is None:
            print("Registrando estado inicial.")
            new_state[event_id] = current
            continue

        # Detecta alterações
        if current != previous:
            changes = []

            for key, value in current.items():
                if value != previous.get(key):
                    changes.append(
                        f"{key}: "
                        f"{previous.get(key)} -> {value}"
                    )

            message = (
                "🎸 U2 - ALTERAÇÃO DETECTADA!\n\n"
                f"Evento: {current['name']}\n"
                f"Data: {current['date']}\n\n"
                + "\n".join(changes)
                + f"\n\n{current['url']}"
            )

            send_telegram(message)

            print("Alerta enviado ao Telegram!")

        new_state[event_id] = current

    save_state(new_state)

    print("Monitoramento concluído!")


if __name__ == "__main__":
    main()
