# dao/dao_hypothesis.py
from dao.db_connection import get_connection
from models.hypothesis import Hypothesis


class HypothesisDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM hypothesis")
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def get_by_project(self, project_id: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM hypothesis WHERE project_id=%s",
                    (project_id,))
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def insert(self, h: Hypothesis):
        sql = """INSERT INTO hypothesis
                 (hyp_id, project_id, text, status, confidence, pmids, note)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    h.getHypId(), h.getProjectId(), h.getText(),
                    h.getStatus(), h.getConfidence(),
                    h.getPmids(), h.getNote()
                ))
            conn.commit()

    def update_status(self, hyp_id: str, status: str, note: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE hypothesis SET status=%s, note=%s WHERE hyp_id=%s",
                    (status, note, hyp_id))
            conn.commit()

    def _to_obj(self, r):
        return Hypothesis(
            r["hyp_id"], r["project_id"], r["text"],
            r["status"], r["confidence"], r["pmids"], r["note"]
        )