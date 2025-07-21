import os
import sys

import ngrok
from dotenv import load_dotenv
from flask import Flask
from linebot.v3.messaging import (ApiClient, Configuration, MessagingApi,
                                  SetWebhookEndpointRequest)

from config.settings import CONFIG_BY_NAME
from containers import AppContainer
from interfaces.linebot import create_linebot_blueprint

DEV_PORT = 8095
PROD_PORT = 8096


def create_app():
    if os.getenv("FLASK_ENV", "production") != "production":
        load_dotenv()

    app = Flask(__name__)

    env = os.getenv("FLASK_ENV", "production")
    app.config.from_object(CONFIG_BY_NAME[env])

    container = AppContainer()
    container.config.from_object(app.config)

    linebot_blueprint = create_linebot_blueprint()

    container.wire(modules=[sys.modules[__name__], "interfaces.linebot"])

    app.register_blueprint(linebot_blueprint)

    app.container = container

    return app


def set_webhook(token: str, endpoint: str):
    configuration = Configuration(access_token=token)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.set_webhook_endpoint(
            SetWebhookEndpointRequest(endpoint=endpoint))
        print(f"✅ 已自動設定 LINE Webhook URL 為 {endpoint}")


if __name__ == "__main__":
    # FLASK_ENV=production python main.py

    # 啟動 Flask 應用
    app = create_app()

    if app.config.get("FLASK_DEBUG"):

        NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
        listener = ngrok.forward(DEV_PORT, authtoken=NGROK_AUTHTOKEN)
        ngrok_url = listener.url()

        # 讓其他模組也能透過 os.environ 使用這個 URL
        os.environ["NGROK_URL"] = ngrok_url

        # 自動設定 LINE Webhook
        DEV_LINE_TOKEN = app.config["DEV_LINE_TOKEN"]

        set_webhook(token=DEV_LINE_TOKEN, endpoint=f"{ngrok_url}/linebot/")

        app.run(port=DEV_PORT)

    else:
        # Production 模式 (由 Gunicorn 啟動)
        print("🌍 正在啟動 Production 模式...")
        print("   建議使用 Gunicorn 搭配 Nginx，不直接用 Flask 啟動")

        PROD_LINE_TOKEN = app.config["PROD_LINE_TOKEN"]

        set_webhook(token=PROD_LINE_TOKEN, endpoint=os.getenv("WEBHOOK_URL"))

        app.run(host="0.0.0.0", port=PROD_PORT, ssl_context=(
            '/etc/letsencrypt/live/chatbot.moocs.tw/fullchain.pem', '/etc/letsencrypt/live/chatbot.moocs.tw/privkey.pem'))
