import requests
import json
import os

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

# verification_test_rich_menu_id = "richmenu-4667fcc9e76820a929220d8af84d3b2a"
# verification_test_image_path = '/root/pychatbot/test_img/verification_test.png'

# headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
#            "Content-Type": 'image/png'}

# with open(verification_test_image_path, 'rb') as f:
#     response = requests.post(
#         f'https://api-data.line.me/v2/bot/richmenu/{verification_test_rich_menu_id}/content',
#         headers=headers,
#         data=f
#     )

# print(response.status_code)
# print(response.text)

# main_menu_test_rich_menu_id = "richmenu-2098cb2a534de65d2d1138b9210dbffe"
# main_menu_test_image_path = '/root/pychatbot/test_img/main_menu_test.png'

# headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
#            "Content-Type": 'image/png'}

# with open(main_menu_test_image_path, 'rb') as f:
#     response = requests.post(
#         f'https://api-data.line.me/v2/bot/richmenu/{main_menu_test_rich_menu_id}/content',
#         headers=headers,
#         data=f
#     )

# print(response.status_code)
# print(response.text)

chapter_test_rich_menu_id = "richmenu-e6c1d65bd74ea8cbba40876bdef3d849"
chapter_test_image_path = '/root/pychatbot/test_img/chapter_test.png'

headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
           "Content-Type": 'image/png'}

with open(chapter_test_image_path, 'rb') as f:
    response = requests.post(
        f'https://api-data.line.me/v2/bot/richmenu/{chapter_test_rich_menu_id}/content',
        headers=headers,
        data=f
    )

print(response.status_code)
print(response.text)
