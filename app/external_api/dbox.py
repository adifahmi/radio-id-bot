import os

from dotenv import load_dotenv
from .base import api

load_dotenv()

HOST = lambda: 'https://api.dropboxapi.com/2/'
CONTENT_HOST = lambda: 'https://content.dropboxapi.com/2/'

BASE_HEADERS = {
    'Authorization': f'Bearer {os.getenv("DBOX_TOKEN")}',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/json',
}

dbox_api = api(HOST, BASE_HEADERS)


def upload_file(file, filename):
    headers = dict(BASE_HEADERS, **{
        'Content-Type': 'application/octet-stream',
        'Dropbox-API-Arg': f'{{"path": "/APIUpload/RadioID/{filename}","mode": "add","autorename": true,"mute": false,"strict_conflict": false}}'
    })
    payload = file

    dbox_api = api(CONTENT_HOST, headers)
    result = dbox_api('post', 'files/upload', payload, False)
    return result


def create_share_link(file_path):
    payload = f'{{"path": "{file_path}"}}'
    result = dbox_api('post', 'sharing/create_shared_link_with_settings', payload, False)
    return result


def get_link(file_id):
    payload = f'{{"path": "{file_id}"}}'
    result = dbox_api('post', 'sharing/list_shared_links', payload, False)
    return result
