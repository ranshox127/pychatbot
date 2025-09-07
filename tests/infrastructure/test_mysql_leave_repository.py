"""
記得測試前先塞對應的 account_info
FOREIGN KEY (`student_ID`,`context_title`)
"""
# uv run -m pytest tests/infrastructure/test_mysql_leave_repository.py
from datetime import datetime
import pytest

from infrastructure.mysql_leave_repository import MySQLLeaveRepository
from domain.leave_request import LeaveRequest

pytestmark = pytest.mark.infrastructure


@pytest.fixture
def repo(test_config):
    return MySQLLeaveRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean):
    yield


def test_save_leave_request_success(linebot_clean, infra_seed_student, repo):
    student_id = "114514"
    student_name = "旅歐文"
    apply_time = "2025-08-02"  # 留意 apply_time 應有格式一致性
    reason = "身體不適"
    context_title = "1122_程式設計-Python_黃鈺晴教師"

    infra_seed_student(student_id=student_id,
                       name=student_name,
                       context_title=context_title)

    leave_request = LeaveRequest(
        operation_time=datetime.now(),
        student_id=student_id,
        student_name=student_name,
        apply_time=apply_time,
        reason=reason,
        context_title=context_title
    )

    result = repo.save_leave_request(leave_request)

    assert result == "收到，已經幫你請好假了。"

    # 再查詢資料庫確認資料確實存在
    with linebot_clean.cursor() as cur:
        cur.execute(
            "SELECT * FROM ask_for_leave WHERE student_ID = %s AND apply_time = %s",
            (student_id, apply_time)
        )
        assert cur.fetchone() is not None


def test_save_leave_request_duplicate(infra_seed_leave, repo):
    student_id = "114514"
    student_name = "旅歐文"
    apply_time = "2025-08-02"
    reason = "身體不適"
    context_title = "1122_程式設計-Python_黃鈺晴教師"

    infra_seed_leave(operation_time=datetime.now(),
                     student_ID=student_id,
                     student_name=student_name,
                     apply_time=apply_time,
                     reason=reason,
                     context_title=context_title)

    # 嘗試插入重複資料
    duplicate_request = LeaveRequest(
        operation_time=datetime.now(),
        student_id=student_id,
        student_name=student_name,
        apply_time=apply_time,
        reason=reason,
        context_title=context_title
    )

    result = repo.save_leave_request(duplicate_request)

    assert result == "同學你已經請過假了喔。"


def test_save_leave_request_failure_with_no_existing(linebot_clean, repo):
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
