# dao/dao_grant.py
from dao.db_connection import get_connection
from models.grant_fund import Grant
from models.milestone  import Milestone


class GrantDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM grant_fund")
                rows = cur.fetchall()
        return [self._to_grant(r) for r in rows]

    def get_milestones(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM milestone ORDER BY due")
                rows = cur.fetchall()
        return [self._to_milestone(r) for r in rows]

    def add_milestone(self, m: Milestone):
        sql = """INSERT INTO milestone (grant_id, descr, due, completed)
                 VALUES (%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    m.getGrantId(), m.getDesc(),
                    m.getDue(), int(m.isCompleted())
                ))
            conn.commit()

    def mark_milestone_done(self, milestone_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE milestone SET completed=1 WHERE id=%s",
                    (milestone_id,))
            conn.commit()

    def _to_grant(self, r):
        return Grant(
            r["grant_id"], r["project_id"], r["agency"],
            r["deadline"], r["total"], r["used"]
        )

    def _to_milestone(self, r):
        return Milestone(
            r["grant_id"], r["descr"], r["due"],
            bool(r["completed"]), r["id"]
        )