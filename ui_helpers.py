# ui_helpers.py – Whimsigoth palette v2 (lighter BG + vivid card borders)
from PyQt6.QtWidgets import (QFrame, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QHeaderView, QAbstractItemView,
                             QScrollArea, QSizePolicy, QProgressBar)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

# ── Palette (adjusted: lighter background) ────────────────────────────────────
BG     = "#111D2E"   # dark navy – visible, not pitch black
SURF   = "#1C2D44"   # card surface
SURF2  = "#172438"   # deeper surface / input bg
INP    = "#0F1D2C"   # input fields
BORDER = "#2A3F5C"   # default subtle border
# Vivid accent colours used as card borders & badges
AMBER  = "#C09060"   # warm gold
TEAL   = "#12A898"   # teal
GREEN  = "#20BB52"   # emerald
RED    = "#E53E3E"   # ruby
WARN   = "#E8960A"   # amber warning
PURP   = "#8A65C0"   # violet
BLUE   = "#4A90D9"   # sapphire
ROSE   = "#E05580"   # rose
# Text
TXT    = "#D5E2EE"   # primary
TXT_S  = "#7A9EB8"   # secondary
TXT_M  = "#4A6880"   # muted labels
MONO   = "#8AAEC6"   # monospace data

# Status maps
STATUS_FG = {"supported":GREEN,"refuted":RED,"pending":WARN,
             "active":TEAL,"inactive":TXT_M,"planning":PURP}
STATUS_BG = {"supported":"#0A2015","refuted":"#200A0A","pending":"#1A1204",
             "active":"#061818","inactive":"#1A2030","planning":"#100C1A"}
STATUS_BORDER = {k: v+"60" for k, v in STATUS_FG.items()}
STATUS_ROW_BG = {"supported":QColor("#0D2518"),"refuted":QColor("#250D0D"),
                 "pending":QColor("#201804")}


# ── Card factory  (key change: vivid border per card) ─────────────────────────
def card(title: str = "", accent: str = AMBER, border: str = None):
    """
    Whimsigoth card with vivid coloured border.
    border: any hex colour — e.g. TEAL, PURP, ROSE …
    Returns (outer QFrame, content QVBoxLayout).
    """
    bc = border or BORDER          # vivid or subtle
    outer = QFrame()
    # Each card gets its own inline style so borders can differ
    outer.setStyleSheet(f"""
        QFrame {{
            background-color: {SURF};
            border: 1.5px solid {bc};
            border-radius: 14px;
        }}
    """)
    ol = QVBoxLayout(outer)
    ol.setContentsMargins(0, 0, 0, 0)
    ol.setSpacing(0)

    if title:
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background-color: {SURF2};
                border: none;
                border-top-left-radius: 13px;
                border-top-right-radius: 13px;
                border-bottom: 1px solid {bc}50;
            }}
        """)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 11, 16, 11)
        hl.setSpacing(10)
        acc = QFrame()
        acc.setFixedSize(3, 14)
        acc.setStyleSheet(f"background:{bc};border-radius:2px;border:none;")
        hl.addWidget(acc)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color:{TXT};font-size:13px;font-weight:600;"
                          f"background:transparent;border:none;")
        hl.addWidget(lbl)
        hl.addStretch()
        ol.addWidget(hdr)

    body = QWidget()
    body.setStyleSheet("background:transparent;border:none;")
    cl = QVBoxLayout(body)
    cl.setContentsMargins(16, 14, 16, 14)
    cl.setSpacing(10)
    ol.addWidget(body)
    return outer, cl


# ── Badge ─────────────────────────────────────────────────────────────────────
def badge(text: str, variant: str = "default") -> QLabel:
    fg  = STATUS_FG.get(variant, TXT_S)
    bg  = STATUS_BG.get(variant, SURF2)
    brd = STATUS_BORDER.get(variant, BORDER)
    lbl = QLabel(text.upper())
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedHeight(22)
    lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    lbl.setContentsMargins(14, 0, 14, 0)
    lbl.setStyleSheet(f"QLabel{{background:{bg};color:{fg};"
                      f"border:1px solid {brd};border-radius:11px;"
                      f"font-size:11px;font-weight:700;letter-spacing:0.5px;}}")
    return lbl


# ── Separator ─────────────────────────────────────────────────────────────────
def hsep(color: str = None) -> QFrame:
    s = QFrame()
    s.setFrameShape(QFrame.Shape.HLine)
    s.setStyleSheet(f"background:{color or BORDER};max-height:1px;border:none;")
    return s


# ── Scroll wrapper ────────────────────────────────────────────────────────────
def scroll_wrap(tab: QWidget, spacing: int = 14, m=(10, 10, 10, 10)):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
    container = QWidget()
    container.setStyleSheet("background:transparent;")
    layout = QVBoxLayout(container)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*m)
    scroll.setWidget(container)
    ol = QVBoxLayout(tab)
    ol.setContentsMargins(0, 0, 0, 0)
    ol.addWidget(scroll)
    return container, layout


# ── Table ─────────────────────────────────────────────────────────────────────
def setup_table(tbl: QTableWidget, headers: list, stretch: int = -1):
    tbl.setColumnCount(len(headers))
    tbl.setHorizontalHeaderLabels(headers)
    tbl.setAlternatingRowColors(True)
    tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tbl.verticalHeader().setVisible(False)
    tbl.setShowGrid(False)
    hdr = tbl.horizontalHeader()
    hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    col = stretch if stretch >= 0 else len(headers) - 1
    hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
    tbl.setMinimumHeight(140)


def titem(text: str, color: str = None, bg: str = None):
    from PyQt6.QtWidgets import QTableWidgetItem
    it = QTableWidgetItem(str(text))
    if color: it.setForeground(QBrush(QColor(color)))
    if bg:    it.setBackground(QBrush(QColor(bg)))
    return it


# ── Form helpers ──────────────────────────────────────────────────────────────
def flbl(text: str) -> QLabel:
    l = QLabel(text.upper())
    l.setObjectName("WFormLabel")
    return l

def fgroup(label: str, widget: QWidget) -> QVBoxLayout:
    vl = QVBoxLayout()
    vl.setSpacing(4)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.addWidget(flbl(label))
    vl.addWidget(widget)
    return vl

def form_row(*pairs) -> "QGridLayout":
    from PyQt6.QtWidgets import QGridLayout
    g = QGridLayout()
    g.setSpacing(10); g.setContentsMargins(0, 0, 0, 0)
    for i, (lbl_txt, widget) in enumerate(pairs):
        col = QVBoxLayout(); col.setSpacing(4); col.setContentsMargins(0,0,0,0)
        col.addWidget(flbl(lbl_txt)); col.addWidget(widget)
        g.addLayout(col, 0, i); g.setColumnStretch(i, 1)
    return g


# ── Progress bar ──────────────────────────────────────────────────────────────
def prog_bar(value: int, color: str = TEAL, height: int = 8) -> QProgressBar:
    b = QProgressBar()
    b.setRange(0, 100); b.setValue(value)
    b.setTextVisible(False); b.setFixedHeight(height)
    r = height // 2
    b.setStyleSheet(
        f"QProgressBar{{background:{BORDER};border-radius:{r}px;border:none;}}"
        f"QProgressBar::chunk{{background:{color};border-radius:{r}px;}}")
    return b
