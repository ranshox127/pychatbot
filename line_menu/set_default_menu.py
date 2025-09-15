import os

import requests
from dotenv import load_dotenv

load_dotenv(".env")

LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")
verification_rich_menu_id = "richmenu-79ae711ecc30ed02d208ea1382066ede"
verification_image_path = '/Users/jinq/Desktop/pychatbot/test_img/verification_test.png'

headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
           "Content-Type": 'application/json'}

response = requests.post(
    f'https://api.line.me/v2/bot/user/all/richmenu/{verification_rich_menu_id}',
    headers=headers
)

print(response.status_code)
print(response.text)
