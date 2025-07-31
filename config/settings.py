# config/settings.py
import os


class BaseConfig:
    pass


class DevelopmentConfig(BaseConfig):
    FLASK_DEBUG = True

    @property
    def LINE_ACCESS_TOKEN(self):
        return os.getenv("DEV_LINE_TOKEN")

    @property
    def LINE_CHANNEL_SECRET(self):
        return os.getenv("DEV_LINE_SECRET")

    @property
    def LINEBOT_DB_CONFIG(self):
        return {
            "host": os.getenv("CHATBOT_DB_HOST"),
            "user": os.getenv("CHATBOT_DB_USER"),
            "password": os.getenv("CHATBOT_DB_PASSWORD"),
            "db": os.getenv("LINEBOT_DB_NAME"),
            "port": int(os.getenv("CHATBOT_DB_PORT", 3306)),
        }

    @property
    def VERIFY_DB_CONFIG(self):
        return {
            "host": os.getenv("CHATBOT_DB_HOST"),
            "user": os.getenv("CHATBOT_DB_USER"),
            "password": os.getenv("CHATBOT_DB_PASSWORD"),
            "db": os.getenv("VERIFY_DB_NAME"),
            "port": int(os.getenv("CHATBOT_DB_PORT", 3306)),
        }

    @property
    def REVIEW_SYSTEM_DB_CONFIG(self):
        return {
            "host": os.getenv("CHATBOT_DB_HOST"),
            "user": os.getenv("CHATBOT_DB_USER"),
            "password": os.getenv("CHATBOT_DB_PASSWORD"),
            "db": os.getenv("REVIEW_SYSTEM_DB_NAME"),
            "port": int(os.getenv("CHATBOT_DB_PORT", 3306)),
        }

    @property
    def MOODLE_DB_CONFIG(self):
        return {
            "host": os.getenv("MOODLE_DB_HOST"),
            "database": os.getenv("MOODLE_DB_NAME"),
            "user": os.getenv("MOODLE_DB_USER"),
            "password": os.getenv("MOODLE_DB_PASSWORD"),
            "port": os.getenv("MOODLE_DB_PORT"),
        }

    @property
    def MOODLE_SSH_CONFIG(self):
        return {
            "ssh_host": os.getenv("MOODLE_SSH_HOST"),
            "ssh_username": os.getenv("MOODLE_SSH_USER"),
            "ssh_password": os.getenv("MOODLE_SSH_PASSWORD"),
            "ssh_port": int(os.getenv("MOODLE_SSH_PORT", 22)),
        }

    @property
    def OJ_DB_CONFIG(self):
        return {
            "host": os.getenv("OJ_DB_HOST"),
            "database": os.getenv("OJ_DB_NAME"),
            "user": os.getenv("OJ_DB_USER"),
            "password": os.getenv("OJ_DB_PASSWORD"),
            "port": os.getenv("OJ_DB_PORT"),
        }

    @property
    def OJ_SSH_CONFIG(self):
        return {
            "ssh_host": os.getenv("OJ_SSH_HOST"),
            "ssh_username": os.getenv("OJ_SSH_USER"),
            "ssh_password": os.getenv("OJ_SSH_PASSWORD"),
            "ssh_port": int(os.getenv("OJ_SSH_PORT", 22)),
        }

    LINE_RICH_MENUS = {
        "main": "richmenu-2098cb2a534de65d2d1138b9210dbffe",
        "register": "richmenu-4667fcc9e76820a929220d8af84d3b2a"
    }
    print("[DEBUG-SETTINGS] LINEBOT_DB_CONFIG =", LINEBOT_DB_CONFIG)


class ProductionConfig(BaseConfig):
    FLASK_DEBUG = False

    LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("PROD_LINE_SECRET")

    LINEBOT_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("LINEBOT_DB_NAME"),
        "port": int(os.getenv("CHATBOT_DB_PORT", 3306))
    }

    VERIFY_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("VERIFY_DB_NAME"),
        "port": int(os.getenv("CHATBOT_DB_PORT", 3306))
    }

    REVIEW_SYSTEM_DB_CONFIG = {
        "host": os.getenv("CHATBOT_DB_HOST"),
        "user": os.getenv("CHATBOT_DB_USER"),
        "password": os.getenv("CHATBOT_DB_PASSWORD"),
        "db": os.getenv("REVIEW_SYSTEM_DB_NAME"),
        "port": int(os.getenv("CHATBOT_DB_PORT", 3306))
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
