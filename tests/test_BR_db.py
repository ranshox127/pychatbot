import pytest
from unittest.mock import patch, MagicMock
from databases.BR_db import BR_Database

@pytest.fixture
def db_instance():
    db = BR_Database()
    # 模擬初始化的連線資料
    db.ssh_host = 'dummy_ssh'
    db.ssh_pw = 'dummy_pw'
    db.sql_password = 'dummy_sql_pw'
    return db

@patch("databases.BR_db.SSHTunnelForwarder")
@patch("databases.BR_db.pymysql.connect")
def test_get_student_summary(mock_connect, mock_tunnel, db_instance):
    # 模擬 SSH tunnel
    mock_tunnel.return_value.__enter__.return_value = mock_tunnel
    mock_tunnel.return_value.local_bind_port = 3306

    # 模擬 DB cursor 行為
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("總結", "這是memo文字;:::nl:::;第二行")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    result = db_instance.get_student_summary("student1", "課程A", "章節B")
    expected = "這是memo文字\n第二行"
    assert result == expected
