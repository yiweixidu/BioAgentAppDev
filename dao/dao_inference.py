# dao/dao_inference.py
from dao.db_connection import get_connection
from models.inference_record import InferenceRecord


class InferenceDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM inference_history ORDER BY timestamp DESC")
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def insert(self, rec: InferenceRecord):
        sql = """INSERT INTO inference_history
                 (inf_id, type, model, project_id,
                  input, result_summary, timestamp)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    rec.getInfId(), rec.getType(), rec.getModel(),
                    rec.getProjectId(), rec.getInput(),
                    rec.getResultSummary(), rec.getTimestamp()
                ))
            conn.commit()

    def count(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM inference_history")
                return cur.fetchone()["cnt"]

    def _to_obj(self, r):
        return InferenceRecord(
            r["inf_id"], r["type"], r["model"],
            r["project_id"], r["input"],
            r["result_summary"], str(r["timestamp"])
        )