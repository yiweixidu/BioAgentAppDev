# gui/tabs/grant_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QComboBox)
from PyQt6.QtGui import QColor, QBrush
from datetime import date
from gui.ui_helpers import (card, scroll_wrap, setup_table, fgroup,
                            prog_bar, AMBER, TEAL, GREEN, RED, BLUE, TXT_M)
from dao.dao_grant   import GrantDAO
from dao.dao_project import ProjectDAO
from dao.dao_audit   import AuditDAO
from models.grant_fund import Grant
from models.milestone  import Milestone


class GrantTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dao         = GrantDAO()
        self.project_dao = ProjectDAO()
        self.audit_dao   = AuditDAO()
        _, layout = scroll_wrap(self)

        self.alert = QLabel(); self.alert.setWordWrap(True)
        layout.addWidget(self.alert)

        gr_c, gl = card("📅  Active Grants", border=TEAL)
        self.gr_tbl = QTableWidget()
        setup_table(self.gr_tbl,
            ["Grant ID","Project","Agency","Deadline",
             "Budget Used","Total","Milestone %"], 1)
        self.gr_tbl.setMinimumHeight(120); gl.addWidget(self.gr_tbl)
        ex_r = QHBoxLayout()
        self.exp_btn = QPushButton("📄  Export Report  (DOCX mock)")
        self.exp_btn.clicked.connect(self._export)
        ex_r.addWidget(self.exp_btn); ex_r.addStretch()
        gl.addLayout(ex_r); layout.addWidget(gr_c)

        ms_c, ml = card("📌  Milestones", border=AMBER)
        self.ms_tbl = QTableWidget()
        setup_table(self.ms_tbl,
            ["ID","Grant","Description","Due Date","Completed"], 2)
        self.ms_tbl.setMinimumHeight(110); ml.addWidget(self.ms_tbl)
        mk_r = QHBoxLayout(); mk_r.setSpacing(10)
        self.ms_sel = QLineEdit()
        self.ms_sel.setPlaceholderText("Milestone ID")
        mk_btn = QPushButton("✔  Mark Complete")
        mk_btn.setObjectName("primaryButton")
        mk_btn.clicked.connect(self._mark_done)
        mk_r.addLayout(fgroup("Milestone ID", self.ms_sel))
        mk_r.addWidget(mk_btn); mk_r.addStretch()
        ml.addLayout(mk_r); layout.addWidget(ms_c)

        add_c, al = card("➕  Add Milestone", border=BLUE)
        self.f_grant = QComboBox()
        try:
            titles = self.project_dao.get_titles()
            for g in self.dao.get_all():
                self.f_grant.addItem(
                    f"{g.getGrantId()} — "
                    f"{titles.get(g.getProjectId(), g.getProjectId())}",
                    g.getGrantId())
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e))
        self.f_desc = QLineEdit()
        self.f_desc.setPlaceholderText("Milestone description")
        self.f_due  = QLineEdit()
        self.f_due.setPlaceholderText("YYYY-MM-DD")
        r1 = QHBoxLayout(); r1.setSpacing(12)
        r1.addLayout(fgroup("Grant",       self.f_grant))
        r1.addLayout(fgroup("Description", self.f_desc))
        al.addLayout(r1)
        r2 = QHBoxLayout(); r2.setSpacing(12)
        r2.addLayout(fgroup("Due Date", self.f_due)); r2.addStretch()
        al.addLayout(r2)
        r3 = QHBoxLayout()
        add_btn = QPushButton("✚  Add Milestone  (audit logged)")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add)
        r3.addWidget(add_btn); r3.addStretch()
        al.addLayout(r3); layout.addWidget(add_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        try:
            grants     = self.dao.get_all()
            milestones = self.dao.get_milestones()
            titles     = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return

        today = date.today().isoformat()
        overdue = [m.getDesc() for m in milestones
                   if not m.isCompleted() and m.getDue() < today]
        if overdue:
            self.alert.setObjectName("AlertBar")
            self.alert.setText(f"⚠  Overdue: {' · '.join(overdue)}")
        else:
            self.alert.setObjectName("OkBar")
            self.alert.setText("✅  No overdue milestones")
        self.alert.setStyleSheet(self.alert.styleSheet())

        self.gr_tbl.setRowCount(len(grants))
        for r, g in enumerate(grants):
            pct    = g.getBudgetPct()
            over_g = g.isOverdue()
            for c, v in enumerate([
                g.getGrantId(),
                titles.get(g.getProjectId(), g.getProjectId()),
                g.getAgency(), g.getDeadline(),
                f"${g.getUsed():,.0f}", f"${g.getTotal():,.0f}", ""
            ]):
                if c == 6: continue
                it = QTableWidgetItem(str(v))
                if c == 3 and over_g:
                    it.setForeground(QBrush(QColor(RED)))
                elif c == 2:
                    it.setForeground(QBrush(QColor(AMBER)))
                self.gr_tbl.setItem(r, c, it)
            bar = prog_bar(pct, RED if over_g else TEAL, 10)
            bar.setTextVisible(True); bar.setFormat(f" {pct}%")
            self.gr_tbl.setCellWidget(r, 6, bar)
            self.gr_tbl.setRowHeight(r, 34)

        self.ms_tbl.setRowCount(len(milestones))
        for r, m in enumerate(milestones):
            overdue_m = not m.isCompleted() and m.getDue() < today
            for c, v in enumerate([
                str(m.getId()), m.getGrantId(), m.getDesc(), m.getDue(),
                "✔ Done" if m.isCompleted()
                else ("⚠ Overdue" if overdue_m else "—")
            ]):
                it = QTableWidgetItem(str(v))
                if c == 4:
                    it.setForeground(QBrush(QColor(
                        GREEN if m.isCompleted()
                        else RED if overdue_m else TXT_M)))
                elif c == 3 and overdue_m:
                    it.setForeground(QBrush(QColor(RED)))
                self.ms_tbl.setItem(r, c, it)

    def _mark_done(self):
        mid_txt = self.ms_sel.text().strip()
        if not mid_txt:
            QMessageBox.warning(self, "Validation", "Enter a Milestone ID."); return
        try:
            self.dao.mark_milestone_done(int(mid_txt))
            self.audit_dao.add("system", "MILESTONE_DONE",
                               f"Milestone {mid_txt}", "Completed")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh(); self.ms_sel.clear()
        QMessageBox.information(self, "Done", "Milestone completed.")

    def _add(self):
        desc = self.f_desc.text().strip()
        due  = self.f_due.text().strip()
        if not desc or not due:
            QMessageBox.warning(self, "Validation",
                                "Description and due date required."); return
        gid = self.f_grant.currentData()
        try:
            m = Milestone(gid, desc, due, False)
            self.dao.add_milestone(m)
            self.audit_dao.add("system", "ADD_MILESTONE", gid, desc)
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()
        self.f_desc.clear(); self.f_due.clear()
        QMessageBox.information(self, "Added", "Milestone added.")

    def _export(self):
        QMessageBox.information(self, "Export",
                                "DOCX report generation triggered (mock mode).")