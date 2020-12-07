import os

from dotenv import load_dotenv
from .base import api

load_dotenv()

HOST = lambda: 'https://api.ksoft.si/'
HEADERS = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Authorization': f'Bearer {os.getenv("KSOFT_TOKEN")}'
}

ksoft_api = api(HOST, HEADERS)


def get_lyrics(query: str):
    result = ksoft_api('get', f'lyrics/search?q={query}&limit=1')
    return result
