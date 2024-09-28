
from telethon import TelegramClient, events, errors
from pprint import pprint
import asyncio
import csv
import os
import pandas as pd
from telethon.tl.types import MessageMediaPhoto
import re
import tg_session



# API ID and Hash

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

# Initialize the client
client = TelegramClient('session_name', API_ID, API_HASH)

messages_info = []

def extract_message_id_from_url(url):
    # https://t.me/channel_name/message_id

    pattern = r"https://t\.me/[^/]+/(\d+)"
    match = re.search(pattern, url)
    if match:
        return int(match.group(1)) 
    else:
        return None

async def fetch_grouped_messages(channel_name, message_url):
    async with client:
        # Start the client
        await client.start()

        # Get the channel entity
        channel = await client.get_entity(channel_name)
        print("Channel:", channel)

        # Extract the message ID from the input URL
        message_id = extract_message_id_from_url(message_url)

        if message_id:
            print(f"Fetching message with ID: {message_id}")
            message = await client.get_messages(channel, ids=message_id)

            if message:
                # Get the grouped_id of the message
                grouped_id = message.grouped_id
                original_message_text = message.message  # Store the original message text
                if grouped_id:
                    print(f"Fetching all messages with grouped_id: {grouped_id}")
                    # Fetch a batch of recent messages and filter for the same grouped_id
                    recent_messages = await client.get_messages(channel, limit=100)  # Adjust limit if needed
                    grouped_messages = [msg for msg in recent_messages if msg.grouped_id == grouped_id]

                    if grouped_messages:
                        # Process each message in the grouped set
                        for msg in grouped_messages:
                            await process_message(msg, channel_name, msg.id, grouped_id, original_message_text)
                    else:
                        print(f"No messages found with grouped_id: {grouped_id}")
                else:
                    # If there's no grouped_id, process the single message
                    print(f"No grouped_id found. Processing message with ID: {message_id}")
                    #await process_message(message, channel_name, message_id, grouped_id=None, message.message)
                    await process_message(message, channel_name, message_id, None, message.message)

                # Save the data to a CSV after processing
                df = pd.DataFrame(messages_info)
                df.to_csv(f'messages_all_{channel_name}_{grouped_id or "none"}.csv', index=False)
            else:
                print(f"Message with ID {message_id} not found.")
        else:
            print("Invalid message URL. Could not extract message_id.")
        
        # Disconnect the client after operation
        await client.disconnect()

async def process_message(message, channel_name, message_id, grouped_id, original_message_text):
    try:
        # Check if the message contains a photo
        if isinstance(message.media, MessageMediaPhoto):
            print(f"Downloading photo from message with ID: {message_id}")
            # Download the photo and save it using the message_id as the file name
            await client.download_media(message.media, f'{PHOTO_SAVE_PATH}/{message_id}.jpg')
            print(f"Photo downloaded for message ID {message_id}")
        else:
            print(f"No photo found in message with ID {message_id}")
        
        # Add message information to the list for CSV
        my_dict = {
            "channel_name": channel_name,
            "grouped_id": grouped_id,
            "message_id": message_id, 
            "date": message.date,
            "url": f"https://t.me/{channel_name}/{message_id}",
            "message": original_message_text
        }
        messages_info.append(my_dict)

    except Exception as e:
        print(f"Error processing message {message_id}: {str(e)}")


# Example usage
# Specify the channel name and message URL
channel_name = "NowMelitopol"  # Replace with your specific channel name
message_url = "https://t.me/NowMelitopol/26464"  # Replace with your message URL

# Run the fetch_grouped_messages function to download all photos for the grouped message
await fetch_grouped_messages(channel_name, message_url)
