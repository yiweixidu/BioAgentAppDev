# gui/tabs/dashboard_chart_dialogs.py
"""
Two chart dialogs triggered by double-clicking the corresponding
dashboard cards:

  ProjectProgressDialog — double-click the "📁 Active Projects" card
      Displays a bar chart of progress across all projects

  GrantSpendingDialog   — double-click the "📈 Grant Status" card
      Displays a spending timeline (spending vs. datetime) ordered
      by milestone date

Both dialogs embed matplotlib + NavigationToolbar, following the
same pattern as plot2_menu_action() in gui_main_window.py:
  FigureCanvas + NavigationToolbar2QT packed into a QVBoxLayout.
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt import NavigationToolbar2QT

from gui.tabs.dashboard_chart_canvas import (
    DashboardChartCanvas, TEAL, AMBER, GREEN, RED, TXT, TXT_M, BG, BORDER
)

_DLG_QSS = f"""
QDialog {{ background:{BG}; color:{TXT}; }}
QLabel  {{ background:transparent; color:{TXT}; }}
"""


# ══════════════════════════════════════════════════════════════
# Dialog 1 — Project Progress
# ══════════════════════════════════════════════════════════════
class ProjectProgressDialog(QDialog):
    """
    Triggered by double-clicking the Active Projects card.
    Displays a horizontal bar chart of project progress,
    color-coded by status.
    """
    STATUS_COLOR = {
        "active":   TEAL,
        "planning": AMBER,
        "archived": TXT_M,
    }

    def __init__(self, projects: list, parent=None):
        super().__init__(parent)
        self.projects = projects
        self.setWindowTitle("Project Progress Overview")
        self.setMinimumSize(760, 520)
        self.setStyleSheet(_DLG_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        hdr = QLabel("📁  Project Progress — all registered projects")
        hdr.setStyleSheet(
            f"color:{TEAL};font-size:14px;font-weight:700;")
        layout.addWidget(hdr)

        if not projects:
            empty = QLabel("No projects to display.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{TXT_M};font-size:12px;")
            layout.addWidget(empty)
            return

        self.canvas = DashboardChartCanvas(self, width=8, height=5)
        self._plot(self.canvas.axes)

        toolbar = NavigationToolbar2QT(self.canvas, self)
        toolbar.setStyleSheet(
            f"QToolBar{{background:{BG};border:none;}} "
            f"QToolButton{{color:{TXT_M};}}")

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

    def _plot(self, ax):
        # Sort by progress descending for readability
        sorted_projects = sorted(
            self.projects, key=lambda p: p.getProgress(), reverse=True)

        labels   = [f"{p.getProjId()}\n{p.getTitle()[:24]}"
                    for p in sorted_projects]
        progress = [p.getProgress() for p in sorted_projects]
        colors   = [self.STATUS_COLOR.get(p.getStatus(), TXT_M)
                    for p in sorted_projects]

        y_pos = range(len(labels))
        bars = ax.barh(y_pos, progress, color=colors, height=0.55,
                       edgecolor=BORDER, linewidth=0.8)

        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()   # highest progress on top
        ax.set_xlim(0, 100)
        ax.set_xlabel("Progress (%)")
        ax.set_title("Project Progress by Status", fontsize=11, pad=10)

        # Value labels at bar end
        for bar, val in zip(bars, progress):
            ax.text(val + 1.5, bar.get_y() + bar.get_height() / 2,
                    f"{val}%", va="center", fontsize=8, color=TXT)

        # Legend
        from matplotlib.patches import Patch
        legend_items = [
            Patch(facecolor=TEAL,  label="active"),
            Patch(facecolor=AMBER, label="planning"),
            Patch(facecolor=TXT_M, label="archived"),
        ]
        leg = ax.legend(handles=legend_items, loc="lower right",
                        fontsize=8, facecolor="#172438",
                        edgecolor=BORDER, labelcolor=TXT)

        ax.figure.tight_layout()


# ══════════════════════════════════════════════════════════════
# Dialog 2 — Grant Spending over Time
# ══════════════════════════════════════════════════════════════
class GrantSpendingDialog(QDialog):
    """
    Triggered by double-clicking the Grant Status card.
    Plots a cumulative spending timeline keyed off milestone
    due dates (milestone.due). Each grant gets its own line,
    with the deadline marked by a dashed reference line.
    """
    def __init__(self, grants: list, milestones: list, parent=None):
        super().__init__(parent)
        self.grants     = grants
        self.milestones = milestones
        self.setWindowTitle("Grant Spending Timeline")
        self.setMinimumSize(800, 540)
        self.setStyleSheet(_DLG_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        hdr = QLabel("📈  Grant Spending — budget usage over time")
        hdr.setStyleSheet(
            f"color:{TEAL};font-size:14px;font-weight:700;")
        layout.addWidget(hdr)

        if not grants:
            empty = QLabel("No grants to display.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{TXT_M};font-size:12px;")
            layout.addWidget(empty)
            return

        self.canvas = DashboardChartCanvas(self, width=8, height=5)
        self._plot(self.canvas.axes)

        toolbar = NavigationToolbar2QT(self.canvas, self)
        toolbar.setStyleSheet(
            f"QToolBar{{background:{BG};border:none;}} "
            f"QToolButton{{color:{TXT_M};}}")

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

    def _plot(self, ax):
        colors = [TEAL, AMBER, GREEN, RED, "#8A65C0", "#4A90D9"]

        for i, g in enumerate(self.grants):
            color = colors[i % len(colors)]

            # Build a simple two-point timeline: today (current usage)
            # plus the deadline, since the schema doesn't track a
            # spending history — this shows budget burn trajectory.
            today_str = datetime.now().strftime("%Y-%m-%d")
            x_dates   = [today_str, str(g.getDeadline())]
            y_used    = [float(g.getUsed()), float(g.getUsed())]

            # If this grant has milestones, plot them as markers
            g_milestones = [m for m in self.milestones
                            if m.getGrantId() == g.getGrantId()]
            if g_milestones:
                g_milestones = sorted(g_milestones, key=lambda m: m.getDue())
                m_dates = [str(m.getDue()) for m in g_milestones]
                # Approximate cumulative spend at each milestone:
                # split total 'used' proportionally by milestone order
                n = len(g_milestones)
                m_values = [
                    float(g.getUsed()) * (idx + 1) / n
                    for idx in range(n)
                ]
                x_dates = [today_str] + m_dates
                y_used  = [0.0] + m_values

            try:
                x_parsed = [datetime.strptime(d, "%Y-%m-%d") for d in x_dates]
            except Exception:
                continue

            ax.plot(x_parsed, y_used, marker="o", linewidth=2,
                   color=color, markersize=6,
                   label=f"{g.getGrantId()} · {g.getGrantType()}")

            # Total budget as a dashed reference line
            ax.axhline(float(g.getTotal()), color=color,
                      linestyle="--", linewidth=0.8, alpha=0.4)

        ax.set_xlabel("Date")
        ax.set_ylabel("Amount Spent (CAD)")
        ax.set_title("Grant Spending vs. Milestone Timeline",
                     fontsize=11, pad=10)
        ax.legend(loc="upper left", fontsize=8,
                 facecolor="#172438", edgecolor=BORDER, labelcolor=TXT)
        ax.figure.autofmt_xdate(rotation=30)
        ax.figure.tight_layout()