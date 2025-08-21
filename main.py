import os

from dotenv import load_dotenv
from flask import Flask


from config.settings import CONFIG_BY_NAME
from containers import AppContainer
from interfaces.linebot_route import create_linebot_blueprint

DEV_PORT = 8095
PROD_PORT = 8096


def create_app():
    if os.getenv("FLASK_ENV", "production") != "production":
        load_dotenv()

    app = Flask(__name__)

    env = os.getenv("FLASK_ENV", "production")

    cfg_cls = CONFIG_BY_NAME[env]
    app.config.from_object(cfg_cls())

    container = AppContainer()
    container.config.from_dict(dict(app.config))

    # ✅ 先 wire（很重要：要在建立 blueprint 之前）
    container.wire(packages=["interfaces"])

    # 再建立並註冊 blueprint
    app.register_blueprint(create_linebot_blueprint(container))

    app.container = container
    return app
