import json
import os

import requests
from dotenv import load_dotenv

load_dotenv(".env")

LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")

verification_test_AliasId = "main_menu_test"
verification_test_richMenuId = 'richmenu-2098cb2a534de65d2d1138b9210dbffe'

chapter_test_AliasId = "chapter_test"
chapter_test_richMenuId = 'richmenu-e6c1d65bd74ea8cbba40876bdef3d849'

headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
           "Content-Type": 'application/json'}

# 建立 alias A
verification_test = {
    "richMenuAliasId": verification_test_AliasId,
    "richMenuId": verification_test_richMenuId
}

# response_a = requests.post(
#     'https://api.line.me/v2/bot/richmenu/alias',
#     headers=headers,
#     data=json.dumps(verification_test)
# )

# print("verification_test:", response_a.status_code, response_a.text)

# 建立 alias B
chapter_test = {
    "richMenuAliasId": chapter_test_AliasId,
    "richMenuId": chapter_test_richMenuId
}

# response_b = requests.post(
#     'https://api.line.me/v2/bot/richmenu/alias',
#     headers=headers,
#     data=json.dumps(chapter_test)
# )

# print("chapter_test:", response_b.status_code, response_b.text)


main_menu_AliasId = "main"
main_menu_richMenuId = 'richmenu-37d8d3482f960040037939828214d388'

main_menu = {
    "richMenuAliasId": main_menu_AliasId,
    "richMenuId": main_menu_richMenuId
}

response_main = requests.post(
    'https://api.line.me/v2/bot/richmenu/alias',
    headers=headers,
    data=json.dumps(main_menu)
)

print("response_main:", response_main.status_code, response_main.text)