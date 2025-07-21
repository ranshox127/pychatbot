# config/settings.py
import os


class BaseConfig:
    pass


class DevelopmentConfig(BaseConfig):
    FLASK_DEBUG = True

    LINE_ACCESS_TOKEN = os.getenv("DEV_LINE_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("DEV_LINE_SECRET")

    LINEBOT_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("LINEBOT_DB_NAME")
    }

    VERIFY_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("VERIFY_DB_NAME")
    }

    REVIEW_SYSTEM_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("REVIEW_SYSTEM_DB_NAME")
    }

    MOODLE_DB_CONFIG = {
        "host": os.getenv("MOODLE_DB_HOST"),
        "database": os.getenv("MOODLE_DB_NAME"),
        "user": os.getenv("MOODLE_DB_USER"),
        "password": os.getenv("MOODLE_DB_PASSWORD"),
        "port": os.getenv("MOODLE_DB_PORT"),
    }

    MOODLE_SSH_CONFIG = {
        "ssh_host": os.getenv("MOODLE_SSH_HOST"),
        "ssh_username": os.getenv("MOODLE_SSH_USER"),
        "ssh_password": os.getenv("MOODLE_SSH_PASSWORD"),
        "ssh_port": int(os.getenv("MOODLE_SSH_PORT", 22)),  # 預設 SSH port
    }

    OJ_DB_CONFIG = {
        "host": os.getenv("OJ_DB_HOST"),
        "database": os.getenv("OJ_DB_NAME"),
        "user": os.getenv("OJ_DB_USER"),
        "password": os.getenv("OJ_DB_PASSWORD"),
        "port": os.getenv("OJ_DB_PORT")
    }

    OJ_SSH_CONFIG = {
        "ssh_host": os.getenv("OJ_SSH_HOST"),
        "ssh_username": os.getenv("OJ_SSH_USER"),
        "ssh_password": os.getenv("OJ_SSH_PASSWORD"),
        "ssh_port": int(os.getenv("OJ_SSH_PORT", 22)),  # 預設 SSH port
    }

    LINE_RICH_MENUS = {
        "main": "richmenu-2098cb2a534de65d2d1138b9210dbffe",
        "register": "richmenu-4667fcc9e76820a929220d8af84d3b2a"
    }


class ProductionConfig(BaseConfig):
    FLASK_DEBUG = False

    LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("PROD_LINE_SECRET")

    LINEBOT_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("LINEBOT_DB_NAME")
    }

    VERIFY_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("VERIFY_DB_NAME")
    }

    REVIEW_SYSTEM_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("REVIEW_SYSTEM_DB_NAME")
    }

    MOODLE_DB_CONFIG = {
        "host": os.getenv("MOODLE_DB_HOST"),
        "database": os.getenv("MOODLE_DB_NAME"),
        "user": os.getenv("MOODLE_DB_USER"),
        "password": os.getenv("MOODLE_DB_PASSWORD"),
        "port": os.getenv("MOODLE_DB_PORT"),
    }

    MOODLE_SSH_CONFIG = {
        "ssh_host": os.getenv("MOODLE_SSH_HOST"),
        "ssh_username": os.getenv("MOODLE_SSH_USER"),
        "ssh_password": os.getenv("MOODLE_SSH_PASSWORD"),
        "ssh_port": int(os.getenv("MOODLE_SSH_PORT", 22)),  # 預設 SSH port
    }

    OJ_DB_CONFIG = {
        "host": os.getenv("OJ_DB_HOST"),
        "database": os.getenv("OJ_DB_NAME"),
        "user": os.getenv("OJ_DB_USER"),
        "password": os.getenv("OJ_DB_PASSWORD"),
        "port": os.getenv("OJ_DB_PORT")
    }

    OJ_SSH_CONFIG = {
        "ssh_host": os.getenv("OJ_SSH_HOST"),
        "ssh_username": os.getenv("OJ_SSH_USER"),
        "ssh_password": os.getenv("OJ_SSH_PASSWORD"),
        "ssh_port": int(os.getenv("OJ_SSH_PORT", 22)),  # 預設 SSH port
    }

    LINE_RICH_MENUS = {
        "main": "richmenu-aaaaaaaaaaaa",
        "register": "richmenu-bbbbbbbbbbbb"
    }


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
