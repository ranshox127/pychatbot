from sshtunnel import SSHTunnelForwarder
import psycopg2

from domain.score import OnlinejudgeRepository


class PostgreSQLOnlinejudgeRepository(OnlinejudgeRepository):
    def __init__(self, ssh_host: str, ssh_user: str, ssh_password: str,
                 db_user: str, db_password: str, db_name: str, ssh_port: int = 22, db_port: int = 5432):
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password

        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name

        self.ssh_port = ssh_port
        self.db_port = db_port

    def _get_connection(self):
        tunnel = SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_user,
            ssh_password=self.ssh_password,
            remote_bind_address=('127.0.0.1', self.db_port)
        )
        tunnel.start()

        conn = psycopg2.connect(
            host='127.0.0.1',
            port=tunnel.local_bind_port,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name
        )

        return tunnel, conn

    def _count_problem_by_type(self, oj_contest_title, contents_name, type_suffix, q_type):
        tunnel, conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT COUNT(DISTINCT problem._id)
                    FROM problem
                    JOIN contest ON problem.contest_id = contest.id
                    WHERE problem._id ILIKE %s
                    AND contest.title ILIKE %s
                    AND problem.visible = TRUE;
                """
                problem_like = f"%{contents_name}_{type_suffix}%"
                contest_title_like = f"%{oj_contest_title}%{contents_name}%{q_type}%"
                cur.execute(query, (problem_like, contest_title_like))
                result = cur.fetchone()
                return int(result[0]) if result else 0
        finally:
            conn.close()
            tunnel.close()

    def get_exercise_number_by_contents_name(self, oj_contest_title, contents_name):
        return self._count_problem_by_type(oj_contest_title, contents_name, 'E', 'Exercise')

    def get_advance_number_by_contents_name(self, oj_contest_title, contents_name):
        return self._count_problem_by_type(oj_contest_title, contents_name, 'A', 'Advance')

    def _count_submission_by_type(self, OJ_contest_title, contents_name, stdID, deadline, type_suffix, q_type):
        tunnel, conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT COUNT(DISTINCT problem._id)
                    FROM problem
                    JOIN submission ON submission.problem_id = problem.id
                    JOIN contest ON submission.contest_id = contest.id
                    WHERE problem._id ILIKE %s
                    AND submission.result = 0
                    AND submission.create_time <= %s
                    AND (submission.username ILIKE %s OR submission.username = %s)
                    AND contest.title ILIKE %s
                    AND problem.visible = TRUE;
                """
                problem_like = f"{contents_name}_{type_suffix}%"
                username_like = f"{stdID}@%"
                contest_title_like = f"%{OJ_contest_title}%{contents_name}%{q_type}%"
                cur.execute(query, (
                    problem_like,
                    deadline,
                    username_like,
                    stdID,
                    contest_title_like
                ))
                result = cur.fetchone()
                return int(result[0]) if result else 0
        finally:
            conn.close()
            tunnel.close()

    def get_advance_submission_by_contents_name(self, OJ_contest_title, contents_name, stdID, deadline):
        return self._count_submission_by_type(OJ_contest_title, contents_name, stdID, deadline, 'A', 'Advance')

    def get_exercise_submission_by_contents_name(self, OJ_contest_title, contents_name, stdID, deadline):
        return self._count_submission_by_type(OJ_contest_title, contents_name, stdID, deadline, 'E', 'Exercise')
