# gui/tabs/projects_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox)
from PyQt6.QtGui import QColor, QBrush
from gui.ui_helpers import (card, scroll_wrap, setup_table, fgroup,
                            AMBER, TEAL, GREEN, RED, PURP, TXT_M)
from dao.dao_project import ProjectDAO
from dao.dao_audit   import AuditDAO
from models.project  import Project

STATUS_CLR = {"active": TEAL, "planning": PURP, "archived": TXT_M}


class ProjectsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dao       = ProjectDAO()
        self.audit_dao = AuditDAO()
        _, layout = scroll_wrap(self)

        reg, cl = card("➕  New Project Registration", border=AMBER)
        self.f_title  = QLineEdit(); self.f_title.setPlaceholderText("Project title")
        self.f_pi     = QLineEdit(); self.f_pi.setPlaceholderText("Principal Investigator")
        self.f_domain = QComboBox()
        self.f_domain.addItems(["flu_bnab","noncoding_dna",
                                "antibiotic_resistance","oncology","general"])
        self.f_grant = QComboBox()
        self.f_grant.addItems(["CIHR","NSERC","MITACS","Génome Québec","FRQS"])
        for a, b, la, lb in [(self.f_title,  self.f_pi,    "Title",        "PI Name"),
                             (self.f_domain, self.f_grant, "Domain Skill", "Grant Type")]:
            row = QHBoxLayout(); row.setSpacing(12)
            row.addLayout(fgroup(la, a)); row.addLayout(fgroup(lb, b))
            cl.addLayout(row)
        r = QHBoxLayout()
        btn = QPushButton("✚  Create Project")
        btn.setObjectName("primaryButton")
        btn.clicked.connect(self._create)
        r.addWidget(btn); r.addStretch()
        cl.addLayout(r); layout.addWidget(reg)

        tbl_c, tl = card("📋  Project Registry", border=TEAL)
        self.table = QTableWidget()
        setup_table(self.table,
            ["ID","Title","Domain","Grant","PI","Status","AI Skill"], 1)
        tl.addWidget(self.table); layout.addWidget(tbl_c)

        del_c, dl = card("🗑  Delete Project", border=RED)
        self.del_id = QLineEdit()
        self.del_id.setPlaceholderText("e.g.  PRJ-101")
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("dangerButton")
        del_btn.clicked.connect(self._delete)
        dr = QHBoxLayout(); dr.setSpacing(12)
        dr.addLayout(fgroup("Project ID", self.del_id))
        dr.addWidget(del_btn); dr.addStretch()
        dl.addLayout(dr); layout.addWidget(del_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        try:
            projects = self.dao.get_all()
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self.table.setRowCount(len(projects))
        for r, p in enumerate(projects):
            for c, v in enumerate([
                p.getProjId(), p.getTitle(),  p.getDomain(),
                p.getGrant(),  p.getPi(),     p.getStatus(),
                p.getSkill() or "—"
            ]):
                it = QTableWidgetItem(str(v))
                if c == 5:
                    it.setForeground(QBrush(QColor(
                        STATUS_CLR.get(p.getStatus(), TXT_M))))
                elif c == 6 and p.getSkill():
                    it.setForeground(QBrush(QColor(TEAL)))
                self.table.setItem(r, c, it)

    def _create(self):
        title = self.f_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Title required."); return
        try:
            nid = f"PRJ-{self.dao.count() + 200}"
            p   = Project(
                nid, title,
                self.f_domain.currentText(),
                self.f_grant.currentText(),
                self.f_pi.text().strip() or "Unknown",
                "active", None, 0
            )
            self.dao.insert(p)
            self.audit_dao.add("system", "CREATE",
                               f"Project {nid}", f"'{title}' registered")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()
        self.f_title.clear(); self.f_pi.clear()
        QMessageBox.information(self, "Created", f"{nid} created.")

    def _delete(self):
        pid = self.del_id.text().strip()
        if not pid:
            QMessageBox.warning(self, "Validation", "Enter a Project ID."); return
        try:
            self.dao.delete(pid)
            self.audit_dao.add("system", "DELETE",
                               f"Project {pid}", "Soft-deleted")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh(); self.del_id.clear()
        QMessageBox.information(self, "Deleted", f"{pid} removed.")