# dao/dao_model_skill.py
from dao.db_connection import get_connection
from models.model_skill import ModelSkill


class ModelSkillDAO:

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM model_skill ORDER BY skill_id")
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def get_active(self):
        """Return only skills with status='active', used by InferenceTab model picker."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM model_skill WHERE status='active' ORDER BY skill_id")
                rows = cur.fetchall()
        return [self._to_obj(r) for r in rows]

    def insert(self, s: ModelSkill):
        sql = """INSERT INTO model_skill
                 (skill_id, name, project_id, lora_version,
                  threshold, benchmark, status, loaded)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    s.getSkillId(), s.getName(), s.getProjectId(),
                    s.getLoraVersion(), s.getThreshold(),
                    s.getBenchmark(), s.getStatus(), s.getLoaded()
                ))
            conn.commit()

    def update_status(self, skill_id: str, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE model_skill SET status=%s WHERE skill_id=%s",
                    (status, skill_id))
            conn.commit()

    def delete(self, skill_id: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM model_skill WHERE skill_id=%s", (skill_id,))
            conn.commit()

    def count(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM model_skill")
                return cur.fetchone()["cnt"]

    def _to_obj(self, r):
        return ModelSkill(
            r["skill_id"], r["name"], r["project_id"],
            r["lora_version"], r["threshold"],
            r["benchmark"], r["status"], str(r["loaded"])
        )