# grant_tab.py – BP6 Whimsigoth v2
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QProgressBar)
from PyQt6.QtGui import QColor, QBrush
from datetime import date
from ui_helpers import card, scroll_wrap, setup_table, fgroup, prog_bar, AMBER, TEAL, GREEN, RED, BLUE, ROSE, TXT_M
from mock_data import grants, milestones, add_audit, get_project_title

class GrantTab(QWidget):
    def __init__(self):
        super().__init__()
        _, layout = scroll_wrap(self)

        self.alert = QLabel(); self.alert.setWordWrap(True)
        layout.addWidget(self.alert)

        gr_c, gl = card("📅  Active Grants", border=TEAL)
        self.gr_tbl = QTableWidget()
        setup_table(self.gr_tbl,
            ["Grant ID","Project","Agency","Deadline","Budget Used","Total","Milestone %"],1)
        self.gr_tbl.setMinimumHeight(120); gl.addWidget(self.gr_tbl)
        ex_r = QHBoxLayout()
        self.exp_btn = QPushButton("📄  Export Report  (DOCX mock)")
        self.exp_btn.clicked.connect(self._export)
        ex_r.addWidget(self.exp_btn); ex_r.addStretch(); gl.addLayout(ex_r)
        layout.addWidget(gr_c)

        ms_c, ml = card("📌  Milestones", border=AMBER)
        self.ms_tbl = QTableWidget()
        setup_table(self.ms_tbl,["Grant","Description","Due Date","Completed"],1)
        self.ms_tbl.setMinimumHeight(110); ml.addWidget(self.ms_tbl)
        mk_r = QHBoxLayout(); mk_r.setSpacing(10)
        self.ms_sel = QLineEdit(); self.ms_sel.setPlaceholderText("Row number (1-based)")
        mk_btn = QPushButton("✔  Mark Complete"); mk_btn.setObjectName("primaryButton")
        mk_btn.clicked.connect(self._mark_done)
        mk_r.addLayout(fgroup("Row", self.ms_sel)); mk_r.addWidget(mk_btn); mk_r.addStretch()
        ml.addLayout(mk_r); layout.addWidget(ms_c)

        add_c, al = card("➕  Add Milestone", border=BLUE)
        self.f_grant = QComboBox()
        for g in grants:
            self.f_grant.addItem(f"{g['id']} — {get_project_title(g['project_id'])}", g["id"])
        self.f_desc = QLineEdit(); self.f_desc.setPlaceholderText("Milestone description")
        self.f_due  = QLineEdit(); self.f_due.setPlaceholderText("YYYY-MM-DD")
        r1 = QHBoxLayout(); r1.setSpacing(12)
        r1.addLayout(fgroup("Grant", self.f_grant))
        r1.addLayout(fgroup("Description", self.f_desc)); al.addLayout(r1)
        r2 = QHBoxLayout(); r2.setSpacing(12)
        r2.addLayout(fgroup("Due Date", self.f_due)); r2.addStretch(); al.addLayout(r2)
        r3 = QHBoxLayout()
        add_btn = QPushButton("✚  Add Milestone  (audit logged)"); add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add); r3.addWidget(add_btn); r3.addStretch()
        al.addLayout(r3); layout.addWidget(add_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        today = date.today().isoformat()
        over = [m["desc"] for m in milestones if not m["completed"] and m["due"] < today]
        if over:
            self.alert.setObjectName("AlertBar")
            self.alert.setText(f"⚠  Overdue: {' · '.join(over)}")
        else:
            self.alert.setObjectName("OkBar")
            self.alert.setText("✅  No overdue milestones")
        self.alert.setStyleSheet(self.alert.styleSheet())

        self.gr_tbl.setRowCount(len(grants))
        for r,g in enumerate(grants):
            pct=int(g["used"]/g["total"]*100); over_g=g["deadline"]<today
            for c,v in enumerate([g["id"],get_project_title(g["project_id"]),g["agency"],
                                   g["deadline"],f"${g['used']:,}",f"${g['total']:,}",""]):
                if c==6: continue
                it=QTableWidgetItem(str(v))
                if c==3 and over_g: it.setForeground(QBrush(QColor(RED)))
                elif c==2: it.setForeground(QBrush(QColor(AMBER)))
                self.gr_tbl.setItem(r,c,it)
            bar=prog_bar(pct, RED if over_g else TEAL, 10)
            bar.setTextVisible(True); bar.setFormat(f" {pct}%")
            self.gr_tbl.setCellWidget(r,6,bar); self.gr_tbl.setRowHeight(r,34)

        self.ms_tbl.setRowCount(len(milestones))
        for r,m in enumerate(milestones):
            overdue = not m["completed"] and m["due"]<today
            for c,v in enumerate([m["grant_id"],m["desc"],m["due"],
                                   "✔ Done" if m["completed"] else ("⚠ Overdue" if overdue else "—")]):
                it=QTableWidgetItem(str(v))
                if c==3: it.setForeground(QBrush(QColor(GREEN if m["completed"] else RED if overdue else TXT_M)))
                elif c==2 and overdue: it.setForeground(QBrush(QColor(RED)))
                self.ms_tbl.setItem(r,c,it)

    def _mark_done(self):
        txt=self.ms_sel.text().strip()
        try: idx=int(txt)-1; assert 0<=idx<len(milestones)
        except: QMessageBox.warning(self,"Invalid",f"Enter 1–{len(milestones)}."); return
        milestones[idx]["completed"]=True
        add_audit("system","MILESTONE_DONE",milestones[idx]["grant_id"],milestones[idx]["desc"])
        self._refresh(); self.ms_sel.clear()
        QMessageBox.information(self,"Done","Milestone completed.")

    def _add(self):
        desc=self.f_desc.text().strip(); due=self.f_due.text().strip()
        if not desc or not due: QMessageBox.warning(self,"Validation","Description and due date required."); return
        gid=self.f_grant.currentData()
        milestones.append({"grant_id":gid,"desc":desc,"due":due,"completed":False})
        add_audit("system","ADD_MILESTONE",gid,desc)
        self._refresh(); self.f_desc.clear(); self.f_due.clear()
        QMessageBox.information(self,"Added","Milestone added.")

    def _export(self):
        QMessageBox.information(self,"Export","DOCX report generation triggered (mock mode).")
