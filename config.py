import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ['TICKETMASTER_API_KEY']
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
INTERVAL = max(300, int(os.getenv('CHECK_INTERVAL_SECONDS', '900')))
NOTIFY_EXISTING = os.getenv('NOTIFY_EXISTING_ON_START', 'false').lower() == 'true'
