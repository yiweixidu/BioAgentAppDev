# gui/tabs/dashboard_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame)
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

STATUS_FG2 = {'supported': GREEN, 'refuted': RED, 'pending': WARN}


# ── Sub-widgets ───────────────────────────────────────────────────────────────

class StatCard(QFrame):
    """
    One stat tile in the Lab Overview card.
    Mirrors the HTML .stat-card: large teal number + muted uppercase label.
    """
    def __init__(self, value: str, label: str):
        super().__init__()
        self.setStyleSheet(
            f'QFrame{{background:{SURF2};border-radius:10px;border:none;}}')
        self.setMinimumWidth(110)

        num_lbl = QLabel(str(value))
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_lbl.setStyleSheet(
            f'color:{TEAL};font-size:28px;font-weight:700;background:transparent;')

        lbl_lbl = QLabel(label.upper())
        lbl_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_lbl.setStyleSheet(
            f'color:{TXT_M};font-size:10px;font-weight:700;'
            f'letter-spacing:0.6px;background:transparent;')

        vl = QVBoxLayout(self)
        vl.setContentsMargins(14, 14, 14, 14)
        vl.setSpacing(4)
        vl.addWidget(num_lbl)
        vl.addWidget(lbl_lbl)


class ProjectRow(QFrame):
    """One project row: title + progress bar."""
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet('background:transparent;border:none;')

        self.titleLbl = QLabel(p.getTitle())
        self.titleLbl.setStyleSheet(
            f'color:{TXT};font-size:13px;font-weight:500;background:transparent;')
        self.pctLbl = QLabel(f'{p.getProgress()}%')
        self.pctLbl.setFixedWidth(34)
        self.pctLbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.pctLbl.setStyleSheet(
            f'color:{TEAL};font-size:11px;font-weight:600;background:transparent;')

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 7, 0, 7); vl.setSpacing(5)
        vl.addWidget(self.titleLbl)
        row = QHBoxLayout(); row.setSpacing(10)
        row.addWidget(prog_bar(p.getProgress(), TEAL))
        row.addWidget(self.pctLbl)
        vl.addLayout(row)


class HypCard(QFrame):
    """One hypothesis card with status colour bar."""
    def __init__(self, h):
        super().__init__()
        fg = STATUS_FG2.get(h.getStatus(), TXT_S)
        self.setStyleSheet(
            f'QFrame{{background:{SURF2};border-radius:10px;'
            f'border:none;border-left:3px solid {fg};}}')

        self.confLbl = QLabel(f'conf. {h.getConfidence():.2f}')
        self.confLbl.setStyleSheet(
            f'color:{TXT_M};font-size:11px;background:transparent;')
        self.txtLbl = QLabel(h.getText())
        self.txtLbl.setWordWrap(True)
        self.txtLbl.setStyleSheet(
            f'color:{TXT_S};font-size:12px;background:transparent;')

        vl = QVBoxLayout(self)
        vl.setContentsMargins(12, 9, 12, 9); vl.setSpacing(6)
        row = QHBoxLayout()
        row.addWidget(badge(h.getStatus(), h.getStatus()))
        row.addStretch()
        row.addWidget(self.confLbl)
        vl.addLayout(row)
        vl.addWidget(self.txtLbl)


# ── Main tab ──────────────────────────────────────────────────────────────────

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.researcher_dao = ResearcherDAO()
        self.project_dao    = ProjectDAO()
        self.hypothesis_dao = HypothesisDAO()
        self.skill_dao      = ModelSkillDAO()
        self.inference_dao  = InferenceDAO()
        self.grant_dao      = GrantDAO()

        # ------------Load data------------
        _, layout = scroll_wrap(self)
        try:
            projects    = self.project_dao.get_all()
            researchers = self.researcher_dao.get_all()
            hypotheses  = self.hypothesis_dao.get_all()
            skills      = self.skill_dao.get_all()
            inferences  = self.inference_dao.get_all()
            grants      = self.grant_dao.get_all()
            milestones  = self.grant_dao.get_milestones()
        except Exception as e:
            layout.addWidget(QLabel(f'DB Error: {e}')); return

        today = date.today().isoformat()
        active_skills = [s for s in skills if s.isActive()]

        # ── Row 0: Lab Overview stat card (NEW) ──────────────────────────────
        # Mirrors the HTML dashboard .stat-grid with 5 tiles:
        # Projects · Researchers · Active Skills · Inference Jobs · Grants
        overview_c, ol = card('📊  Lab Overview', border=ROSE)
        stat_row = QHBoxLayout()
        stat_row.setSpacing(12)
        for value, label in [
            (len(projects),    'Projects'),
            (len(researchers), 'Researchers'),
            (len(active_skills), 'Active Skills'),
            (len(inferences),  'Inference Jobs'),
            (len(grants),      'Grants'),
        ]:
            stat_row.addWidget(StatCard(value, label))
        ol.addLayout(stat_row)
        layout.addWidget(overview_c)

        # ── Row 1: Active Projects + Hypothesis Summary ───────────────────────
        r1 = QHBoxLayout(); r1.setSpacing(14)

        proj_c, pl = card('📁  Active Projects', border=TEAL)
        active = [p for p in projects if p.isActive()]
        for i, p in enumerate(active):
            pl.addWidget(ProjectRow(p))
            if i < len(active) - 1: pl.addWidget(hsep(TEAL + '40'))
        pl.addStretch()
        r1.addWidget(proj_c, 3)

        hyp_c, hl = card('🧪  Hypothesis Summary', border=AMBER)
        counts = {'supported': 0, 'refuted': 0, 'pending': 0}
        for h in hypotheses:
            if h.getStatus() in counts: counts[h.getStatus()] += 1
        hyp_stat_row = QHBoxLayout()
        hyp_stat_row.setSpacing(0)
        for stat, color, icon in [
            ('supported', GREEN, '✅'),
            ('refuted',   RED,   '❌'),
            ('pending',   WARN,  '⏳'),
        ]:
            lbl = QLabel(f'{icon}  {stat.title()}: {counts[stat]}')
            lbl.setStyleSheet(
                f'color:{color};font-size:14px;font-weight:600;'
                f'padding:4px 0;background:transparent;')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hyp_stat_row.addStretch(1)
            hyp_stat_row.addWidget(lbl)
        hyp_stat_row.addStretch(1)
        hl.addLayout(hyp_stat_row)
        hl.addWidget(hsep(AMBER + '40'))
        for h in hypotheses:
            hl.addWidget(HypCard(h))
        hl.addStretch()
        r1.addWidget(hyp_c, 2)
        layout.addLayout(r1)

        # ── Row 2: Registered Researchers + Active Skills ─────────────────────
        r2 = QHBoxLayout(); r2.setSpacing(14)

        res_c, rl = card('👤  Registered Researchers', border=PURP)
        for i, res in enumerate(researchers):
            row = QHBoxLayout()
            id_lbl = QLabel(res.getResId())
            id_lbl.setStyleSheet(
                f'color:{TXT_M};font-size:11px;min-width:72px;background:transparent;')
            row.addWidget(id_lbl)
            name_lbl = QLabel(res.getName())
            name_lbl.setStyleSheet(
                f'color:{TXT};font-size:12px;background:transparent;')
            row.addWidget(name_lbl); row.addStretch()
            row.addWidget(badge(res.getRole(),
                'amber' if res.getRole() == 'lab_manager' else 'active'))
            rl.addLayout(row)
            if i < len(researchers) - 1: rl.addWidget(hsep(PURP + '40'))
        rl.addStretch()
        r2.addWidget(res_c, 1)

        sk_c, skl = card('🤖  Active Model Skills', border=GREEN)
        for s in active_skills:
            row = QHBoxLayout()
            name_lbl = QLabel(s.getName())
            name_lbl.setStyleSheet(
                f'color:{TEAL};font-size:12px;font-weight:600;background:transparent;')
            row.addWidget(name_lbl)
            lora_lbl = QLabel(s.getLoraVersion())
            lora_lbl.setStyleSheet(
                f'color:{TXT_M};font-size:11px;background:transparent;')
            row.addWidget(lora_lbl); row.addStretch()
            proj_lbl = QLabel(f'→ {s.getProjectId()}')
            proj_lbl.setStyleSheet(
                f'color:{AMBER};font-size:11px;background:transparent;')
            row.addWidget(proj_lbl)
            skl.addLayout(row)
        skl.addStretch()
        r2.addWidget(sk_c, 1)
        layout.addLayout(r2)

        # ── Row 3: Recent Inference Results + Grant Status ────────────────────
        r3 = QHBoxLayout(); r3.setSpacing(14)

        inf_c, infl = card('🔬  Recent Inference Results', border=BLUE)
        for e in inferences[:3]:
            lbl = QLabel(f'[{e.getTimestamp()}]  {e.getType()} · {e.getInput()}')
            lbl.setStyleSheet(
                f"font-family:'Cascadia Code','Consolas',monospace;"
                f'font-size:11px;color:{MONO};padding:2px 0;background:transparent;')
            lbl.setWordWrap(True)
            infl.addWidget(lbl)
        infl.addStretch()
        r3.addWidget(inf_c, 3)

        gr_c, grl = card('📈  Grant Status', border=RED)
        for g in grants:
            pct  = g.getBudgetPct()
            over = g.isOverdue()
            row  = QHBoxLayout()
            id_lbl = QLabel(f'{g.getGrantId()} · {g.getGrantType()}')
            id_lbl.setStyleSheet(
                f'color:{RED if over else AMBER};'
                f'font-size:12px;background:transparent;')
            row.addWidget(id_lbl); row.addStretch()
            pct_lbl = QLabel(f'{pct}%')
            pct_lbl.setStyleSheet(
                f'color:{TXT_M};font-size:11px;background:transparent;')
            row.addWidget(pct_lbl)
            grl.addLayout(row)
            grl.addWidget(prog_bar(pct, RED if over else TEAL, 6))

        overdue_ms = [m for m in milestones
                      if not m.isCompleted() and m.getDue() < today]
        if overdue_ms:
            w = QLabel(f'  ⚠  {len(overdue_ms)} overdue milestone(s)')
            w.setStyleSheet(
                f'color:{RED};font-weight:600;padding:6px 0;background:transparent;')
            grl.addWidget(w)
        grl.addStretch()
        r3.addWidget(gr_c, 2)
        layout.addLayout(r3)

        layout.addStretch()