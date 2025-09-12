"""
其實這個單元測試沒啥意義，直接測連不連得到真實的資料庫，並拿資料對照才能看得出來對不對．

print(ojdb.get_exercise_number_by_contents_name('中央_1132', 'C2'))
> 3
print(ojdb.get_exercise_submission_by_contents_name('中央_1132', 'C2', '113409023', '2025-03-11 23:00'))
> 2

"""
# uv run -m pytest tests/infrastructure/test_postgresql_onlinejudge_repository.py
from unittest.mock import patch, MagicMock

import pytest

from infrastructure.postgresql_onlinejudge_repository import PostgreSQLOnlinejudgeRepository

pytestmark = pytest.mark.contract


@pytest.fixture
def repo():
    db_config = {'host': 'dummy', 'port': 5432, 'user': 'dummy',
                 'password': 'dummy', 'database': 'dummy'}
    ssh_config = {'ssh_host': 'dummy',
                  'ssh_username': 'dummy', 'ssh_password': 'dummy'}
    return PostgreSQLOnlinejudgeRepository(db_config, ssh_config)


@pytest.fixture
def mock_postgresql_connection():
    mock_tunnel = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (15,)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_tunnel, mock_conn, mock_cursor


@patch('infrastructure.postgresql_onlinejudge_repository.PostgreSQLOnlinejudgeRepository._get_connection')
def test_get_exercise_number_by_contents_name(mock_get_connection, mock_postgresql_connection, repo):
    mock_tunnel, mock_conn, mock_cursor = mock_postgresql_connection
    mock_get_connection.return_value = (mock_tunnel, mock_conn)

    result = repo.get_exercise_number_by_contents_name("MyContest", "Chapter1")

    assert result == 15
    mock_cursor.execute.assert_called_once()
    query, params = mock_cursor.execute.call_args[0]
    assert params == ("%Chapter1_E%", "%MyContest%Chapter1%Exercise%")


@patch('infrastructure.postgresql_onlinejudge_repository.PostgreSQLOnlinejudgeRepository._get_connection')
def test_get_advance_submission_by_contents_name_found(mock_get_connection, mock_postgresql_connection, repo):
    mock_tunnel, mock_conn, mock_cursor = mock_postgresql_connection
    mock_get_connection.return_value = (mock_tunnel, mock_conn)

    result = repo.get_advance_submission_by_contents_name(
        "MyContest", "Chapter2", "b12345678", "2025-08-03 23:59:59"
    )

    assert result == 15
    _, params = mock_cursor.execute.call_args[0]
    assert params[0] == "Chapter2_A%"
    assert params[1] == "2025-08-03 23:59:59"
    assert params[2] == "b12345678@%"
    assert params[3] == "b12345678"
