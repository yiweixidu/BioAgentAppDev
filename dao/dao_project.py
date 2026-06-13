# dao/dao_project.py
from dao.db_connection import get_connection
from models.project import Project


class ProjectDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM project ORDER BY proj_id")
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def insert(self, p: Project):
        sql = """INSERT INTO project
                 (proj_id, title, domain, grant_src, pi, status, skill, progress)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    p.getProjId(), p.getTitle(), p.getDomain(),
                    p.getGrant(), p.getPi(), p.getStatus(),
                    p.getSkill(), p.getProgress()
                ))
            conn.commit()

    def delete(self, proj_id: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM project WHERE proj_id=%s", (proj_id,))
            conn.commit()

    def update(self, p: Project):
        sql = """UPDATE project
                 SET title=%s, domain=%s, grant_src=%s,
                     pi=%s, status=%s, skill=%s, progress=%s
                 WHERE proj_id=%s"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    p.getTitle(), p.getDomain(), p.getGrant(),
                    p.getPi(), p.getStatus(), p.getSkill(),
                    p.getProgress(), p.getProjId()
                ))
            conn.commit()

    def update_status(self, proj_id: str, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE project SET status=%s WHERE proj_id=%s",
                    (status, proj_id))
            conn.commit()

    def get_titles(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT proj_id, title FROM project")
                rows = cur.fetchall()
        return {r["proj_id"]: r["title"] for r in rows}

    def count(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM project")
                return cur.fetchone()["cnt"]

    def search(self, keyword: str = '', status: str = None):
        conditions = []
        params     = []
        if keyword:
            conditions.append("(title LIKE %s OR proj_id LIKE %s)")
            params += [f'%{keyword}%', f'%{keyword}%']
        if status:
            conditions.append("status=%s")
            params.append(status)
        sql = "SELECT * FROM project"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def _to_obj(self, r):
        return Project(
            r['proj_id'], r['title'], r['domain'], r['grant_src'],
            r['pi'], r['status'], r['skill'], r['progress']
        )

    def get_distinct_domains(self):
        """Return all unique domain values from project table."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT domain FROM project ORDER BY domain")
                rows = cur.fetchall()
        return [r["domain"] for r in rows if r["domain"]]

    def get_distinct_grants(self):
        """Return all unique grant_src values actually used in projects."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT grant_src FROM project "
                    "WHERE grant_src IS NOT NULL ORDER BY grant_src")
                rows = cur.fetchall()
        return [r["grant_src"] for r in rows if r["grant_src"]]