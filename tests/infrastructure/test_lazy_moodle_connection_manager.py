# uv run -m pytest tests/infrastructure/test_lazy_moodle_connection_manager.py
from unittest.mock import patch

import psycopg2
import pytest

from infrastructure.postgresql_moodle_repository import LazyMoodleConnectionManager

# 我們需要 patch 掉所有外部依賴
# 使用 autospec=True 可以讓 mock 物件的簽名與原物件一致，更安全


@patch('infrastructure.postgresql_moodle_repository.psycopg2', autospec=True)
@patch('infrastructure.postgresql_moodle_repository.SSHTunnelForwarder', autospec=True)
@patch('infrastructure.postgresql_moodle_repository.Timer', autospec=True)
class TestLazyMoodleConnectionManager:

    @pytest.fixture
    def manager_instance(self):
        """提供一個 manager 實體，並設定短的 timeout 以加速測試"""
        # 提供包含必要鍵的假設定，即使值是假的也沒關係
        dummy_ssh_config = {
            "ssh_host": "dummy_host",
            "ssh_username": "dummy_user",
            "ssh_password": "dummy_password"
        }
        dummy_db_config = {
            "host": "dummy_db_host",
            "port": 5432,
            "database": "dummy_db",
            "user": "dummy_user",
            "password": "dummy_password"
        }
        return LazyMoodleConnectionManager(dummy_db_config, dummy_ssh_config, idle_timeout=0.1)

    def test_initial_state_is_lazy(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試初始狀態，所有連線物件都應為 None"""
        assert manager_instance._conn is None
        assert manager_instance._tunnel is None
        assert manager_instance._timer is None

    def test_first_call_establishes_connection(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試第一次呼叫 get_cursor 會建立連線"""
        # 執行
        with manager_instance.get_cursor():
            pass

        # 驗證
        MockSSHTunnel.return_value.start.assert_called_once()
        MockPsycopg2.connect.assert_called_once()
        assert manager_instance._conn is not None
        assert manager_instance._tunnel is not None

    def test_subsequent_calls_reuse_connection(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試後續呼叫會重複使用連線，而不是建立新的"""
        # 第一次呼叫
        with manager_instance.get_cursor():
            pass
        # 第二次呼叫
        with manager_instance.get_cursor():
            pass

        # 驗證 start 和 connect 依然只被呼叫一次
        MockSSHTunnel.return_value.start.assert_called_once()
        MockPsycopg2.connect.assert_called_once()

    def test_auto_close_is_scheduled(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試 get_cursor 是否會排程自動關閉"""
        with manager_instance.get_cursor():
            pass

        # 驗證 Timer 被建立，且其回呼函式是 self.close
        MockTimer.assert_called_with(0.1, manager_instance.close)
        # 驗證 Timer 的 start 方法被呼叫
        MockTimer.return_value.start.assert_called_once()

    def test_manual_close_cleans_up_resources(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試手動呼叫 close 方法是否能正確清理資源"""
        # 先建立連線
        with manager_instance.get_cursor():
            pass

        # 取得 mock 的連線和通道物件
        mock_conn = manager_instance._conn
        mock_tunnel = manager_instance._tunnel

        # 手動關閉
        manager_instance.close()

        # 驗證資源的 close 方法被呼叫
        mock_conn.close.assert_called_once()
        mock_tunnel.close.assert_called_once()

        # 驗證內部狀態被重設為 None
        assert manager_instance._conn is None
        assert manager_instance._tunnel is None

    def test_connection_failure_handling(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試連線失敗時的錯誤處理"""
        # 讓建立 tunnel 時就引發例外
        MockSSHTunnel.return_value.start.side_effect = Exception(
            "SSH connection failed")

        # 驗證呼叫 get_cursor 時會拋出例外
        with pytest.raises(Exception, match="SSH connection failed"):
            with manager_instance.get_cursor():
                pass

        # 驗證即使發生錯誤，內部狀態依然是乾淨的
        assert manager_instance._conn is None
        assert manager_instance._tunnel is None

    def test_get_cursor_after_manual_close(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試手動關閉後，再次呼叫 get_cursor 是否能重新建立連線"""
        with manager_instance.get_cursor():
            pass

        # 先手動關閉連線
        manager_instance.close()

        # 再次嘗試呼叫 get_cursor
        with manager_instance.get_cursor():
            pass  # 應該重新建立連線

        MockSSHTunnel.return_value.start.assert_called_with()
        MockPsycopg2.connect.assert_any_call(
            host='127.0.0.1',
            port=MockSSHTunnel.return_value.local_bind_port,  # 使用 mock 生成的端口
            database='dummy_db',
            user='dummy_user',
            password='dummy_password'
        )

    def test_connection_failure_handling_2(self, MockTimer, MockSSHTunnel, MockPsycopg2, manager_instance):
        """測試 psycopg2.connect() 失敗時，連線會被正確處理"""
        MockPsycopg2.connect.side_effect = psycopg2.OperationalError(
            "Database connection failed")

        with pytest.raises(psycopg2.OperationalError, match="Database connection failed"):
            with manager_instance.get_cursor():
                pass

        assert manager_instance._conn is None
        assert manager_instance._tunnel is None
