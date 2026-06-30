# dao/dao_inference.py  — extended for full_output and project filtering
import json
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

    def get_by_project(self, project_id: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM inference_history "
                    "WHERE project_id=%s ORDER BY timestamp DESC",
                    (project_id,))
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def get_full(self, inf_id: str) -> dict:
        """Return the full raw dict for one record (includes result_full JSON)."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM inference_history WHERE inf_id=%s", (inf_id,))
                return cur.fetchone()

    def insert(self, rec: InferenceRecord, full_output: dict = None):
        """
        Insert inference record.
        full_output: the complete SkillResult.full_output dict (stored as JSON).
        """
        full_json = json.dumps(full_output, ensure_ascii=False) if full_output else None
        sql = """INSERT INTO inference_history
                 (inf_id, type, model, project_id,
                  input, result_summary, result_full,
                  confidence, ip_owner, timestamp)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                 ON DUPLICATE KEY UPDATE
                  result_summary=VALUES(result_summary)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    rec.getInfId(), rec.getType(), rec.getModel(),
                    rec.getProjectId(), rec.getInput(),
                    rec.getResultSummary(), full_json,
                    getattr(rec, 'confidence', None),
                    getattr(rec, 'ip_owner', 'platform'),
                    rec.getTimestamp(),
                ))
            conn.commit()

    def count(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM inference_history")
                return cur.fetchone()["cnt"]

    def _to_obj(self, r):
        rec = InferenceRecord(
            r["inf_id"], r["type"], r["model"],
            r["project_id"], r["input"],
            r["result_summary"], str(r["timestamp"])
        )
        # Attach extras for report generation
        rec.confidence = r.get("confidence") or 0.0
        rec.ip_owner   = r.get("ip_owner") or "platform"
        rec.result_full = r.get("result_full") or ""
        return rec
