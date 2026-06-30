# gui/login_dialog.py
"""
Login Dialog — The first window shown when the application starts.

Flow:
  1. User enters Email + Password
  2. Validate against the researcher table (password field, SHA-256 hash)
  3. Success → Session.set(...) → close dialog → MainWindow appears
  4. Failure → show error, max 5 attempts, then exit

Initial passwords:
  All seed accounts in seed_data.sql have an empty password string.
  Log in with an empty password initially, then change it later in the Researcher Tab.
  (Production: use bcrypt; SHA-256 is used here for simplicity.)
"""
import hashlib
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.session import Session
from core.audit_chain import AuditChain

# ── Palette ────────────────────────────────────────────────
BG     = "#111D2E"
SURF   = "#1C2D44"
SURF2  = "#172438"
BORDER = "#2A3F5C"
TEAL   = "#12A898"
AMBER  = "#C09060"
RED    = "#E53E3E"
TXT    = "#D5E2EE"
TXT_M  = "#4A6880"

QSS = f"""
QDialog {{
    background: {BG};
    color: {TXT};
}}
QLabel {{
    background: transparent;
    border: none;
    color: {TXT};
}}
QLineEdit {{
    background: {SURF2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TXT};
    padding: 6px 14px;
    min-height: 24px;
    font-size: 13px;
    selection-background-color: {TEAL}50;
}}
QLineEdit:focus {{
    border-color: {TEAL};
}}
QPushButton {{
    background: {SURF};
    color: #7A9EB8;
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 10px 28px;
    font-size: 13px;
    font-weight: 500;
    min-height: 36px;
}}
QPushButton:hover {{
    background: #243858;
    color: {TXT};
    border-color: #4A6880;
}}
QPushButton#loginBtn {{
    background: #8C6A3C;
    color: #EADBC6;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    font-size: 12px;
    padding: 0px;
    min-height: 24px;
    max-height: 24px;
    min-width: 100px;
    max-width: 100px;
}}
QPushButton#loginBtn:hover {{
    background: #A07848;
}}
"""

MAX_ATTEMPTS = 5


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._attempts = 0
        self.setWindowTitle("BioAgent  ·  Login")
        self.setFixedSize(420, 520)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 32)
        layout.setSpacing(0)

        # ── Logo / title ──────────────────────────────────────
        logo = QLabel("🧬")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI Emoji", 36))
        logo.setStyleSheet("background:transparent;")
        layout.addWidget(logo)
        layout.addSpacing(8)

        title = QLabel("BioAgent")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color:{TEAL};font-size:26px;font-weight:700;"
            f"background:transparent;")
        layout.addWidget(title)

        sub = QLabel("Research Management System")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            f"color:{TXT_M};font-size:12px;background:transparent;")
        layout.addWidget(sub)
        layout.addSpacing(32)

        # ── Card ─────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(
            f"QFrame{{background:{SURF};border:1.5px solid {BORDER};"
            f"border-radius:14px;}}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(14)

        # Email
        email_lbl = QLabel("EMAIL")
        email_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;"
            f"letter-spacing:0.8px;background:transparent;border:none")
        cl.addWidget(email_lbl)
        self.emailLE = QLineEdit()
        self.emailLE.setPlaceholderText("your@institution.ca")
        cl.addWidget(self.emailLE)

        # Password
        pw_lbl = QLabel("PASSWORD")
        pw_lbl.setStyleSheet(
            f"color:{TXT_M};font-size:10px;font-weight:700;"
            f"letter-spacing:0.8px;background:transparent;border:none")
        cl.addWidget(pw_lbl)
        self.pwLE = QLineEdit()
        self.pwLE.setPlaceholderText("Leave blank for seed accounts")
        self.pwLE.setEchoMode(QLineEdit.EchoMode.Password)
        cl.addWidget(self.pwLE)

        # Error label (hidden until needed)
        self.errorLbl = QLabel("")
        self.errorLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.errorLbl.setWordWrap(True)
        self.errorLbl.setStyleSheet(
            f"color:{RED};font-size:11px;background:transparent;")
        self.errorLbl.setVisible(False)
        cl.addWidget(self.errorLbl)

        # Login button
        self.loginBtn = QPushButton("Sign In")
        self.loginBtn.setObjectName("loginBtn")
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.loginBtn)
        btn_row.addStretch()
        cl.addLayout(btn_row)

        layout.addWidget(card)
        layout.addSpacing(20)

        # ── Hint ─────────────────────────────────────────────
        hint = QLabel(
            "Seed accounts: liwei.rong@vanier.ca\n"
            "or  ana.cardinal@vanier.ca  (empty password)")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            f"color:{TXT_M};font-size:10px;background:transparent;")
        layout.addWidget(hint)
        layout.addStretch()

        # ── Signals ──────────────────────────────────────────
        self.loginBtn.clicked.connect(self._attempt_login)
        self.pwLE.returnPressed.connect(self._attempt_login)
        self.emailLE.returnPressed.connect(self.pwLE.setFocus)

    # ── Login logic ──────────────────────────────────────────

    def _attempt_login(self):
        email    = self.emailLE.text().strip().lower()
        password = self.pwLE.text()

        if not email:
            self._show_error("Please enter your email address.")
            return

        self._attempts += 1
        if self._attempts > MAX_ATTEMPTS:
            QMessageBox.critical(
                self, "Too many attempts",
                "Maximum login attempts exceeded. Application will close.")
            self.reject()
            return

        try:
            researcher = self._lookup(email, password)
        except Exception as e:
            self._show_error(f"Database error: {e}")
            return

        if researcher is None:
            remaining = MAX_ATTEMPTS - self._attempts
            self._show_error(
                f"Invalid email or password.\n"
                f"{remaining} attempt(s) remaining.")
            self.pwLE.clear()
            self.pwLE.setFocus()
            return

        # ── Success ──────────────────────────────────────────
        Session.set(
            res_id = researcher["res_id"],
            name   = researcher["name"],
            role   = researcher["role"],
            email  = researcher["email"],
        )

        try:
            AuditChain.log(
                user_id     = researcher["res_id"],
                action      = "LOGIN",
                entity_type = "session",
                entity_id   = researcher["res_id"],
                detail      = f"role={researcher['role']}",
                ip_owner    = "platform",
            )
        except Exception:
            pass   # audit failure must not block login

        self.accept()

    def _lookup(self, email: str, password: str):
        """
        Return researcher dict if credentials match, else None.
        Password check: SHA-256(password) == stored hash.
        Empty password is allowed during initial setup.
        """
        from dao.db_connection import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT res_id, name, role, email, password "
                    "FROM researcher WHERE LOWER(email)=%s",
                    (email,))
                row = cur.fetchone()

        if row is None:
            return None

        stored = row["password"] or ""
        given  = _hash(password)

        # Accept: stored is empty AND given password is empty (seed accounts)
        # OR stored hash matches given hash
        if stored == "" and password == "":
            return row
        if stored == given:
            return row
        # Also accept plain empty stored with any password? No — strict.
        return None

    def _show_error(self, msg: str):
        self.errorLbl.setText(msg)
        self.errorLbl.setVisible(True)


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()