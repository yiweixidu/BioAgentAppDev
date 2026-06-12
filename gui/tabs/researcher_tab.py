# gui/tabs/researcher_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox)
from PyQt6.QtGui import QColor, QBrush
from gui.ui_helpers import (card, scroll_wrap, setup_table, fgroup,
                            AMBER, TEAL, GREEN, RED, PURP, TXT_M)
from dao.dao_researcher import ResearcherDAO
from dao.dao_audit      import AuditDAO
from models.researcher  import Researcher

ROLE_CLR = {"admin": AMBER, "lab_manager": TEAL, "researcher": GREEN}


class ResearcherTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dao       = ResearcherDAO()
        self.audit_dao = AuditDAO()
        _, layout = scroll_wrap(self)

        reg, cl = card("👤  Register New Researcher", border=AMBER)
        self.f_name   = QLineEdit(); self.f_name.setPlaceholderText("Full name")
        self.f_inst   = QLineEdit(); self.f_inst.setPlaceholderText("Institution / lab")
        self.f_pi     = QLineEdit(); self.f_pi.setPlaceholderText("Principal Investigator")
        self.f_email  = QLineEdit(); self.f_email.setPlaceholderText("email@institution.ca")
        self.f_pw     = QLineEdit(); self.f_pw.setPlaceholderText("Password")
        self.f_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_domain = QComboBox()
        self.f_domain.addItems(["flu_bnab","noncoding_dna",
                                "antibiotic_resistance","oncology","general"])
        self.f_role = QComboBox()
        self.f_role.addItems(["researcher","lab_manager","admin"])
        for a, b, la, lb in [(self.f_name, self.f_inst,   "Name",    "Institution"),
                             (self.f_pi,   self.f_email,  "PI Name", "Email"),
                             (self.f_domain, self.f_role, "Domain",  "Role")]:
            row = QHBoxLayout(); row.setSpacing(12)
            row.addLayout(fgroup(la, a)); row.addLayout(fgroup(lb, b))
            cl.addLayout(row)
        pw_row = QHBoxLayout(); pw_row.setSpacing(12)
        pw_row.addLayout(fgroup("Password", self.f_pw)); pw_row.addStretch()
        cl.addLayout(pw_row)
        btn_r = QHBoxLayout()
        btn = QPushButton("✚  Register Researcher")
        btn.setObjectName("primaryButton")
        btn.clicked.connect(self._create)
        btn_r.addWidget(btn); btn_r.addStretch()
        cl.addLayout(btn_r)
        layout.addWidget(reg)

        tbl_c, tl = card("📋  Researcher Registry", border=TEAL)
        self.table = QTableWidget()
        setup_table(self.table,
            ["ID","Name","Institution","PI","Domain","Role","Email"], 6)
        tl.addWidget(self.table); layout.addWidget(tbl_c)

        del_c, dl = card("🗑  Remove Researcher", border=RED)
        self.del_id = QLineEdit()
        self.del_id.setPlaceholderText("e.g.  RES-001")
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("dangerButton")
        del_btn.clicked.connect(self._delete)
        dr = QHBoxLayout(); dr.setSpacing(12)
        dr.addLayout(fgroup("Researcher ID", self.del_id))
        dr.addWidget(del_btn); dr.addStretch()
        dl.addLayout(dr); layout.addWidget(del_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        try:
            researchers = self.dao.get_all()
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self.table.setRowCount(len(researchers))
        for r, res in enumerate(researchers):
            for c, v in enumerate([
                res.getResId(), res.getName(), res.getInstitution(),
                res.getPi(),    res.getDomain(), res.getRole(), res.getEmail()
            ]):
                it = QTableWidgetItem(str(v))
                if c == 5:
                    it.setForeground(QBrush(QColor(
                        ROLE_CLR.get(res.getRole(), TXT_M))))
                self.table.setItem(r, c, it)

    def _create(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required."); return
        try:
            nid = f"RES-{self.dao.count() + 1:03d}"
            res = Researcher(
                nid, name,
                self.f_inst.text().strip()   or "—",
                self.f_pi.text().strip()     or "—",
                self.f_domain.currentText(),
                self.f_role.currentText(),
                self.f_email.text().strip()
            )
            self.dao.insert(res)
            self.audit_dao.add(name, "CREATE",
                               f"Researcher {nid}", "Registered")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()
        for w in [self.f_name, self.f_inst, self.f_pi,
                  self.f_email, self.f_pw]:
            w.clear()
        QMessageBox.information(self, "Registered",
                                f"{nid} registered successfully.")

    def _delete(self):
        rid = self.del_id.text().strip()
        if not rid:
            QMessageBox.warning(self, "Validation", "Enter a Researcher ID."); return
        try:
            res = self.dao.get_by_id(rid)
            if res is None:
                QMessageBox.warning(self, "Not found",
                                    f"No researcher with ID {rid}."); return
            self.dao.delete(rid)
            self.audit_dao.add("system", "DELETE",
                               f"Researcher {rid}", "Removed")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh(); self.del_id.clear()
        QMessageBox.information(self, "Deleted", f"{rid} removed.")