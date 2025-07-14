import json
from domain.user_state import UserState, UserStateEnum, UserStateRepository
import pymysql

class MySQLUserStateRepository(UserStateRepository):
    def __init__(self, connection_pool):
        self.pool = connection_pool

    def get(self, line_user_id: str):
        conn = self.pool.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT state_name, context FROM user_states WHERE line_user_id = %s", (line_user_id,))
                row = cursor.fetchone()
                if row:
                    context = json.loads(row[1]) if row[1] else {}
                    return UserState(line_user_id, UserStateEnum[row[0]], context)
                return None
        finally:
            conn.close()

    def save(self, state: UserState):
        conn = self.pool.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_states (line_user_id, state_name, context)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE state_name = VALUES(state_name), context = VALUES(context)
                """, (state.line_user_id, state.status.name, json.dumps(state.context)))
                conn.commit()
        finally:
            conn.close()

    def delete(self, line_user_id: str):
        conn = self.pool.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM user_states WHERE line_user_id = %s", (line_user_id,))
                conn.commit()
        finally:
            conn.close()
