"""
modb.find_student_enrollments('jz1452896')
> [MoodleEnrollment(course_fullname='1121_創意學習_楊鎮華教師', roleid=5, user_id=26963, fullname='張金騏'), MoodleEnrollment(course_fullname='1122_智慧型網路服務工程_楊鎮華教師', roleid=5, user_id=26963, fullname='張金騏'), MoodleEnrollment(course_fullname='1122_程式設計-Python_黃鈺晴教師', roleid=5, user_id=26963, fullname='張金騏'), MoodleEnrollment(course_fullname='1112_程式設計-Python_黃鈺晴教師', roleid=4, user_id=26963, fullname='張金騏'), MoodleEnrollment(course_fullname='1131_程式設計-Python_黃鈺晴教師', roleid=4, user_id=26963, fullname='張金騏'), MoodleEnrollment(course_fullname='1132_程式設計-Python_黃鈺晴教師', roleid=4, user_id=26963, fullname='張金騏')]

modb.find_student_info('1132_程式設計-Python_黃鈺晴教師', '113409023')
> MoodleEnrollment(course_fullname=28672, roleid=5, user_id='113409023', fullname='柯鈞泰')
"""
# uv run -m pytest tests/infrastructure/test_postgresql_moodle_repository.py
from unittest.mock import patch, MagicMock

import pytest

# 匯入要被測試的類別和 DTO
from domain.moodle_enrollment import MoodleEnrollment
from infrastructure.postgresql_moodle_repository import PostgreSQLMoodleRepository

@pytest.fixture
def mock_conn_mgr():
    """提供一個被 mock 的 connection manager"""
    # 建立一個假的 cursor
    mock_cursor = MagicMock()
    
    # 建立一個假的 connection manager
    mock_manager = MagicMock()
    # 讓 manager 的 get_cursor() context manager 回傳假的 cursor
    mock_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
    
    # 回傳 manager 和 cursor，方便在測試中使用
    return mock_manager, mock_cursor

@patch('infrastructure.postgresql_moodle_repository.LazyMoodleConnectionManager')
def test_find_student_enrollments(MockLazyManager, mock_conn_mgr):
    """
    測試 find_student_enrollments 方法
    """
    # 1. 準備 (Arrange)
    mock_manager, mock_cursor = mock_conn_mgr
    # 讓 patch 過的 LazyMoodleConnectionManager 在建立時回傳我們的 mock_manager
    MockLazyManager.return_value = mock_manager

    # 準備假的資料庫回傳資料
    fake_db_rows = [
        ('Course A', 5, 101, '學生A'),
        ('Course B', 5, 101, '學生A')
    ]
    mock_cursor.fetchall.return_value = fake_db_rows

    # 建立 repository (此時其 self.conn_mgr 會是 mock_manager)
    repo = PostgreSQLMoodleRepository(db_config={}, ssh_config={})

    # 2. 執行 (Act)
    enrollments = repo.find_student_enrollments('student123')

    # 3. 驗證 (Assert)
    # 驗證 conn_mgr 的 get_cursor 是否被呼叫
    mock_manager.get_cursor.assert_called_once()
    
    # 驗證 SQL 和參數是否正確
    expected_sql = """
            SELECT
                cour.fullname,
                ra.roleid,
                usr.id,
                CONCAT(usr.lastname, usr.firstname)
            FROM mdl_user AS usr
            JOIN mdl_role_assignments AS ra ON ra.userid = usr.id
            JOIN mdl_context AS context ON context.id = ra.contextid
            JOIN mdl_course AS cour ON cour.id = context.instanceid
            WHERE (usr.username = %s OR usr.username LIKE %s);
            """
    mock_cursor.execute.assert_called_once_with(expected_sql, ('student123', 'student123@%'))

    # 驗證回傳的物件列表是否正確
    assert len(enrollments) == 2
    assert isinstance(enrollments[0], MoodleEnrollment)
    assert enrollments[0].course_fullname == 'Course A'
    assert enrollments[1].user_id == 101