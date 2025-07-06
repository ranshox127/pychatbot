import requests
import os

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
verification_test_rich_menu_id = "richmenu-4667fcc9e76820a929220d8af84d3b2a"
verification_test_image_path = '/root/pychatbot/test_img/verification_test.png'

headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
           "Content-Type": 'application/json'}

response = requests.post(
    f'https://api.line.me/v2/bot/user/all/richmenu/{verification_test_rich_menu_id}',
    headers=headers
)

print(response.status_code)
print(response.text)
