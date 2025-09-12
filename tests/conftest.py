# tests/conftest.py
import os

import pytest
from dotenv import load_dotenv

from main import create_app

# 建議使用 APP_ENV，並保留 FLASK_ENV 相容
os.environ.setdefault("APP_ENV", "testing")
os.environ["FLASK_ENV"] = "testing"

# 測試 DB/密鑰來自 .env.test
load_dotenv(".env.test")


@pytest.fixture
def app():
    """為每次測試建立並配置一個新的 app 實例。"""
    app = create_app()
    # 若要在測試時覆寫設定，可在這裡 update：
    # app.config.update({"SOME_FLAG": True})
    yield app


@pytest.fixture
def client(app):
    """app 的測試 client。"""
    return app.test_client()


@pytest.fixture
def container(app):
    """應用程式的依賴注入 container。"""
    return app.container


pytest_plugins = [
    "tests.fixtures.mysql_fixtures",
    "tests.fixtures.db_truncate",
    "tests.fixtures.seeder_wrapper",
    "tests.fixtures.spies",
    "tests.fixtures.live_server"
]
