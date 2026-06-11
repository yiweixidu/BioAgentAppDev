# dashboard_tab.py – Whimsigoth v2
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from datetime import date
from ui_helpers import (card, badge, hsep, scroll_wrap, prog_bar,
                        AMBER, TEAL, GREEN, RED, WARN, PURP, BLUE, ROSE,
                        TXT, TXT_S, TXT_M, MONO, SURF2, STATUS_FG)
from mock_data import (projects, researchers, model_skills, hypotheses,
                       inference_history, grants, milestones,
                       get_hypothesis_counts)

PROJ_COLORS = {"PRJ-101": TEAL, "PRJ-102": WARN, "PRJ-103": GREEN}
STATUS_FG2  = {"supported": GREEN, "refuted": RED, "pending": WARN}


class ProjectRow(QFrame):
    def __init__(self, p):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")
        vl = QVBoxLayout(self); vl.setContentsMargins(0,7,0,7); vl.setSpacing(5)
        title = QLabel(p["title"])
        title.setStyleSheet(f"color:{TXT};font-size:13px;font-weight:500;background:transparent;")
        vl.addWidget(title)
        row = QHBoxLayout(); row.setSpacing(10)
        color = PROJ_COLORS.get(p["id"], TEAL)
        row.addWidget(prog_bar(p.get("progress", 0), color))
        pct = QLabel(f"{p.get('progress',0)}%")
        pct.setFixedWidth(34)
        pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pct.setStyleSheet(f"color:{color};font-size:11px;font-weight:600;background:transparent;")
        row.addWidget(pct)
        vl.addLayout(row)


class HypCard(QFrame):
    def __init__(self, h):
        super().__init__()
        status = h["status"]
        fg = STATUS_FG2.get(status, TXT_S)
        self.setStyleSheet(
            f"QFrame{{background:{SURF2};border-radius:10px;"
            f"border:none;border-left:3px solid {fg};}}")
        vl = QVBoxLayout(self); vl.setContentsMargins(12,9,12,9); vl.setSpacing(6)
        row = QHBoxLayout()
        row.addWidget(badge(status, status)); row.addStretch()
        conf = QLabel(f"conf. {h['confidence']:.2f}")
        conf.setStyleSheet(f"color:{TXT_M};font-size:11px;background:transparent;")
        row.addWidget(conf)
        vl.addLayout(row)
        txt = QLabel(h["text"])
        txt.setWordWrap(True)
        txt.setStyleSheet(f"color:{TXT_S};font-size:12px;background:transparent;")
        vl.addWidget(txt)


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        _, layout = scroll_wrap(self)

        # Row 1
        r1 = QHBoxLayout(); r1.setSpacing(14)
        proj_c, pl = card("📁  Active Projects", border=TEAL)
        for i, p in enumerate(projects):
            pl.addWidget(ProjectRow(p))
            if i < len(projects)-1: pl.addWidget(hsep(TEAL+"40"))
        pl.addStretch()
        r1.addWidget(proj_c, 3)

        hyp_c, hl = card("🧪  Hypothesis Summary", border=AMBER)
        counts = get_hypothesis_counts()
        for stat, color, icon in [("supported",GREEN,"✅"),("refuted",RED,"❌"),("pending",WARN,"⏳")]:
            lbl = QLabel(f"{icon}  {stat.title()}: {counts[stat]}")
            lbl.setStyleSheet(f"color:{color};font-size:14px;font-weight:600;"
                              f"padding:4px 0;background:transparent;")
            hl.addWidget(lbl)
        hl.addWidget(hsep(AMBER+"40"))
        for h in hypotheses: hl.addWidget(HypCard(h))
        hl.addStretch()
        r1.addWidget(hyp_c, 2)
        layout.addLayout(r1)

        # Row 2
        r2 = QHBoxLayout(); r2.setSpacing(14)
        res_c, rl = card("👤  Registered Researchers", border=PURP)
        for i, r in enumerate(researchers):
            row = QHBoxLayout()
            id_lbl = QLabel(r["id"])
            id_lbl.setStyleSheet(f"color:{TXT_M};font-size:11px;min-width:72px;background:transparent;")
            row.addWidget(id_lbl)
            name = QLabel(r["name"])
            name.setStyleSheet(f"color:{TXT};font-size:12px;background:transparent;")
            row.addWidget(name); row.addStretch()
            row.addWidget(badge(r["role"], "amber" if r["role"]=="lab_manager" else "active"))
            rl.addLayout(row)
            if i < len(researchers)-1: rl.addWidget(hsep(PURP+"40"))
        rl.addStretch()
        r2.addWidget(res_c, 1)

        sk_c, skl = card("🤖  Active Model Skills", border=GREEN)
        for s in [x for x in model_skills if x["status"]=="active"]:
            row = QHBoxLayout()
            name = QLabel(s["name"])
            name.setStyleSheet(f"color:{TEAL};font-size:12px;font-weight:600;background:transparent;")
            row.addWidget(name)
            lora = QLabel(s["lora_version"])
            lora.setStyleSheet(f"color:{TXT_M};font-size:11px;background:transparent;")
            row.addWidget(lora); row.addStretch()
            proj = QLabel(f"→ {s['project_id']}")
            proj.setStyleSheet(f"color:{AMBER};font-size:11px;background:transparent;")
            row.addWidget(proj)
            skl.addLayout(row)
        skl.addStretch()
        r2.addWidget(sk_c, 1)
        layout.addLayout(r2)

        # Row 3
        r3 = QHBoxLayout(); r3.setSpacing(14)
        inf_c, infl = card("🔬  Recent Inference Results", border=BLUE)
        for e in list(reversed(inference_history[-3:])) if inference_history else []:
            txt = QLabel(f"[{e['timestamp']}]  {e['type']} · {e['input']}")
            txt.setStyleSheet(
                f"font-family:'Cascadia Code','Consolas',monospace;"
                f"font-size:11px;color:{MONO};padding:2px 0;background:transparent;")
            txt.setWordWrap(True)
            infl.addWidget(txt)
        infl.addStretch()
        r3.addWidget(inf_c, 3)

        today = date.today().isoformat()
        gr_c, grl = card("📈  Grant Status", border=ROSE)
        for g in grants:
            pct = int(g["used"]/g["total"]*100)
            over = g["deadline"] < today
            row = QHBoxLayout()
            id_lbl = QLabel(f"{g['id']} · {g['agency']}")
            id_lbl.setStyleSheet(
                f"color:{RED if over else AMBER};font-size:12px;background:transparent;")
            row.addWidget(id_lbl); row.addStretch()
            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setStyleSheet(f"color:{TXT_M};font-size:11px;background:transparent;")
            row.addWidget(pct_lbl)
            grl.addLayout(row)
            grl.addWidget(prog_bar(pct, RED if over else TEAL, 6))
        overdue = [m for m in milestones if not m["completed"] and m["due"] < today]
        if overdue:
            w = QLabel(f"  ⚠  {len(overdue)} overdue milestone(s)")
            w.setStyleSheet(f"color:{RED};font-weight:600;padding:6px 0;background:transparent;")
            grl.addWidget(w)
        grl.addStretch()
        r3.addWidget(gr_c, 2)
        layout.addLayout(r3)
        layout.addStretch()
