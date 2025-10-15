import os
from dotenv import load_dotenv
from ngrok import forward

from cli import set_webhook


def on_starting(server):
    load_dotenv()
    TOKEN = os.getenv("PROD_LINE_TOKEN")

    port = int(os.environ.get("PORT", "8096"))
    token = os.environ.get("NGROK_AUTHTOKEN")
    server.log.info("starting ngrok on port %s", port)
    server.ngrok_listener = forward(port, authtoken=token)
    server.log.info("ngrok url: %s", server.ngrok_listener.url())

    set_webhook(
        token=TOKEN, endpoint=f"{server.ngrok_listener.url()}/linebot/linebot/")


def on_exit(server):
    try:
        server.ngrok_listener.close()
    except Exception:
        pass
