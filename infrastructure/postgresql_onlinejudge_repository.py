from sshtunnel import SSHTunnelForwarder
import psycopg2

from domain.score import OnlinejudgeRepository


class PostgreSQLOnlinejudgeRepository(OnlinejudgeRepository):
    def __init__(self, db_config: dict, ssh_config: dict):
        self.db_config = db_config
        self.ssh_config = ssh_config

    def _get_connection(self):
        tunnel = SSHTunnelForwarder(
            (self.ssh_config['ssh_host'], self.ssh_config.get('ssh_port', 22)),
            ssh_username=self.ssh_config['ssh_username'],
            ssh_password=self.ssh_config['ssh_password'],
            remote_bind_address=(
                self.db_config['host'], self.db_config['port'])
        )
        tunnel.start()

        conn = psycopg2.connect(
            host="127.0.0.1",
            port=tunnel.local_bind_port,
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database']
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
