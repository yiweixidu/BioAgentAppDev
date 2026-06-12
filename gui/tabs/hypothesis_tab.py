# gui/tabs/hypothesis_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QTextEdit)
from PyQt6.QtGui import QColor, QBrush
from gui.ui_helpers import (card, scroll_wrap, setup_table, fgroup, flbl,
                            AMBER, TEAL, GREEN, RED, PURP, BLUE, TXT_S,
                            STATUS_FG, STATUS_ROW_BG)
from dao.dao_hypothesis import HypothesisDAO
from dao.dao_project    import ProjectDAO
from dao.dao_audit      import AuditDAO
from models.hypothesis  import Hypothesis


class HypothesisTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dao         = HypothesisDAO()
        self.project_dao = ProjectDAO()
        self.audit_dao   = AuditDAO()
        _, layout = scroll_wrap(self)

        filt_c, fl = card("🔍  Filter Hypotheses", border=BLUE)
        f_row = QHBoxLayout(); f_row.setSpacing(20)
        self.f_proj = QComboBox()
        self.f_proj.addItem("All Projects", None)
        try:
            for p in self.project_dao.get_all():
                self.f_proj.addItem(
                    f"{p.getProjId()} – {p.getTitle()}", p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e))
        self.f_stat = QComboBox()
        self.f_stat.addItems(["All Statuses","supported","refuted","pending"])
        for label, w in [("Project", self.f_proj), ("Status", self.f_stat)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(flbl(label)); col.addWidget(w)
            f_row.addLayout(col)
        f_row.addStretch(); fl.addLayout(f_row)
        self.f_proj.currentIndexChanged.connect(self._refresh)
        self.f_stat.currentIndexChanged.connect(self._refresh)
        layout.addWidget(filt_c)

        tbl_c, tl = card("📋  Hypothesis List", border=TEAL)
        self.table = QTableWidget()
        setup_table(self.table,
            ["ID","Hypothesis Text","Status","Confidence",
             "PMIDs","Project","Note"], 1)
        tl.addWidget(self.table); layout.addWidget(tbl_c)

        upd_c, ul = card("✏️  Record Wet-Lab Result", border=AMBER)
        self.u_id   = QLineEdit(); self.u_id.setPlaceholderText("H14")
        self.u_stat = QComboBox()
        self.u_stat.addItems(["supported","refuted","pending"])
        self.u_user = QLineEdit()
        self.u_user.setPlaceholderText("Researcher name")
        self.u_note = QLineEdit()
        self.u_note.setPlaceholderText("Observation note")
        for a, b, la, lb in [
            (self.u_id,   self.u_stat, "Hypothesis ID", "New Status"),
            (self.u_user, self.u_note, "Researcher",    "Note")
        ]:
            row = QHBoxLayout(); row.setSpacing(12)
            row.addLayout(fgroup(la, a)); row.addLayout(fgroup(lb, b))
            ul.addLayout(row)
        r = QHBoxLayout()
        upd_btn = QPushButton("✔  Record Result  (audit logged)")
        upd_btn.setObjectName("primaryButton")
        upd_btn.clicked.connect(self._update)
        r.addWidget(upd_btn); r.addStretch(); ul.addLayout(r)
        layout.addWidget(upd_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        try:
            all_hyp = self.dao.get_all()
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        pid  = self.f_proj.currentData()
        stat = self.f_stat.currentText()
        filtered = [h for h in all_hyp
                    if (pid is None or h.getProjectId() == pid)
                    and (stat == "All Statuses" or h.getStatus() == stat)]
        self.table.setRowCount(len(filtered))
        for r, h in enumerate(filtered):
            bg = STATUS_ROW_BG.get(h.getStatus())
            for c, v in enumerate([
                h.getHypId(),        h.getText(),
                h.getStatus(),       str(h.getConfidence()),
                h.getPmids(),        h.getProjectId(),
                h.getNote()
            ]):
                it = QTableWidgetItem(str(v))
                if bg:  it.setBackground(QBrush(bg))
                if c == 2:
                    it.setForeground(QBrush(QColor(
                        STATUS_FG.get(h.getStatus(), TXT_S))))
                self.table.setItem(r, c, it)

    def _update(self):
        hid  = self.u_id.text().strip()
        stat = self.u_stat.currentText()
        user = self.u_user.text().strip() or "Unknown"
        note = self.u_note.text().strip()
        if not hid:
            QMessageBox.warning(self, "Validation", "Hypothesis ID required."); return
        try:
            self.dao.update_status(hid, stat, note)
            self.audit_dao.add(
                user, "UPDATE", f"Hypothesis {hid}",
                f"-> {stat}" + (f" ({note})" if note else ""))
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()
        self.u_id.clear(); self.u_note.clear()
        QMessageBox.information(self, "Updated", f"{hid} → {stat}")