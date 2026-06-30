# main_window.py – Whimsigoth v2 (lighter + vivid borders)
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout,
                             QHBoxLayout, QWidget, QLabel, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import pyqtSignal
from gui.tabs.dashboard_tab  import DashboardTab
from gui.tabs.researcher_tab import ResearcherTab
from gui.tabs.projects_tab   import ProjectsTab
from gui.tabs.knowledge_tab  import KnowledgeTab
from gui.tabs.hypothesis_tab import HypothesisTab
from gui.tabs.inference_tab  import InferenceTab
from gui.tabs.grant_tab      import GrantTab
from core.session            import Session
from core.audit_chain        import AuditChain

QSS = """
/* ── Root ────────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #111D2E;
    color: #D5E2EE;
    font-family: "Segoe UI","Inter","SF Pro Display",system-ui,sans-serif;
    font-size: 13px;
}

/* ── Tab bar ──────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    background-color: #111D2E;
    border: none;
    border-top: 1px solid #2A3F5C;
}
QTabBar             { background: #0F1929; }
QTabBar::tab {
    background: #0F1929;
    color: #4A6880;
    padding: 11px 22px;
    margin-right: 1px;
    font-size: 12px;
    font-weight: 500;
    border: none;
    border-bottom: 2px solid transparent;
    min-width: 118px;
}
QTabBar::tab:selected  { color: #EADBC6; border-bottom: 2px solid #C09060; background: #111D2E; }
QTabBar::tab:hover:!selected { color: #7A9EB8; background: #12202F; }

/* ── Inputs ───────────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #0F1D2C;
    border: 1px solid #2A3F5C;
    border-radius: 8px;
    color: #D5E2EE;
    padding: 7px 12px;
    font-size: 12px;
    selection-background-color: #C0906050;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #C09060; }
QComboBox::drop-down          { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #172438;
    color: #D5E2EE;
    selection-background-color: #2A3F5C;
    border: 1px solid #2A3F5C;
    outline: none;
}
QSpinBox::up-button, QSpinBox::down-button { width: 18px; border: none; }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1C2D44;
    color: #7A9EB8;
    border: 1px solid #2A3F5C;
    border-radius: 20px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: 500;
    min-height: 32px;
}
QPushButton:hover   { background-color: #243858; color: #D5E2EE; border-color: #4A6880; }
QPushButton:pressed { background-color: #0F1929; }
QPushButton#primaryButton {
    background-color: #8C6A3C;
    color: #EADBC6;
    border: none;
    font-weight: 700;
}
QPushButton#primaryButton:hover   { background-color: #A07848; }
QPushButton#primaryButton:pressed { background-color: #7A5830; }
QPushButton#dangerButton {
    background-color: #251418;
    color: #E53E3E;
    border: 1px solid #E53E3E50;
}
QPushButton#dangerButton:hover { background-color: #321820; }

/* ── Type selector pills ──────────────────────────────────────────────────── */
QPushButton#typeBtn {
    background-color: #1C2D44;
    color: #7A9EB8;
    border: 1px solid #2A3F5C;
    border-radius: 16px;
    padding: 6px 16px;
    font-size: 12px;
    min-height: 28px;
}
QPushButton#typeBtn:checked {
    background-color: #062025;
    color: #12A898;
    border: 1.5px solid #12A898;
    font-weight: 600;
}
QPushButton#typeBtn:hover:!checked { background-color: #1C3850; color: #D5E2EE; }

/* ── Tables ───────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0F1D2C;
    alternate-background-color: #132030;
    gridline-color: transparent;
    border: none;
    border-radius: 10px;
    font-size: 12px;
    color: #7A9EB8;
    selection-background-color: #1C3858;
    selection-color: #D5E2EE;
    outline: none;
}
QHeaderView::section {
    background-color: #172438;
    color: #4A6880;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #2A3F5C;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QTableWidget::item          { padding: 7px 10px; border: none; }
QTableCornerButton::section { background: #172438; border: none; }

/* ── Card inner labels ────────────────────────────────────────────────────── */
QLabel#WFormLabel {
    color: #4A6880;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    background: transparent;
    border: none;
}

/* ── Named text widgets ───────────────────────────────────────────────────── */
QTextEdit#ResultBox {
    background-color: #0F1D2C;
    border: 1px solid #2A3F5C;
    border-left: 3px solid #C09060;
    border-radius: 8px;
    font-family: "Cascadia Code","Consolas","Courier New",monospace;
    font-size: 12px;
    color: #8AAEC6;
    padding: 10px;
}
QTextEdit#AuditView {
    background-color: #0F1D2C;
    border: 1px solid #2A3F5C;
    border-radius: 8px;
    font-family: "Cascadia Code","Consolas","Courier New",monospace;
    font-size: 11px;
    color: #4A6880;
    padding: 8px;
}
QLabel#AlertBar {
    background-color: #2A1010;
    color: #E53E3E;
    border: 1px solid #E53E3E40;
    border-left: 3px solid #E53E3E;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 12px;
}
QLabel#OkBar {
    background-color: #0A2515;
    color: #20BB52;
    border: 1px solid #20BB5240;
    border-left: 3px solid #20BB52;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 12px;
}

/* ── Progress bars ────────────────────────────────────────────────────────── */
QProgressBar {
    background-color: #2A3F5C;
    border-radius: 5px;
    border: none;
    color: #7A9EB8;
    font-size: 11px;
    text-align: center;
}
QProgressBar::chunk { background-color: #C09060; border-radius: 5px; }

/* ── Scrollbars ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #111D2E;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical   { background: #2A3F5C; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal          { height: 6px; background: #111D2E; border-radius: 3px; }
QScrollBar::handle:horizontal  { background: #2A3F5C; border-radius: 3px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""


class MainWindow(QMainWindow):
    # Emitted when user clicks Logout — main.py listens and restarts login loop
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BioAgent  ·  Research Management System")
        self.setMinimumSize(1300, 820)
        c = QWidget()
        self.setCentralWidget(c)
        root = QVBoxLayout(c)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar: current user + logout ──────────────────────────────
        topbar = QWidget()
        topbar.setStyleSheet(
            "background:#0F1929;border-bottom:1px solid #2A3F5C;")
        topbar.setFixedHeight(40)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)

        user_lbl = QLabel(f"👤  {Session.display_label()}")
        user_lbl.setStyleSheet(
            "color:#7A9EB8;font-size:12px;background:transparent;")
        tb.addWidget(user_lbl)
        tb.addStretch()

        self.logoutBtn = QPushButton("🚪  Logout")
        self.logoutBtn.setStyleSheet(
            "QPushButton{background:#1C2D44;color:#7A9EB8;"
            "border:1px solid #2A3F5C;border-radius:14px;"
            "padding:4px 16px;font-size:11px;}"
            "QPushButton:hover{background:#243858;color:#E53E3E;"
            "border-color:#E53E3E;}")
        self.logoutBtn.clicked.connect(self._handle_logout)
        tb.addWidget(self.logoutBtn)

        root.addWidget(topbar)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs)

        # Instantiate all tabs and keep named references for signal wiring.
        self.dashboard_tab   = DashboardTab()
        self.researcher_tab  = ResearcherTab()
        self.projects_tab    = ProjectsTab()
        self.knowledge_tab   = KnowledgeTab()
        self.hypothesis_tab  = HypothesisTab()
        self.inference_tab   = InferenceTab()
        self.grant_tab       = GrantTab()

        self.tabs.addTab(self.dashboard_tab,  "📊   Lab Dashboard")
        self.tabs.addTab(self.researcher_tab, "👤   Researcher")
        self.tabs.addTab(self.projects_tab,   "📁   Research Projects")
        self.tabs.addTab(self.knowledge_tab,  "🤖   Model Skills")
        self.tabs.addTab(self.hypothesis_tab, "🧪   Hypothesis Panel")
        self.tabs.addTab(self.inference_tab,  "🧬   Molecular Inference")
        self.tabs.addTab(self.grant_tab,      "📈   Grant Management")

        # ── Cross-tab signal wiring ────────────────────────────────────────
        # ProjectsTab saves   → HypothesisTab and InferenceTab project dropdowns
        self.projects_tab.data_changed.connect(
            self.hypothesis_tab.refresh_lookups)
        self.projects_tab.data_changed.connect(
            self.inference_tab.refresh_lookups)

        # ResearcherTab saves → HypothesisTab researcher dropdown
        self.researcher_tab.data_changed.connect(
            self.hypothesis_tab.refresh_lookups)

        # KnowledgeTab saves  → InferenceTab model/skill picker
        self.knowledge_tab.data_changed.connect(
            self.inference_tab.refresh_lookups)

        self.setStyleSheet(QSS)

    # ── Logout ───────────────────────────────────────────────────────
    def _handle_logout(self):
        reply = QMessageBox.question(
            self, "Confirm Logout",
            f"Log out of {Session.current_name()}'s session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            AuditChain.log(
                user_id     = Session.res_id(),
                action      = "LOGOUT",
                entity_type = "session",
                entity_id   = Session.res_id(),
                detail      = f"role={Session.current_role()}",
                ip_owner    = "platform",
            )
        except Exception:
            pass

        Session.clear()
        self.logout_requested.emit()
        self.close()