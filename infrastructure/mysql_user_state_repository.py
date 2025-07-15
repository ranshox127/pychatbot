import json

import pymysql

from domain.user_state import UserState, UserStateEnum, UserStateRepository


class MySQLUserStateRepository(UserStateRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def get(self, line_user_id: str):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT state_name, context FROM user_states WHERE line_user_id = %s", (line_user_id,))
                row = cursor.fetchone()
                if row:
                    context = json.loads(row[1]) if row[1] else {}
                    return UserState(line_user_id, UserStateEnum[row[0]], context)
                return None

    def save(self, state: UserState):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_states (line_user_id, state_name, context)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE state_name = VALUES(state_name), context = VALUES(context)
                """, (state.line_user_id, state.status.name, json.dumps(state.context)))
                conn.commit()

    def delete(self, line_user_id: str):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM user_states WHERE line_user_id = %s", (line_user_id,))
                conn.commit()
