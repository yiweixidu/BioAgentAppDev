# core/access_control.py
"""L0 Compliance — RBAC (SQL-backed, graceful dev-mode fallback)."""

from dao.db_connection import get_connection

class AccessDenied(Exception):
    pass

_cache: dict = {}
_loaded = False

def _load_permissions():
    global _cache, _loaded
    _cache = {}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role_id, resource, action FROM rbac_permission")
                for row in cur.fetchall():
                    _cache[(row["role_id"], row["resource"], row["action"])] = True
    except Exception:
        pass  # DB not available — only admin shortcut works
    _loaded = True

def refresh():
    global _loaded; _loaded = False; _load_permissions()

def can(role: str, resource: str, action: str) -> bool:
    if not _loaded:
        _load_permissions()
    if role == "admin":
        return True
    return _cache.get((role, resource, action), False)

def require_permission(role: str, resource: str, action: str):
    if not can(role, resource, action):
        raise AccessDenied(f"Role '{role}' cannot {action} {resource}.")
