# uv run -m pytest tests/infrastructure/test_mysql_student_repository.py
import pytest
from infrastructure.mysql_student_repository import MySQLStudentRepository
from domain.student import Student, RoleEnum, StudentStatus


@pytest.fixture
def repo(container, linebot_mysql_tx, monkeypatch):
    # 不讓共享連線被關掉
    monkeypatch.setattr(linebot_mysql_tx, "close", lambda: None)
    # repo 與 seed 共用同一條連線
    repo = MySQLStudentRepository(container.config.LINEBOT_DB_CONFIG())
    monkeypatch.setattr(repo, "_get_connection", lambda: linebot_mysql_tx)
    return repo


def student_obj():
    return Student(
        line_user_id="lineid",
        student_id="114514000",
        mdl_id="12345",
        name="旅歐文",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        role=RoleEnum.STUDENT,
        is_active=True,
        status=StudentStatus.REGISTERED,
    )


def test_find_by_line_id_returns_student(repo, linebot_mysql_tx, seed_student):
    seed_student(
        student_id="114514000",
        line_user_id="lineid",
        mdl_id="12345",
        name="旅歐文",
    )
    s = repo.find_by_line_id("lineid")
    assert s is not None
    assert s.student_id == "114514000"
    assert s.name == "旅歐文"
    assert s.role == RoleEnum.STUDENT
    assert s.is_active


def test_find_by_student_id_returns_student(repo, linebot_mysql_tx, seed_student):
    seed_student(
        student_id="114514000",
        line_user_id="lineid",
        mdl_id="12345",
        name="旅歐文",
    )
    s = repo.find_by_student_id("114514000")
    assert s is not None
    assert s.line_user_id == "lineid"
    assert s.name == "旅歐文"
    assert s.role == RoleEnum.STUDENT
    assert s.is_active


def test_find_by_student_id_returns_none_when_not_exists(repo, linebot_mysql_tx):
    s = repo.find_by_student_id("999999")
    assert s is None


def test_save_inserts_new_student(repo, linebot_mysql_tx, seed_course):
    # 先確保課程存在
    seed_course(context_title="1122_程式設計-Python_黃鈺晴教師")

    new_student = Student(
        line_user_id="lineid_new",
        student_id="1919810",
        mdl_id="88888",
        name="新學生",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        role=RoleEnum.STUDENT,
        is_active=True,
        status=StudentStatus.REGISTERED,
    )

    repo.save(new_student)

    found = repo.find_by_student_id("1919810")
    assert found is not None
    assert found.name == "新學生"
    assert found.line_user_id == "lineid_new"
