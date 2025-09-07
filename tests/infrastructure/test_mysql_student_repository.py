# uv run -m pytest tests/infrastructure/test_mysql_student_repository.py
import pytest
from infrastructure.mysql_student_repository import MySQLStudentRepository
from domain.student import RoleEnum

pytestmark = pytest.mark.infrastructure


@pytest.fixture
def repo(test_config):
    return MySQLStudentRepository(test_config.LINEBOT_DB_CONFIG)


@pytest.fixture(autouse=True)
def clean_dbs(linebot_clean):
    yield


def test_find_by_line_id_returns_student(repo, infra_seed_student):
    infra_seed_student(
        student_id="114514000",
        user_id="lineid",
        mdl_id="12345",
        name="旅歐文",
    )
    s = repo.find_by_line_id("lineid")
    assert s is not None
    assert s.student_id == "114514000"
    assert s.name == "旅歐文"
    assert s.role == RoleEnum.STUDENT
    assert s.is_active


def test_find_by_student_id_returns_student(repo, infra_seed_student):
    infra_seed_student(
        student_id="114514000",
        user_id="lineid",
        mdl_id="12345",
        name="旅歐文",
    )
    s = repo.find_by_student_id("114514000")
    assert s is not None
    assert s.line_user_id == "lineid"
    assert s.name == "旅歐文"
    assert s.role == RoleEnum.STUDENT
    assert s.is_active


def test_find_by_student_id_returns_none_when_not_exists(repo, linebot_clean):
    s = repo.find_by_student_id("999999")
    assert s is None


def test_save_inserts_new_student(repo, infra_seed_student):
    infra_seed_student(
        student_id="1919810",
        user_id="lineid_new",
        mdl_id="12345",
        name="新學生",
    )

    found = repo.find_by_student_id("1919810")
    assert found is not None
    assert found.name == "新學生"
    assert found.line_user_id == "lineid_new"
