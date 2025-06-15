import pandas as pd
import requests
import os

# Assume these values are now being loaded from a .env file
DEFAULT_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEFAULT_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(bot_message, production_mode=False, chat_group=None, bot_token=None):
    
    effective_bot_token = bot_token
    if effective_bot_token is None:
        effective_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', DEFAULT_BOT_TOKEN)

    chat_ids = {
        'player-markets': '-1001668549483'
    }
   
    effective_bot_chat_id = None 
    if chat_group is not None:
        effective_bot_chat_id = chat_ids.get(chat_group) if production_mode else DEFAULT_CHAT_ID
        if production_mode and chat_ids.get(chat_group) is None:
            print(f"Warning: chat_group '{chat_group}' not found in chat_ids. Falling back to default chat_id for non-production if applicable, or potentially None.")

    else:
        # If no chat_group, use TELEGRAM_CHAT_ID from env, or fallback to DEFAULT_CHAT_ID
        effective_bot_chat_id = os.getenv('TELEGRAM_CHAT_ID', DEFAULT_CHAT_ID)

    if not effective_bot_token or not effective_bot_chat_id:
        print(f"Telegram fallback: BOT_TOKEN or CHAT_ID is missing or invalid.")
        print(f"Intended message: {bot_message}")
        return

    send_text = (f'https://api.telegram.org/bot{effective_bot_token}'
                 f'/sendMessage?chat_id={effective_bot_chat_id}'
                 f'&parse_mode=Markdown&disable_web_page_preview=true&text={bot_message}')
    try:
        response = requests.get(send_text)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"{bot_message}")


def get_telegram_messages(bot_token=None):
    effective_bot_token = bot_token
    if effective_bot_token is None:
        effective_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', DEFAULT_BOT_TOKEN)
    return requests.get(f'https://api.telegram.org/bot{effective_bot_token}/getUpdates').content
