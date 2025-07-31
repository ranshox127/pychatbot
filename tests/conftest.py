# tests/conftest.py
import pytest
from config.settings import DevelopmentConfig
from dotenv import load_dotenv

load_dotenv(".env.test")  # 提前載入

import os
print("[DEBUG-CONFIGTEST] CHATBOT_DB_HOST =", os.getenv("CHATBOT_DB_HOST"))
print("[DEBUG-CONFIGTEST] LINEBOT_DB_NAME =", os.getenv("LINEBOT_DB_NAME"))


@pytest.fixture(scope="session")
def test_config():
    return DevelopmentConfig()


pytest_plugins = [
    "tests.fixtures.mysql_fixtures",
    "tests.fixtures.postgresql_fixtures",
]
