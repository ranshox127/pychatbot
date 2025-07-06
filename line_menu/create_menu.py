import requests
import json
import os
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
           "Content-Type": "application/json"}

# body = {
#     "size": {"width": 1200, "height": 810},
#     "selected": "true",
#     "name": "verification_test",
#     "chatBarText": "驗證身分",
#     "areas": [
#         {
#             "bounds": {"x": 0, "y": 0, "width": 1, "height": 1},
#             "action": {"type": "postback", "data": "noop"}
#         }
#     ]
# }

# body = {
#     "size": {"width": 1200, "height": 810},
#     "selected": True,
#     "name": "main_menu_test",
#     "chatBarText": "主要選單",
#     "areas": [
#         {
#             "bounds": {"x": 0, "y": 0, "width": 600, "height": 405},
#             "action": {'type': 'richmenuswitch', 'richMenuAliasId': 'chapter_test', 'data': 'change-to-chapter_test'}
#         },
#         {
#             "bounds": {"x": 600, "y": 0, "width": 600, "height": 405},
#             "action": {"type": "postback", "data": "fetch_absence_info"}
#         },
#         {
#             "bounds": {"x": 0, "y": 405, "width": 600, "height": 405},
#             "action": {"type": "postback", "data": "apply_leave"}
#         },
#         {
#             "bounds": {"x": 600, "y": 405, "width": 600, "height": 405},
#             "action": {"type": "message", "text": "我有問題"}
#         }
#     ]
# }

body = {
    "size": {"width": 1200, "height": 810},
    "selected": True,
    "name": "chapter_test",
    "chatBarText": "選擇單元",
    "areas": [
        # C1 ~ C8
        *[
            {
                "bounds": {
                    "x": (i % 4) * 250,
                    "y": (i // 4) * 405,
                    "width": 250,
                    "height": 405
                },
                "action": {
                    "type": "postback",
                    "data": f"C{i+1}"
                }
            } for i in range(8)
        ],
        # Back 按鈕
        {
            "bounds": {
                "x": 1000,
                "y": 0,
                "width": 200,
                "height": 810
            },
            "action": {
                "type": "richmenuswitch",
                "richMenuAliasId": "main_menu_test",
                "data": "change-to-main_menu_test"
            }
        }
    ]
}

req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
                       headers=headers, data=json.dumps(body).encode('utf-8'))

print(req.text)
# verification_test: {"richMenuId":"richmenu-4667fcc9e76820a929220d8af84d3b2a"}
# main_menu_test: {"richMenuId":"richmenu-2098cb2a534de65d2d1138b9210dbffe"}
# chapter_test: {"richMenuId":"richmenu-e6c1d65bd74ea8cbba40876bdef3d849"}