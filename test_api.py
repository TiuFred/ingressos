
import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

API_KEY = os.getenv("TICKETMASTER_API_KEY")

if not API_KEY:
    raise ValueError("API Key não encontrada no arquivo .env")

# Endpoint da Ticketmaster
url = "https://app.ticketmaster.com/discovery/v2/events.json"

params = {
    "apikey": API_KEY,
    "keyword": "U2",
    "countryCode": "BR",
    "size": 20
}

# Consulta a API
response = requests.get(url, params=params, timeout=15)

print("Status HTTP:", response.status_code)

response.raise_for_status()

# Converte a resposta para JSON
data = response.json()

# Extrai a lista de eventos
eventos = data.get("_embedded", {}).get("events", [])

if not eventos:
    print("Nenhum evento encontrado.")
else:
    print(f"\nEncontrados {len(eventos)} eventos:\n")

    for evento in eventos:
        print("Evento:", evento.get("name"))
        print("ID:", evento.get("id"))

        datas = evento.get("dates", {})
        print("Data:", datas.get("start", {}).get("localDate"))
        print("Status:", datas.get("status", {}).get("code"))

        vendas = evento.get("sales", {})
        publicas = vendas.get("public", {})

        print("Início das vendas:", publicas.get("startDateTime"))
        print("Fim das vendas:", publicas.get("endDateTime"))

        print("Link:", evento.get("url"))
        print("-" * 40)
