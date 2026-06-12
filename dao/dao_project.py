# dao/dao_project.py
from dao.db_connection import get_connection
from models.project import Project


class ProjectDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM project ORDER BY proj_id")
                rows = cur.fetchall()
        return [Project(
            r["proj_id"], r["title"], r["domain"], r["grant_src"],
            r["pi"], r["status"], r["skill"], r["progress"]
        ) for r in rows]

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

    def update_status(self, proj_id: str, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE project SET status=%s WHERE proj_id=%s",
                    (status, proj_id))
            conn.commit()

    def get_titles(self):
        """返回 {proj_id: title} 字典，供下拉框使用"""
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