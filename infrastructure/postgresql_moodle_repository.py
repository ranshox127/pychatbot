"""
## 目前設定
idle_timeout 為 60 秒，測試方法就是直接等

> **「高峰期集中查詢、之後閒置」**  
> 如何在**高峰註冊效率**與**平時資源節省**之間取得平衡？

----------

## 🎯 核心問題拆解

### 1. 高峰期（第一次上課，同時30~40人註冊）
-   約 95% 學生集中同一時段註冊
-   每次註冊都會呼叫 `moodle_repo.find_student_enrollments()`
-   如果每個呼叫都開關 SSH Tunnel & DB 連線，會有：
    -   **效能瓶頸**：連續開關 SSH tunnel 費時（建立一條 SSH tunnel 通常耗時數百毫秒）
    -   **資源競爭**：每條 SSH 連線都會占用埠與 CPU thread（SSHTunnelForwarder 是同步的）

### 2. 非高峰期（之後幾乎沒人註冊）
-   平均一天可能 0~1 人註冊
-   長時間保持 SSH Tunnel 是 **沒意義且浪費資源** 的（尤其是雲端環境）
"""
# infrastructure/postgresql_moodle_repository.py
from typing import List, Optional
from threading import Lock, Timer
from contextlib import contextmanager

from domain.moodle_enrollment import MoodleEnrollment, MoodleRepository

from sshtunnel import SSHTunnelForwarder
import psycopg2


class PostgreSQLMoodleRepository(MoodleRepository):
    def __init__(self, db_config: dict, ssh_config: dict):
        self.conn_mgr = LazyMoodleConnectionManager(db_config, ssh_config)

    def find_student_enrollments(self, student_id: str) -> List[MoodleEnrollment]:
        with self.conn_mgr.get_cursor() as cur:
            # 這個 SQL 不再需要 course.fullname 作為 WHERE 條件
            sql = """
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
            cur.execute(sql, (student_id, student_id + '@%'))
            rows = cur.fetchall()
            # 將查詢結果映射到我們定義的 DTO 列表
            return [MoodleEnrollment(course_fullname=row[0], roleid=row[1], user_id=row[2], fullname=row[3]) for row in rows]

    def find_student_info(self, student_id: str) -> Optional[dict]:
        """
        根據 學生帳號（可能為 username 或 username@開頭）查找該學生資訊。
        """
        with self.conn_mgr.get_cursor() as cur:
            sql = """
            SELECT
                usr.id,
                usr.username,
                CONCAT(usr.lastname, usr.firstname) AS fullname
            FROM mdl_user AS usr
            WHERE usr.username = %s OR usr.username LIKE %s
            LIMIT 1;
            """

            cur.execute(
                sql, (student_id, student_id + '@%'))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "student_id": row[1],
                "fullname": row[2]
            }


class LazyMoodleConnectionManager:
    """
    ## ✅ 推薦方案：**高峰期動態啟動連線 + 自動關閉機制**

    實作一個 **延遲建立、可重用但會自動關閉的連線管理器**，結合：
    1.  **重複利用連線（高峰）**
    2.  **時間未使用自動關閉（非高峰）**

    ----------

    ## 🛠️ 技術方案：Lazy SSH + Expiring Connection Wrapper
    """

    def __init__(self, db_config, ssh_config, idle_timeout=60):
        # host, port, database, user, password
        self.db_config = dict(db_config)
        # enabled, ssh_host, ssh_port, ssh_username, ssh_password
        self.ssh_config = dict(ssh_config)
        self.db_config['port'] = int(self.db_config.get('port', 5432))
        self.ssh_config['ssh_port'] = int(self.ssh_config.get('ssh_port', 22))
        self.ssh_enabled = bool(self.ssh_config.get('enabled', True))

        self.idle_timeout = idle_timeout
        self.lock = Lock()
        self._conn = None
        self._tunnel = None
        self._timer = None

    def _start(self):
        try:
            if self.ssh_enabled:
                self._tunnel = SSHTunnelForwarder(
                    (self.ssh_config['ssh_host'],
                     self.ssh_config.get('ssh_port', 22)),
                    ssh_username=self.ssh_config['ssh_username'],
                    ssh_password=self.ssh_config.get('ssh_password'),
                    remote_bind_address=(
                        self.db_config['host'], self.db_config['port'])
                )
                self._tunnel.start()
                host = "127.0.0.1"
                port = self._tunnel.local_bind_port
            else:
                # 直連：連目標 host:port（在 compose 內用服務名）
                host = self.db_config['host']
                port = self.db_config['port']

            self._conn = psycopg2.connect(
                host=host,
                port=port,
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
        except Exception as e:
            if self._tunnel:
                try:
                    self._tunnel.close()
                except Exception:
                    pass
            self._tunnel = None
            self._conn = None
            raise

    def _schedule_close(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self.idle_timeout, self.close)
        self._timer.start()

    @contextmanager
    def get_cursor(self):
        with self.lock:
            if self._conn is None:
                self._start()
            else:
                # 連線失效時自動重連
                try:
                    with self._conn.cursor() as _test:
                        _test.execute("SELECT 1")
                except Exception:
                    try:
                        self._conn.close()
                    except Exception:
                        pass
                    self._conn = None
                    self._start()

            self._schedule_close()
            cur = self._conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def close(self):
        with self.lock:
            if self._conn:
                try:
                    self._conn.close()
                finally:
                    self._conn = None
            if self._tunnel:
                try:
                    self._tunnel.close()
                finally:
                    self._tunnel = None
