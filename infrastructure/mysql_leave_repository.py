from domain.leave_request import LeaveRequest, LeaveRequestRepository


class MySQLLeaveRepository(LeaveRequestRepository):
    def __init__(self, conn):
        self.conn = conn

    def save_leave_request(self, leave: LeaveRequest) -> str:
        insert_sql = """
        INSERT INTO ask_for_leave (
            operation_time, student_ID, student_name, apply_time, reason, context_title
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_sql, (
                    leave.operation_time.strftime("%Y-%m-%d %H:%M:%S"),
                    leave.student_id,
                    leave.student_name,
                    leave.apply_time,
                    leave.reason,
                    leave.context_title
                ))
                self.conn.commit()
            return "收到，已經幫你請好假了。"
        except:
            # 🔽 這裡加強錯誤處理，以防 SELECT 本身也錯誤
            try:
                check_sql = """
                SELECT * FROM ask_for_leave
                WHERE student_ID = %s AND apply_time = %s
                """
                with self.conn.cursor() as cur:
                    cur.execute(check_sql, (
                        leave.student_id,
                        leave.apply_time
                    ))
                    if cur.fetchone():
                        return "同學你已經請過假了喔。"
            except Exception as e:
                print("[DEBUG] SELECT fallback 也失敗：", e)
            return "很抱歉，請假失敗。"
