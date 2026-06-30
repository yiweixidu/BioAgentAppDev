# core/session.py
"""
Global session singleton — holds the current user's info after login.
All Tabs and Dialogs read the current user's role via Session.current().

Usage:
    from core.session import Session

    # Set at login time (called by LoginDialog)
    Session.set(res_id="RES-001", name="Dr. Liwei Rong",
                role="researcher", email="liwei@vanier.ca")

    # Read anywhere
    role = Session.current_role()       # 'researcher'
    name = Session.current_name()       # 'Dr. Liwei Rong'
    can  = Session.can_manage_options() # False
    Session.require_role(['admin','pi']) # raises PermissionError if not matched
"""

from core.access_control import can as rbac_can

# Super admin roles — allowed to manage dropdown options
SUPER_ADMIN_ROLES = {'admin', 'pi', 'lab_manager'}


class _Session:
    def __init__(self):
        self._res_id = None
        self._name   = ""
        self._role   = "viewer"
        self._email  = ""

    def set(self, res_id: str, name: str, role: str, email: str = ""):
        self._res_id = res_id
        self._name   = name
        self._role   = role.lower().replace(" ", "_")
        self._email  = email

    def clear(self):
        self.__init__()

    # ── Getters ──────────────────────────────────────────────
    def res_id(self)       -> str:  return self._res_id or ""
    def current_name(self) -> str:  return self._name
    def current_role(self) -> str:  return self._role
    def current_email(self)-> str:  return self._email

    def is_logged_in(self) -> bool:
        return self._res_id is not None

    def can_manage_options(self) -> bool:
        """PI, admin, lab_manager 可以管理下拉选项。"""
        return self._role in SUPER_ADMIN_ROLES

    def can(self, resource: str, action: str) -> bool:
        """Check RBAC permission for current user's role."""
        return rbac_can(self._role, resource, action)

    def require_role(self, allowed_roles: list):
        """If current role not in allowed_roles, raise PermissionError."""
        if self._role not in allowed_roles:
            raise PermissionError(
                f"Role '{self._role}' is not allowed. "
                f"Required: {allowed_roles}")

    def display_label(self) -> str:
        """Short string for UI header: 'Dr. Liwei Rong  [researcher]'"""
        return f"{self._name}  [{self._role}]"


# Singleton instance
Session = _Session()