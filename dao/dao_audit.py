# dao/dao_audit.py
from dao.db_connection import get_connection
from models.audit_entry import AuditEntry


class AuditDAO:

    def add(self, user: str, action: str,
            entity: str, detail: str):
        entry = AuditEntry(user, action, entity, detail)
        sql = """INSERT INTO audit_trail
                 (timestamp, user, action, entity, detail)
                 VALUES (%s,%s,%s,%s,%s)"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    entry.getTimestamp(), entry.getUser(),
                    entry.getAction(), entry.getEntity(),
                    entry.getDetail()
                ))
            conn.commit()

    def get_all(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM audit_trail ORDER BY timestamp DESC")
                rows = cur.fetchall()
        return [AuditEntry(
            r["user"], r["action"], r["entity"],
            r["detail"], r["timestamp"], r["id"]
        ) for r in rows]