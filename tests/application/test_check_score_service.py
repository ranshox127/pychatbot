# uv run -m pytest tests/domain/test_check_score_service.py
import pytest

from application.check_score_service import CheckScoreService


def test_check_publish_contents_has_no_contents():
    """
    Scenario: 尚未有任何開放的單元

    Expect:
    系統應該通知「目前還沒有任何要繳交的作業喔。」
    學生的狀態應重置成 IDLE
    """


def test_check_publish_contents_has_contents():
    """
    Scenario: 存在已開放的單元

    Expect:
    系統應該通知「請輸入要查詢的單元。(ex. {unit_list_text})」
    學生的狀態應轉換成 AWAITING_CONTENTS_NAME
    """


def test_check_score_with_wrong_content():
    """
    Scenario: 查詢不存在的單元

    Expect:
    系統應該通知「請單元名稱不存在，請確認後再重新查詢喔。」
    學生的狀態應重置成 IDLE
    """


def test_check_score_with_right_content():
    """
    Scenario: 查詢已開放且存在的單元

    Expect:
    系統應該通知對應的章節的各項活動的分數(看當時什麼狀況)
    學生的狀態應重置成 IDLE
    系統應該記錄該次的 event
    """
