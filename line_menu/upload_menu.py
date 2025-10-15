import requests
import json
import os

from dotenv import load_dotenv

load_dotenv(".env")

LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")

verification_rich_menu_id = "richmenu-79ae711ecc30ed02d208ea1382066ede"
verification_image_path = '/Users/jinq/Desktop/pychatbot/test_img/verification_test.png'

headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
           "Content-Type": 'image/png'}

with open(verification_image_path, 'rb') as f:
    response = requests.post(
        f'https://api-data.line.me/v2/bot/richmenu/{verification_rich_menu_id}/content',
        headers=headers,
        data=f
    )

print(response.status_code)
print(response.text)

main_menu_rich_menu_id = "richmenu-37d8d3482f960040037939828214d388"
main_menu_image_path = '/Users/jinq/Desktop/pychatbot/test_img/main_menu_test.png'

with open(main_menu_image_path, 'rb') as f:
    response = requests.post(
        f'https://api-data.line.me/v2/bot/richmenu/{main_menu_rich_menu_id}/content',
        headers=headers,
        data=f
    )

print(response.status_code)
print(response.text)

# chapter_test_rich_menu_id = "richmenu-e6c1d65bd74ea8cbba40876bdef3d849"
# chapter_test_image_path = '/root/pychatbot/test_img/chapter_test.png'

# headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
#            "Content-Type": 'image/png'}

# with open(chapter_test_image_path, 'rb') as f:
#     response = requests.post(
#         f'https://api-data.line.me/v2/bot/richmenu/{chapter_test_rich_menu_id}/content',
#         headers=headers,
#         data=f
#     )

# print(response.status_code)
# print(response.text)
