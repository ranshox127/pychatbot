# config/settings.py
import os

class BaseConfig:
    DB_CONFIG = {...}

class DevelopmentConfig(BaseConfig):
    LINE_ACCESS_TOKEN = os.getenv("DEV_LINE_TOKEN")
    FLASK_DEBUG = True

class ProductionConfig(BaseConfig):
    LINE_ACCESS_TOKEN = os.getenv("PROD_LINE_TOKEN")

env = os.getenv("FLASK_ENV", "production")
if env == "development":
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)
