# tests/conftest.py
import pytest
from config.settings import DevelopmentConfig
from dotenv import load_dotenv

load_dotenv(".env.test")  # 提前載入


@pytest.fixture(scope="session")
def test_config():
    return DevelopmentConfig()


pytest_plugins = [
    "tests.fixtures.mysql_fixtures",
    "tests.fixtures.postgresql_fixtures",
]
