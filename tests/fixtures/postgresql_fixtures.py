# tests/fixtures/postgresql_fixtures.py
import pytest, psycopg2
from sshtunnel import SSHTunnelForwarder

@pytest.fixture
def pg_conn(test_config):
    tunnel = SSHTunnelForwarder(
        (test_config.OJ_SSH_CONFIG["ssh_host"], test_config.OJ_SSH_CONFIG["ssh_port"]),
        ssh_username=test_config.OJ_SSH_CONFIG["ssh_username"],
        ssh_password=test_config.OJ_SSH_CONFIG["ssh_password"],
        remote_bind_address=(test_config.OJ_DB_CONFIG["host"], test_config.OJ_DB_CONFIG["port"])
    )
    tunnel.start()
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=tunnel.local_bind_port,
        user=test_config.OJ_DB_CONFIG["user"],
        password=test_config.OJ_DB_CONFIG["password"],
        database=test_config.OJ_DB_CONFIG["database"]
    )
    yield conn
    conn.close()
    tunnel.close()
