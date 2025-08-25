import pymysql
from pymysql.cursors import DictCursor
from domain.leave_request import LeaveRequest, LeaveRequestRepository


def _fmt_maybe_dt(value, fmt: str):
    """value 是 datetime/date 就 strftime；是 str/其它就原樣回傳"""
    try:
        return value.strftime(fmt)
    except AttributeError:
        return value


class MySQLLeaveRepository(LeaveRequestRepository):
    """
    MySQL 寫入請假資料的 Repository。

    - 預設強制使用 utf8mb4 與 DictCursor，避免中文寫入問題與欄位名取值混亂。
    - 若 db_config 內提供相同 key，會覆寫預設（例如你想用 autocommit=True）。
    """

    def __init__(self, db_config: dict, logger=None):
        self.db_config = db_config
        self.logger = logger

    def _get_connection(self):
        # 預設適合測試與正式：明確 charset、回傳 dict 列
        cfg = {
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "autocommit": False,  # 如需 autocommit 可在 db_config 覆寫
        }
        cfg.update(self.db_config)
        return pymysql.connect(**cfg)

    def save_leave_request(self, leave: LeaveRequest) -> str:
        sql = """
        INSERT INTO ask_for_leave (
            operation_time, student_ID, student_name, apply_time, reason, context_title
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        conn = None
        try:
            conn = self._get_connection()

            op_time = _fmt_maybe_dt(leave.operation_time, "%Y-%m-%d %H:%M:%S")
            # 若欄位型別是 DATE：用 YYYY-MM-DD；若是 DATETIME，可改 "%Y-%m-%d %H:%M:%S"
            apply_time = _fmt_maybe_dt(leave.apply_time, "%Y-%m-%d")

            with conn.cursor() as cur:
                cur.execute(sql, (
                    op_time,
                    leave.student_id,
                    leave.student_name,
                    apply_time,
                    leave.reason,
                    leave.context_title,
                ))
            conn.commit()
            return "收到，已經幫你請好假了。"

        except Exception as e:
            # 保留商業回覆，同時把錯誤記錄下來（正式環境建議 logger.exception）
            if self.logger:
                self.logger.exception("save_leave_request failed")
            else:
                # 測試或無 logger 時，至少留一條可見訊息（可改為 pass）
                print("[LeaveRepo] insert failed:", repr(e))

            try:
                # 重複請假容錯檢查（依你的產品邏輯保留）
                conn = conn or self._get_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM ask_for_leave WHERE student_ID=%s AND apply_time=%s LIMIT 1",
                        (leave.student_id, _fmt_maybe_dt(
                            leave.apply_time, "%Y-%m-%d")),
                    )
                    if cur.fetchone():
                        return "同學你已經請過假了喔。"
            except Exception as e2:
                if self.logger:
                    self.logger.exception("fallback select failed")
                else:
                    print("[LeaveRepo] SELECT fallback 也失敗：", repr(e2))

            return "很抱歉，請假失敗。"

        finally:
            if conn:
                conn.close()
