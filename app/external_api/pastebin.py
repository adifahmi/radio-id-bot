import os

from dotenv import load_dotenv
from .base import api

load_dotenv()

HOST = lambda: 'https://pastebin.com/api/'
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cache-Control': 'no-cache',
}

pastebin_api = api(HOST, HEADERS)


def post_new_paste(text: str, filename: str, visibility: int = 1, expire: str = "1M"):
    payload = f'api_dev_key={os.getenv("PASTEBIN_TOKEN")}'
    payload += '&api_option=paste'
    payload += f'&api_paste_name={filename}'
    payload += f'&api_paste_private={str(visibility)}'
    payload += f'&api_paste_expire_date={expire}'
    payload += f'&api_paste_code={text}'
    payload = payload.encode('utf-8')
    result = pastebin_api('post', 'api_post.php', payload, False)
    return result
