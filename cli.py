import os

import ngrok
from dotenv import load_dotenv

from linebot.v3.messaging import (ApiClient, Configuration, MessagingApi,
                                  SetWebhookEndpointRequest)

from main import create_app

DEV_PORT = int(os.getenv("DEV_PORT", "8095"))


def set_webhook(token: str, endpoint: str):
    configuration = Configuration(access_token=token)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.set_webhook_endpoint(
            SetWebhookEndpointRequest(endpoint=endpoint))
        print(f"✅ 已自動設定 LINE Webhook URL 為 {endpoint}")


def dev():
    os.environ.setdefault("FLASK_ENV", "development")
    load_dotenv()

    app = create_app()

    # 可選：本機 E2E 才開 USE_REAL_LINE
    print(f"USE_REAL_LINE={app.config.get('USE_REAL_LINE')}")

    authtoken = os.getenv("NGROK_AUTHTOKEN")
    listener = ngrok.forward(DEV_PORT, authtoken=authtoken)
    url = listener.url()
    os.environ["NGROK_URL"] = url

    if app.config.get("USE_REAL_LINE"):
        token = app.config["LINE_ACCESS_TOKEN"]
        set_webhook(token, f"{url}/linebot/")

    app.run(port=DEV_PORT, debug=True)


if __name__ == "__main__":
    dev()
