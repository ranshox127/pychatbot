from linebot.v3.messaging import ApiClient, MessagingApi, SetWebhookEndpointRequest, Configuration
import os
from dotenv import load_dotenv
from flask import Flask
import ngrok

from interface import register_blueprints

# 環境初始化
load_dotenv()
PORT = 8095

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

# 啟動 ngrok 並轉發
listener = ngrok.forward(PORT, authtoken=NGROK_AUTHTOKEN)
ngrok_url = listener.url()
print(f"🌐 臨時 Webhook URL: {ngrok_url}/callback")

# 設定 ngrok_url 給其他模組用
os.environ["NGROK_URL"] = ngrok_url

# 自動設定 LINE webhook URL

configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
with ApiClient(configuration) as api_client:
    line_bot_api = MessagingApi(api_client)
    line_bot_api.set_webhook_endpoint(SetWebhookEndpointRequest(
        endpoint=f"{ngrok_url}/linebot/"
    ))
    print("✅ 已自動設定 LINE Webhook URL")

# 啟動 Flask
app = Flask(__name__)
register_blueprints(app)

if __name__ == "__main__":
    app.run(port=PORT)
