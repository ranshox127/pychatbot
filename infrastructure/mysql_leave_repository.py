from domain.leave_request import LeaveRequest, LeaveRequestRepository


class MySQLLeaveRepository(LeaveRequestRepository):
    def __init__(self, conn):
        self.conn = conn

    def save_leave_request(self, leave: LeaveRequest) -> str:
        insert_sql = f"""
        INSERT INTO ask_for_leave VALUES (
            "{leave.operation_time}",
            "{leave.student_id}",
            "{leave.student_name}",
            "{leave.apply_time}",
            "{leave.reason}",
            "{leave.context_title}"
        )
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_sql)
                self.conn.commit()
            return "收到，已經幫你請好假了。"
        except:
            check_sql = f"""
            SELECT * FROM ask_for_leave
            WHERE student_ID = "{leave.student_id}" AND apply_time = "{leave.apply_time}"
            """
            with self.conn.cursor() as cur:
                cur.execute(check_sql)
                if cur.fetchone():
                    return "同學你已經請過假了喔。"
                return "很抱歉，請假失敗。"
