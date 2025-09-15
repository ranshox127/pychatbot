# config/settings.py
import os


class BaseConfig:
    USE_REAL_LINE = "mock"
    
    @property
    def GRADER_BASE_URL(self) -> str:
        # 預設本機
        return os.getenv("GRADER_BASE_URL", "http://127.0.0.1:8097")

    @property
    def GRADER_API_KEY(self) -> str:
        return os.getenv("GRADER_API_KEY", "dev-162-key")
    
    @property
    def SUMMARY_OPENAI_KEY(self) -> str:
        return os.getenv("SUMMARY_API_KEY", "")


class DevelopmentConfig(BaseConfig):
    FLASK_DEBUG = True
    USE_REAL_LINE = "real"

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
    
    MISTAKE_REVIEW_SHEET_URL = os.getenv("MISTAKE_REVIEW_SHEET_URL")


class ProductionConfig(BaseConfig):
    FLASK_DEBUG = False
    USE_REAL_LINE = "real"

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
        "host": os.getenv("MOODLE_DB_HOST", "moodle-pg"),
        "database": os.getenv("MOODLE_DB_NAME", "moodle"),
        "user": os.getenv("MOODLE_DB_USER", "postgres"),
        "password": os.getenv("MOODLE_DB_PASSWORD", "postgres"),
        "port": os.getenv("MOODLE_DB_PORT", "5432"),
    }

    MOODLE_SSH_CONFIG = {
        "enabled": os.getenv("MOODLE_SSH_ENABLED", "false").lower() == "true",
        "ssh_host": os.getenv("MOODLE_SSH_HOST", ""),
        "ssh_username": os.getenv("MOODLE_SSH_USER", ""),
        "ssh_password": os.getenv("MOODLE_SSH_PASSWORD", ""),
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
        "main": os.getenv("MAIN_MENU_RICH_MENU_ID"),
        "register": os.getenv("VERIFICATION_MENU_RICH_MENU_ID")
    }
    
    MISTAKE_REVIEW_SHEET_URL = os.getenv("MISTAKE_REVIEW_SHEET_URL")
    
    @property
    def GRADER_BASE_URL(self) -> str:
        v = os.getenv("GRADER_BASE_URL")
        if not v:
            raise RuntimeError("GRADER_BASE_URL is required in production")
        return v

    @property
    def GRADER_API_KEY(self) -> str:
        v = os.getenv("GRADER_API_KEY")
        if not v:
            raise RuntimeError("GRADER_API_KEY is required in production")
        return v

# 【新增】為測試環境建立一個專屬的設定類別


class TestingConfig(DevelopmentConfig):
    """
    專為 Pytest 設計的測試環境設定。
    繼承自 DevelopmentConfig 來複用資料庫等設定，但覆寫關鍵值。
    """
    TESTING = True
    USE_REAL_LINE = "mock"

    # 【關鍵】直接覆寫 LINE_CHANNEL_SECRET 為一個固定的字串
    # 不再使用 @property 或 os.getenv，讓測試行為完全確定
    LINE_CHANNEL_SECRET = "this_is_a_fixed_test_secret"
    LINE_ACCESS_TOKEN = "this_is_a_fixed_test_access_token"


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,  # <-- 【新增】將 TestingConfig 加入字典
}
