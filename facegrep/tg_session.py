
from telethon.sync import TelegramClient
import asyncio
import os

# API ID and Hash

TELEGRAM_API_ID = os.environ.get('API_ID')
TELEGRAM_API_HASH = os.environ.get('API_HASH')

# Initialize the client
with TelegramClient('session_name', TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
    client.loop.run_until_complete(client.get_me())

