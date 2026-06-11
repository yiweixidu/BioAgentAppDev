# researcher_tab.py – BP1 Whimsigoth v2
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox)
from PyQt6.QtGui import QColor, QBrush
from ui_helpers import (card, scroll_wrap, setup_table, fgroup,
                        AMBER, TEAL, GREEN, RED, PURP, TXT_M)
from mock_data import researchers, add_audit, next_id

ROLE_CLR = {"admin": AMBER, "lab_manager": TEAL, "researcher": GREEN}

class ResearcherTab(QWidget):
    def __init__(self):
        super().__init__()
        _, layout = scroll_wrap(self)

        reg, cl = card("👤  Register New Researcher", border=AMBER)
        self.f_name   = QLineEdit(); self.f_name.setPlaceholderText("Full name")
        self.f_inst   = QLineEdit(); self.f_inst.setPlaceholderText("Institution / lab")
        self.f_pi     = QLineEdit(); self.f_pi.setPlaceholderText("Principal Investigator")
        self.f_email  = QLineEdit(); self.f_email.setPlaceholderText("email@institution.ca")
        self.f_pw     = QLineEdit(); self.f_pw.setPlaceholderText("Password")
        self.f_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_domain = QComboBox()
        self.f_domain.addItems(["flu_bnab","noncoding_dna","antibiotic_resistance","oncology","general"])
        self.f_role = QComboBox()
        self.f_role.addItems(["researcher","lab_manager","admin"])
        for a, b, la, lb in [(self.f_name,self.f_inst,"Name","Institution"),
                             (self.f_pi,self.f_email,"PI Name","Email"),
                             (self.f_domain,self.f_role,"Domain","Role")]:
            row = QHBoxLayout(); row.setSpacing(12)
            row.addLayout(fgroup(la, a)); row.addLayout(fgroup(lb, b))
            cl.addLayout(row)
        pw_row = QHBoxLayout(); pw_row.setSpacing(12)
        pw_row.addLayout(fgroup("Password", self.f_pw)); pw_row.addStretch()
        cl.addLayout(pw_row)
        btn_r = QHBoxLayout()
        btn = QPushButton("✚  Register Researcher"); btn.setObjectName("primaryButton")
        btn.clicked.connect(self._create); btn_r.addWidget(btn); btn_r.addStretch()
        cl.addLayout(btn_r)
        layout.addWidget(reg)

        tbl_c, tl = card("📋  Researcher Registry", border=TEAL)
        self.table = QTableWidget()
        setup_table(self.table,["ID","Name","Institution","PI","Domain","Role","Email"],6)
        tl.addWidget(self.table); layout.addWidget(tbl_c)

        del_c, dl = card("🗑  Remove Researcher", border=RED)
        self.del_id = QLineEdit(); self.del_id.setPlaceholderText("e.g.  RES-001")
        del_btn = QPushButton("Delete"); del_btn.setObjectName("dangerButton")
        del_btn.clicked.connect(self._delete)
        dr = QHBoxLayout(); dr.setSpacing(12)
        dr.addLayout(fgroup("Researcher ID", self.del_id))
        dr.addWidget(del_btn); dr.addStretch()
        dl.addLayout(dr); layout.addWidget(del_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        self.table.setRowCount(len(researchers))
        for r, res in enumerate(researchers):
            for c, v in enumerate([res["id"],res["name"],res["institution"],
                                   res["pi"],res["domain"],res["role"],res["email"]]):
                it = QTableWidgetItem(str(v))
                if c == 5: it.setForeground(QBrush(QColor(ROLE_CLR.get(res["role"],TXT_M))))
                self.table.setItem(r, c, it)

    def _create(self):
        name = self.f_name.text().strip()
        if not name: QMessageBox.warning(self,"Validation","Name is required."); return
        nid = next_id(researchers,"RES")
        researchers.append({"id":nid,"name":name,
            "institution":self.f_inst.text().strip() or "—",
            "pi":self.f_pi.text().strip() or "—",
            "domain":self.f_domain.currentText(),"role":self.f_role.currentText(),
            "email":self.f_email.text().strip()})
        add_audit(name,"CREATE",f"Researcher {nid}","Registered")
        self._refresh()
        for w in [self.f_name,self.f_inst,self.f_pi,self.f_email,self.f_pw]: w.clear()
        QMessageBox.information(self,"Registered",f"{nid} registered successfully.")

    def _delete(self):
        rid = self.del_id.text().strip()
        for i,r in enumerate(researchers):
            if r["id"]==rid:
                researchers.pop(i); add_audit("system","DELETE",f"Researcher {rid}","Soft-deleted")
                self._refresh(); self.del_id.clear()
                QMessageBox.information(self,"Deleted",f"{rid} removed."); return
        QMessageBox.warning(self,"Not found",f"No researcher with ID {rid}.")
