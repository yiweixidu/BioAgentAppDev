# dao/dao_researcher.py
from dao.db_connection import get_connection
from models.researcher import Researcher


class ResearcherDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM researcher ORDER BY res_id")
                rows = cur.fetchall()
        return [Researcher(
            r["res_id"], r["name"], r["institution"],
            r["pi"], r["domain"], r["role"], r["email"]
        ) for r in rows]

    def insert(self, r: Researcher):
        sql = """INSERT INTO researcher
                 (res_id, name, institution, pi, domain, role, email, password)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    r.getResId(), r.getName(), r.getInstitution(),
                    r.getPi(), r.getDomain(), r.getRole(),
                    r.getEmail(), ""
                ))
            conn.commit()

    def delete(self, res_id: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM researcher WHERE res_id=%s", (res_id,))
            conn.commit()

    def get_by_id(self, res_id: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM researcher WHERE res_id=%s", (res_id,))
                r = cur.fetchone()
        if r is None:
            return None
        return Researcher(
            r["res_id"], r["name"], r["institution"],
            r["pi"], r["domain"], r["role"], r["email"]
        )

    def count(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM researcher")
                return cur.fetchone()["cnt"]