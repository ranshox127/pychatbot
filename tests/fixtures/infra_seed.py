# tests/fixtures/infra_seed.py
from functools import partial
import pytest
from tests.fixtures.seeder import (seed_course as _seed_course,
                                   seed_student as _seed_student,
                                   seed_units as _seed_units)


@pytest.fixture
def _bind():
    # usage: binder(func, *deps) -> callable
    return lambda func, *deps: partial(func, *deps)


# Infrastructure：用不依賴 app 的「乾淨連線」fixture
@pytest.fixture
def infra_seed_course(_bind, linebot_clean):
    return _bind(_seed_course, linebot_clean)


@pytest.fixture
def infra_seed_student(_bind, linebot_clean):
    return _bind(_seed_student, linebot_clean)


@pytest.fixture
def infra_seed_units(_bind, linebot_clean, review_clean):
    return _bind(_seed_units, review_clean, linebot_clean)


# Integration：用啟動 app 後的 truncate 連線（你現在的 linebot_mysql_truncate）
@pytest.fixture
def it_seed_course(_bind, linebot_mysql_truncate):
    return _bind(_seed_course, linebot_mysql_truncate)


def it_seed_student(_bind, linebot_mysql_truncate):
    return _bind(_seed_student, linebot_mysql_truncate)


@pytest.fixture
def it_seed_units(_bind, rs_mysql_truncate, linebot_mysql_truncate):
    return _bind(_seed_units, rs_mysql_truncate, linebot_mysql_truncate)
