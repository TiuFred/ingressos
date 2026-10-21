import requests

ENDPOINT = 'https://app.ticketmaster.com/discovery/v2/events.json'

def find_events(api_key):
    params = {'apikey': api_key, 'keyword': 'U2', 'countryCode': 'BR', 'size': 100, 'page': 0}
    response = requests.get(ENDPOINT, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    pages = payload.get('page', {}).get('totalPages', 0)
    if pages > 1:
        raise RuntimeError('Mais de 100 resultados: implemente paginação antes de continuar.')
    events = payload.get('_embedded', {}).get('events', [])
    return [e for e in events if any(a.get('name', '').casefold() == 'u2' for a in e.get('_embedded', {}).get('attractions', [])) or e.get('name', '').strip().casefold().startswith('u2 ')]
