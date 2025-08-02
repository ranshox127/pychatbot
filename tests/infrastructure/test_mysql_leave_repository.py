# uv run -m pytest tests/infrastructure/test_mysql_leave_repository.py
from datetime import datetime
import pytest

from infrastructure.mysql_leave_repository import MySQLLeaveRepository
from domain.leave_request import LeaveRequest


@pytest.fixture
def repo(mysql_conn):
    return MySQLLeaveRepository(mysql_conn)


@pytest.fixture(autouse=True)
def clean_ask_for_leave(mysql_conn):
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ask_for_leave")
    mysql_conn.commit()


def test_save_leave_request_success(mysql_conn, repo):
    leave_request = LeaveRequest(
        operation_time=datetime.now(),
        student_id="114514",
        student_name="旅歐文",
        apply_time="2025-08-02",  # 留意 apply_time 應有格式一致性
        reason="身體不適",
        context_title="1122_程式設計-Python_黃鈺晴教師"
    )

    result = repo.save_leave_request(leave_request)
    assert result == "收到，已經幫你請好假了。"

    # 再查詢資料庫確認資料確實存在
    with mysql_conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM ask_for_leave WHERE student_ID = %s AND apply_time = %s",
            ("114514", "2025-08-02")
        )
        assert cur.fetchone() is not None


def test_save_leave_request_duplicate(mysql_conn, repo):
    # 先插入一筆相同資料
    with mysql_conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ask_for_leave (
                operation_time, student_ID, student_name, apply_time, reason, context_title
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "114514",
            "旅歐文",
            "2025-08-03",
            "身體不適",
            "1122_程式設計-Python_黃鈺晴教師"
        ))
        mysql_conn.commit()

    # 嘗試插入重複資料
    duplicate_request = LeaveRequest(
        operation_time=datetime.now(),
        student_id="114514",
        student_name="旅歐文",
        apply_time="2025-08-03",
        reason="身體不適",
        context_title="1122_程式設計-Python_黃鈺晴教師"
    )
    result = repo.save_leave_request(duplicate_request)
    assert result == "同學你已經請過假了喔。"


def test_save_leave_request_failure_with_no_existing(mysql_conn, repo, monkeypatch):
    # 模擬 INSERT 與 SELECT 都出錯，觸發未知錯誤訊息
    def fail_execute(*args, **kwargs):
        raise Exception("DB Failure")

    class BrokenCursor:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def execute(self, *args, **kwargs): raise Exception("DB failure")

    class BrokenConnection:
        def cursor(self): return BrokenCursor()

    broken_repo = MySQLLeaveRepository(BrokenConnection())

    leave_request = LeaveRequest(
        operation_time=datetime.now(),
        student_id="999999",
        student_name="測試生",
        apply_time="2025-08-04",
        reason="未知原因",
        context_title="測試課程"
    )

    result = broken_repo.save_leave_request(leave_request)
    assert result == "很抱歉，請假失敗。"
