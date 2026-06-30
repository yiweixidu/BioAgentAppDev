# gui/tabs/dashboard_chart_canvas.py
"""
Matplotlib canvas embedded in PyQt6, styled to match Whimsigoth dashboard.
Follows the same pattern as map_canvas_plot.py:
  FigureCanvasQTAgg subclass exposing self.axes for direct plotting.
"""
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Whimsigoth palette (matches ui_helpers.py)
BG     = "#111D2E"
SURF2  = "#172438"
TEAL   = "#12A898"
AMBER  = "#C09060"
GREEN  = "#20BB52"
RED    = "#E53E3E"
TXT    = "#D5E2EE"
TXT_M  = "#4A6880"
BORDER = "#2A3F5C"


class DashboardChartCanvas(FigureCanvas):
    """
    Dark-themed matplotlib canvas for embedding in dialogs.
    self.axes is the primary subplot — caller plots directly on it.
    """
    def __init__(self, parent=None, width=7, height=4.2, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor(BG)

        self.axes = fig.add_subplot(111)
        self._style_axes(self.axes)

        super().__init__(fig)
        self.setParent(parent)

    def _style_axes(self, ax):
        """Apply Whimsigoth dark styling to a matplotlib Axes."""
        ax.set_facecolor(SURF2)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        ax.tick_params(colors=TXT_M, labelsize=9)
        ax.xaxis.label.set_color(TXT)
        ax.yaxis.label.set_color(TXT)
        ax.title.set_color(TXT)
        ax.grid(True, color=BORDER, alpha=0.4, linewidth=0.6)