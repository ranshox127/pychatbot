# config/settings.py
import os


class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-very-secret-key')


class DevelopmentConfig(BaseConfig):
    FLASK_DEBUG = True
    LINE_ACCESS_TOKEN = os.getenv("DEV_LINE_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("DEV_LINE_SECRET")
    DB_CONFIG = {...}
    SSH_CONFIG = {...}
    LINE_RICH_MENUS = {
        "main": "richmenu-xxxxxxxxxxxx",
        "register": "richmenu-yyyyyyyyyyyy"
    }


class ProductionConfig(BaseConfig):
    FLASK_DEBUG = False
    LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("PROD_LINE_SECRET")
    DB_CONFIG = {...}
    SSH_CONFIG = {...}
    LINE_RICH_MENUS = {
        "main": "richmenu-aaaaaaaaaaaa",
        "register": "richmenu-bbbbbbbbbbbb"
    }


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
