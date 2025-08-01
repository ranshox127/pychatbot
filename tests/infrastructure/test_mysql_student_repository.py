# uv run -m pytest tests/infrastructure/test_mysql_student_repository.py
import pytest
import pymysql
from infrastructure.mysql_student_repository import MySQLStudentRepository
from domain.student import Student, RoleEnum, StudentStatus


@pytest.fixture
def repo(test_config):
    return MySQLStudentRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture
def seed_student_data(mysql_conn):
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE account_info")
        cur.execute("TRUNCATE TABLE course_info")

        cur.execute("""
            INSERT INTO course_info(context_title, status, reserved)
            VALUES('1122_程式設計-Python_黃鈺晴教師', 'in_progress', '')
        """)
        cur.execute("""
            INSERT INTO account_info(student_ID, line_userID, mdl_ID, student_name, context_title, roleid, del)
            VALUES('114514000', 'lineid', 12345, '旅歐文', '1122_程式設計-Python_黃鈺晴教師', 5, 0)
        """)
    yield
    # ⬇️ 清除測試資料（Teardown）
    with mysql_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE account_info")
        cur.execute("TRUNCATE TABLE course_info")


def student():
    return Student(
        line_user_id="lineid",
        student_id="114514000",
        mdl_id="12345",
        name="旅歐文",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        role=RoleEnum.STUDENT,
        is_active=True,
        status=StudentStatus.REGISTERED
    )


def test_find_by_line_id_returns_student(repo, seed_student_data):
    s = repo.find_by_line_id("lineid")
    assert s is not None
    assert s.student_id == "114514000"
    assert s.name == "旅歐文"
    assert s.role == RoleEnum.STUDENT
    assert s.is_active


def test_find_by_student_id_returns_student(repo, seed_student_data):
    s = repo.find_by_student_id("114514000")
    assert s is not None
    assert s.line_user_id == "lineid"
    assert s.name == "旅歐文"
    assert s.role == RoleEnum.STUDENT
    assert s.is_active


def test_find_by_student_id_returns_none_when_not_exists(repo, seed_student_data):
    s = repo.find_by_student_id("999999")
    assert s is None


def test_save_inserts_new_student(repo, mysql_conn):
    new_student = Student(
        line_user_id="lineid_new",
        student_id="1919810",
        mdl_id="88888",
        name="新學生",
        context_title="1122_程式設計-Python_黃鈺晴教師",
        role=RoleEnum.STUDENT,
        is_active=True,
        status=StudentStatus.REGISTERED
    )
    # 插入對應課程
    with mysql_conn.cursor() as cur:
        cur.execute(
            "INSERT IGNORE INTO course_info(context_title, status, reserved) VALUES('1122_程式設計-Python_黃鈺晴教師', 'in_progress', '')")
    repo.save(new_student)

    # 查詢驗證
    found = repo.find_by_student_id("1919810")
    assert found is not None
    assert found.name == "新學生"
    assert found.line_user_id == "lineid_new"
