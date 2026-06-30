# core/audit_chain.py
"""
L0 Compliance — SHA-256 linked audit chain.

Every write to the system goes through AuditChain.log().
Each entry's chain_hash = SHA256(payload_hash + prev_chain_hash),
making the log tamper-evident: modifying any row breaks all
subsequent hashes.
"""

import hashlib
import json
from datetime import datetime
from dao.db_connection import get_connection

GENESIS_HASH = "0" * 64


class AuditChain:

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_last_chain_hash(cur) -> tuple:
        cur.execute(
            "SELECT id, chain_hash FROM audit_chain "
            "ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            return GENESIS_HASH, None
        return row["chain_hash"], row["id"]

    @staticmethod
    def log(user_id, action, entity_type, entity_id,
            detail="", project_id=None, ip_owner="platform"):
        """
        Append one entry to audit_chain. Returns new row id.
        ip_owner: 'platform' | 'lab' | 'shared'
        """
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        payload_str = json.dumps({
            "ts": ts, "user": user_id, "action": action,
            "entity_type": entity_type, "entity_id": entity_id,
            "detail": detail,
        }, sort_keys=True, ensure_ascii=False)
        payload_hash = AuditChain._sha256(payload_str)

        sql = """INSERT INTO audit_chain
                 (timestamp, user_id, action, entity_type, entity_id,
                  detail, ip_owner, project_id,
                  payload_hash, chain_hash, prev_id)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        with get_connection() as conn:
            with conn.cursor() as cur:
                prev_hash, prev_id = AuditChain._get_last_chain_hash(cur)
                chain_hash = AuditChain._sha256(payload_hash + prev_hash)
                cur.execute(sql, (
                    ts, user_id, action, entity_type, entity_id,
                    detail, ip_owner, project_id,
                    payload_hash, chain_hash, prev_id,
                ))
                new_id = cur.lastrowid
            conn.commit()
        return new_id

    @staticmethod
    def verify_chain(limit=1000):
        """
        Verify integrity of last `limit` rows.
        Returns (True, "OK") or (False, "Broken at id=N").
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM audit_chain ORDER BY id ASC LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()
        if not rows:
            return True, "Chain is empty"

        prev_chain_hash = GENESIS_HASH
        for row in rows:
            payload_str = json.dumps({
                "ts":          str(row["timestamp"]),
                "user":        row["user_id"],
                "action":      row["action"],
                "entity_type": row["entity_type"],
                "entity_id":   row["entity_id"],
                "detail":      row["detail"] or "",
            }, sort_keys=True, ensure_ascii=False)
            expected_payload = AuditChain._sha256(payload_str)
            expected_chain   = AuditChain._sha256(expected_payload + prev_chain_hash)
            if row["chain_hash"] != expected_chain:
                return False, f"Chain broken at id={row['id']}"
            prev_chain_hash = row["chain_hash"]

        return True, f"OK — {len(rows)} entries verified"

    @staticmethod
    def get_recent(limit=200):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, timestamp, user_id, action, "
                    "entity_type, entity_id, detail, ip_owner, "
                    "project_id, chain_hash "
                    "FROM audit_chain ORDER BY id DESC LIMIT %s", (limit,)
                )
                return cur.fetchall()
