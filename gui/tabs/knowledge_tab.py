# gui/tabs/knowledge_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QSpinBox)
from PyQt6.QtGui import QColor, QBrush
from datetime import date
from gui.ui_helpers import (card, scroll_wrap, setup_table, fgroup,
                            AMBER, TEAL, GREEN, RED, PURP, BLUE, TXT_M)
from dao.dao_model_skill import ModelSkillDAO
from dao.dao_project     import ProjectDAO
from dao.dao_audit       import AuditDAO
from models.model_skill  import ModelSkill

STATUS_CLR = {"active": TEAL, "inactive": TXT_M}

EVALBUS = {
    "DNABERT-2":     {"pearson_r": 0.74, "AUC": 0.89, "vs_baseline": "+0.03"},
    "ESM-2":         {"pearson_r": 0.81, "AUC": 0.93, "vs_baseline": "+0.05"},
    "PPI Predictor": {"pearson_r": 0.68, "AUC": 0.86, "vs_baseline": "+0.05"},
}


class KnowledgeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dao         = ModelSkillDAO()
        self.project_dao = ProjectDAO()
        self.audit_dao   = AuditDAO()
        _, layout = scroll_wrap(self)

        reg_c, rl = card("📦  Model Skill Registry", border=TEAL)
        self.table = QTableWidget()
        setup_table(self.table,
            ["ID","Model","Project","LoRA Version",
             "Threshold","Benchmark","Status","Loaded"], 2)
        rl.addWidget(self.table)
        btn_row = QHBoxLayout()
        self.act_btn   = QPushButton("✔  Activate")
        self.deact_btn = QPushButton("✖  Deactivate")
        self.del_btn   = QPushButton("🗑  Remove")
        self.del_btn.setObjectName("dangerButton")
        for b in [self.act_btn, self.deact_btn, self.del_btn]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        self.act_btn.clicked.connect(lambda: self._set_status("active"))
        self.deact_btn.clicked.connect(lambda: self._set_status("inactive"))
        self.del_btn.clicked.connect(self._delete)
        rl.addLayout(btn_row); layout.addWidget(reg_c)

        asgn_c, al = card("🔧  Assign Skill to Project", border=AMBER)
        self.f_proj  = QComboBox()
        try:
            for p in self.project_dao.get_all():
                self.f_proj.addItem(
                    f"{p.getProjId()} – {p.getTitle()}", p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e))
        self.f_model = QComboBox()
        self.f_model.addItems(["DNABERT-2","ESM-2","PPI Predictor","LangChain-RAG"])
        self.f_lora  = QLineEdit(); self.f_lora.setPlaceholderText("e.g.  flu-ha-v4")
        self.f_bench = QLineEdit(); self.f_bench.setPlaceholderText("e.g.  HA_binding_eval")
        self.f_thr   = QSpinBox(); self.f_thr.setRange(50, 1000); self.f_thr.setValue(200)
        for a, b, la, lb in [
            (self.f_proj,  self.f_model, "Project",          "AI Model"),
            (self.f_lora,  self.f_bench, "LoRA Version",     "Benchmark"),
            (self.f_thr,   None,         "Threshold (epochs)", None)
        ]:
            row = QHBoxLayout(); row.setSpacing(12)
            row.addLayout(fgroup(la, a))
            if b: row.addLayout(fgroup(lb, b))
            al.addLayout(row)
        r = QHBoxLayout()
        asgn_btn = QPushButton("✚  Assign Skill")
        asgn_btn.setObjectName("primaryButton")
        asgn_btn.clicked.connect(self._assign)
        r.addWidget(asgn_btn); r.addStretch()
        al.addLayout(r); layout.addWidget(asgn_c)

        eval_c, el = card("📊  EvalBus Benchmark Scores", border=PURP)
        self.eval_tbl = QTableWidget()
        setup_table(self.eval_tbl, ["Model","Pearson r","AUC","vs Baseline"], 0)
        self.eval_tbl.setMaximumHeight(110)
        self._populate_evalbus()
        el.addWidget(self.eval_tbl); layout.addWidget(eval_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        try:
            skills = self.dao.get_all()
            titles = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self.table.setRowCount(len(skills))
        for r, s in enumerate(skills):
            for c, v in enumerate([
                s.getSkillId(),
                s.getName(),
                titles.get(s.getProjectId(), s.getProjectId()),
                s.getLoraVersion(),
                str(s.getThreshold()),
                s.getBenchmark(),
                s.getStatus(),
                s.getLoaded()
            ]):
                it = QTableWidgetItem(str(v))
                if c == 6:
                    it.setForeground(QBrush(QColor(
                        STATUS_CLR.get(s.getStatus(), TXT_M))))
                self.table.setItem(r, c, it)

    def _populate_evalbus(self):
        rows = list(EVALBUS.items())
        self.eval_tbl.setRowCount(len(rows))
        for r, (model, sc) in enumerate(rows):
            pos = sc["vs_baseline"].startswith("+")
            for c, v in enumerate([
                model, f"{sc['pearson_r']:.2f}",
                f"{sc['AUC']:.2f}", sc["vs_baseline"]
            ]):
                it = QTableWidgetItem(str(v))
                if c == 3:
                    it.setForeground(QBrush(QColor(GREEN if pos else RED)))
                self.eval_tbl.setItem(r, c, it)

    def _set_status(self, status):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Select a row first."); return
        try:
            skill_id = self.table.item(row, 0).text()
            self.dao.update_status(skill_id, status)
            self.audit_dao.add("system", "SKILL_STATUS",
                               skill_id, f"-> {status}")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Select a row first."); return
        try:
            skill_id = self.table.item(row, 0).text()
            self.dao.delete(skill_id)
            self.audit_dao.add("system", "DELETE", skill_id, "Removed")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()
        QMessageBox.information(self, "Removed", f"{skill_id} removed.")

    def _assign(self):
        lora = self.f_lora.text().strip()
        if not lora:
            QMessageBox.warning(self, "Validation", "LoRA version required."); return
        try:
            nid = f"SK-{self.dao.count() + 1:03d}"
            sk  = ModelSkill(
                nid,
                self.f_model.currentText(),
                self.f_proj.currentData(),
                lora,
                self.f_thr.value(),
                self.f_bench.text().strip() or "default_eval",
                "inactive",
                str(date.today())
            )
            self.dao.insert(sk)
            self.audit_dao.add("system", "ASSIGN_SKILL",
                               f"{nid} -> {sk.getProjectId()}",
                               f"{sk.getName()} {lora}")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh()
        self.f_lora.clear(); self.f_bench.clear()
        QMessageBox.information(self, "Assigned",
                                f"{sk.getName()} assigned (status: inactive).")