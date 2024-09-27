import asyncio
import hashlib
import tempfile

from telethon import TelegramClient, events, tl
from telethon.client.telegramclient import TelegramClient
from telethon.sessions import StringSession
from rich import print
import settings


async def hash_telegram_file(telegram_client: TelegramClient, file: tl.custom.file.File):
    md5 = hashlib.md5()
    async for bytes in telegram_client.iter_download(file.media):
        md5.update(bytes)
    return md5.hexdigest()

def make_session_string():
    with TelegramClient(StringSession(), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH) as client:
        print(client.session.save())

async def main():

    authorization = StringSession(settings.TELEGRAM_SESSION_STRING)
    telegram_client = TelegramClient(authorization, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await telegram_client.start()

    async for dialog in telegram_client.iter_dialogs():
        messages = telegram_client.iter_messages(dialog.id, limit=2)
        async for message in messages:
            file_record = dict()
            if attachment := message.file:
                file_hash = await hash_telegram_file(telegram_client, attachment)
                print(file_hash)
                file_record["file_hash"] = file_hash

if __name__ == "__main__":
    asyncio.run(main())