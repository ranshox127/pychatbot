import os
import sys

import ngrok
from dotenv import load_dotenv
from flask import Flask
from linebot.v3.messaging import (ApiClient, Configuration, MessagingApi,
                                  SetWebhookEndpointRequest)

from config.settings import CONFIG_BY_NAME
from containers import AppContainer
from interfaces import linebot

PORT = 8095


def create_app():
    load_dotenv()

    app = Flask(__name__)

    env = os.getenv("FLASK_ENV", "production")
    app.config.from_object(CONFIG_BY_NAME[env])

    container = AppContainer()
    container.config.from_object(app.config)
    container.wire(modules=[sys.modules[__name__], "interfaces.linebot"])

    app.container = container
    app.register_blueprint(linebot.linebot_bp)

    return app


if __name__ == "__main__":
    # 啟動 Flask 應用
    app = create_app()

    # 啟動 ngrok
    NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
    listener = ngrok.forward(PORT, authtoken=NGROK_AUTHTOKEN)
    ngrok_url = listener.url()
    print(f"🌐 臨時 Webhook URL: {ngrok_url}/linebot/")

    # 讓其他模組也能透過 os.environ 使用這個 URL
    os.environ["NGROK_URL"] = ngrok_url

    # 自動設定 LINE Webhook
    LINE_ACCESS_TOKEN = app.config["LINE_ACCESS_TOKEN"]
    configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.set_webhook_endpoint(SetWebhookEndpointRequest(
            endpoint=f"{ngrok_url}/linebot/"
        ))
        print("✅ 已自動設定 LINE Webhook URL")

    app.run(port=PORT)
