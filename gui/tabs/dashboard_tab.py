# gui/tabs/dashboard_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from datetime import date
from gui.ui_helpers import (card, badge, hsep, scroll_wrap, prog_bar,
                            AMBER, TEAL, GREEN, RED, WARN, PURP, BLUE, ROSE,
                            TXT, TXT_S, TXT_M, MONO, SURF2, STATUS_FG)
from dao.dao_researcher  import ResearcherDAO
from dao.dao_project     import ProjectDAO
from dao.dao_hypothesis  import HypothesisDAO
from dao.dao_model_skill import ModelSkillDAO
from dao.dao_inference   import InferenceDAO
from dao.dao_grant       import GrantDAO

STATUS_FG2 = {"supported": GREEN, "refuted": RED, "pending": WARN}


# ── Sub-widgets ───────────────────────────────────────────────────────────────

class ProjectRow(QFrame):
    """One project row: title + progress bar."""
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 7, 0, 7); vl.setSpacing(5)

        title = QLabel(p.getTitle())
        title.setStyleSheet(
            f"color:{TXT};font-size:13px;font-weight:500;background:transparent;")
        vl.addWidget(title)

        row = QHBoxLayout(); row.setSpacing(10)
        color = TEAL                          # default color per project
        row.addWidget(prog_bar(p.getProgress(), color))
        pct = QLabel(f"{p.getProgress()}%")
        pct.setFixedWidth(34)
        pct.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pct.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:600;background:transparent;")
        row.addWidget(pct)
        vl.addLayout(row)


class HypCard(QFrame):
    """One hypothesis card with status colour bar."""
    def __init__(self, h):
        super().__init__()
        fg = STATUS_FG2.get(h.getStatus(), TXT_S)
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border-radius:10px;"
            f"border:none;border-left:3px solid {fg};}}")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(12, 9, 12, 9); vl.setSpacing(6)

        row = QHBoxLayout()
        row.addWidget(badge(h.getStatus(), h.getStatus()))
        row.addStretch()
        conf = QLabel(f"conf. {h.getConfidence():.2f}")
        conf.setStyleSheet(
            f"color:{TXT_M};font-size:11px;background:transparent;")
        row.addWidget(conf)
        vl.addLayout(row)

        txt = QLabel(h.getText())
        txt.setWordWrap(True)
        txt.setStyleSheet(
            f"color:{TXT_S};font-size:12px;background:transparent;")
        vl.addWidget(txt)


# ── Main tab ──────────────────────────────────────────────────────────────────

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        # -- DAO instances --
        self.researcher_dao = ResearcherDAO()
        self.project_dao    = ProjectDAO()
        self.hypothesis_dao = HypothesisDAO()
        self.skill_dao      = ModelSkillDAO()
        self.inference_dao  = InferenceDAO()
        self.grant_dao      = GrantDAO()

        _, layout = scroll_wrap(self)

        # -- Load all data from MySQL --
        try:
            projects     = self.project_dao.get_all()
            researchers  = self.researcher_dao.get_all()
            hypotheses   = self.hypothesis_dao.get_all()
            skills       = self.skill_dao.get_all()
            inferences   = self.inference_dao.get_all()
            grants       = self.grant_dao.get_all()
            milestones   = self.grant_dao.get_milestones()
            proj_titles  = self.project_dao.get_titles()
        except Exception as e:
            layout.addWidget(QLabel(f"DB Error: {e}"))
            return

        today = date.today().isoformat()

        # ── Row 1: Active Projects + Hypothesis Summary ───────────────────────
        r1 = QHBoxLayout(); r1.setSpacing(14)

        proj_c, pl = card("📁  Active Projects", border=TEAL)
        active_projects = [p for p in projects if p.isActive()]
        for i, p in enumerate(active_projects):
            pl.addWidget(ProjectRow(p))
            if i < len(active_projects) - 1:
                pl.addWidget(hsep(TEAL + "40"))
        pl.addStretch()
        r1.addWidget(proj_c, 3)

        hyp_c, hl = card("🧪  Hypothesis Summary", border=AMBER)
        counts = {"supported": 0, "refuted": 0, "pending": 0}
        for h in hypotheses:
            if h.getStatus() in counts:
                counts[h.getStatus()] += 1
        for stat, color, icon in [
            ("supported", GREEN, "✅"),
            ("refuted",   RED,   "❌"),
            ("pending",   WARN,  "⏳")
        ]:
            lbl = QLabel(f"{icon}  {stat.title()}: {counts[stat]}")
            lbl.setStyleSheet(
                f"color:{color};font-size:14px;font-weight:600;"
                f"padding:4px 0;background:transparent;")
            hl.addWidget(lbl)
        hl.addWidget(hsep(AMBER + "40"))
        for h in hypotheses:
            hl.addWidget(HypCard(h))
        hl.addStretch()
        r1.addWidget(hyp_c, 2)
        layout.addLayout(r1)

        # ── Row 2: Researchers + Active Model Skills ──────────────────────────
        r2 = QHBoxLayout(); r2.setSpacing(14)

        res_c, rl = card("👤  Registered Researchers", border=PURP)
        for i, res in enumerate(researchers):
            row = QHBoxLayout()
            id_lbl = QLabel(res.getResId())
            id_lbl.setStyleSheet(
                f"color:{TXT_M};font-size:11px;"
                f"min-width:72px;background:transparent;")
            row.addWidget(id_lbl)
            name_lbl = QLabel(res.getName())
            name_lbl.setStyleSheet(
                f"color:{TXT};font-size:12px;background:transparent;")
            row.addWidget(name_lbl); row.addStretch()
            row.addWidget(badge(
                res.getRole(),
                "amber" if res.getRole() == "lab_manager" else "active"))
            rl.addLayout(row)
            if i < len(researchers) - 1:
                rl.addWidget(hsep(PURP + "40"))
        rl.addStretch()
        r2.addWidget(res_c, 1)

        sk_c, skl = card("🤖  Active Model Skills", border=GREEN)
        active_skills = [s for s in skills if s.isActive()]
        for s in active_skills:
            row = QHBoxLayout()
            name_lbl = QLabel(s.getName())
            name_lbl.setStyleSheet(
                f"color:{TEAL};font-size:12px;"
                f"font-weight:600;background:transparent;")
            row.addWidget(name_lbl)
            lora_lbl = QLabel(s.getLoraVersion())
            lora_lbl.setStyleSheet(
                f"color:{TXT_M};font-size:11px;background:transparent;")
            row.addWidget(lora_lbl); row.addStretch()
            proj_lbl = QLabel(f"→ {s.getProjectId()}")
            proj_lbl.setStyleSheet(
                f"color:{AMBER};font-size:11px;background:transparent;")
            row.addWidget(proj_lbl)
            skl.addLayout(row)
        skl.addStretch()
        r2.addWidget(sk_c, 1)
        layout.addLayout(r2)

        # ── Row 3: Recent Inference + Grant Status ────────────────────────────
        r3 = QHBoxLayout(); r3.setSpacing(14)

        inf_c, infl = card("🔬  Recent Inference Results", border=BLUE)
        recent = inferences[:3]              # get_all() returns DESC order
        for e in recent:
            lbl = QLabel(
                f"[{e.getTimestamp()}]  {e.getType()} · {e.getInput()}")
            lbl.setStyleSheet(
                f"font-family:'Cascadia Code','Consolas',monospace;"
                f"font-size:11px;color:{MONO};"
                f"padding:2px 0;background:transparent;")
            lbl.setWordWrap(True)
            infl.addWidget(lbl)
        infl.addStretch()
        r3.addWidget(inf_c, 3)

        gr_c, grl = card("📈  Grant Status", border=ROSE)
        for g in grants:
            pct  = g.getBudgetPct()
            over = g.isOverdue()
            row  = QHBoxLayout()
            id_lbl = QLabel(
                f"{g.getGrantId()} · {g.getAgency()}")
            id_lbl.setStyleSheet(
                f"color:{RED if over else AMBER};"
                f"font-size:12px;background:transparent;")
            row.addWidget(id_lbl); row.addStretch()
            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setStyleSheet(
                f"color:{TXT_M};font-size:11px;background:transparent;")
            row.addWidget(pct_lbl)
            grl.addLayout(row)
            grl.addWidget(prog_bar(pct, RED if over else TEAL, 6))

        overdue_ms = [m for m in milestones
                      if not m.isCompleted() and m.getDue() < today]
        if overdue_ms:
            w = QLabel(f"  ⚠  {len(overdue_ms)} overdue milestone(s)")
            w.setStyleSheet(
                f"color:{RED};font-weight:600;"
                f"padding:6px 0;background:transparent;")
            grl.addWidget(w)
        grl.addStretch()
        r3.addWidget(gr_c, 2)
        layout.addLayout(r3)
        layout.addStretch()