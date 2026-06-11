# knowledge_tab.py – BP3 Whimsigoth v2
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QSpinBox)
from PyQt6.QtGui import QColor, QBrush
from datetime import date
from ui_helpers import card, scroll_wrap, setup_table, fgroup, AMBER, TEAL, GREEN, RED, PURP, BLUE, TXT_M
from mock_data import model_skills, projects, add_audit, next_id, get_project_title, EVALBUS

STATUS_CLR = {"active": TEAL, "inactive": TXT_M}

class KnowledgeTab(QWidget):
    def __init__(self):
        super().__init__()
        _, layout = scroll_wrap(self)

        reg_c, rl = card("📦  Model Skill Registry", border=TEAL)
        self.table = QTableWidget()
        setup_table(self.table,
            ["ID","Model","Project","LoRA Version","Threshold","Benchmark","Status","Loaded"],2)
        rl.addWidget(self.table)
        btn_row = QHBoxLayout()
        self.act_btn   = QPushButton("✔  Activate")
        self.deact_btn = QPushButton("✖  Deactivate")
        self.del_btn   = QPushButton("🗑  Remove"); self.del_btn.setObjectName("dangerButton")
        for b in [self.act_btn,self.deact_btn,self.del_btn]: btn_row.addWidget(b)
        btn_row.addStretch()
        self.act_btn.clicked.connect(lambda: self._set_status("active"))
        self.deact_btn.clicked.connect(lambda: self._set_status("inactive"))
        self.del_btn.clicked.connect(self._delete)
        rl.addLayout(btn_row); layout.addWidget(reg_c)

        asgn_c, al = card("🔧  Assign Skill to Project", border=AMBER)
        self.f_proj  = QComboBox()
        for p in projects: self.f_proj.addItem(f"{p['id']} – {p['title']}", p["id"])
        self.f_model = QComboBox()
        self.f_model.addItems(["DNABERT-2","ESM-2","PPI Predictor","LangChain-RAG"])
        self.f_lora  = QLineEdit(); self.f_lora.setPlaceholderText("e.g.  flu-ha-v4")
        self.f_bench = QLineEdit(); self.f_bench.setPlaceholderText("e.g.  HA_binding_eval")
        self.f_thr   = QSpinBox(); self.f_thr.setRange(50,1000); self.f_thr.setValue(200)
        for a,b,la,lb in [(self.f_proj,self.f_model,"Project","AI Model"),
                          (self.f_lora,self.f_bench,"LoRA Version","Benchmark"),
                          (self.f_thr,None,"Threshold (epochs)",None)]:
            row = QHBoxLayout(); row.setSpacing(12)
            row.addLayout(fgroup(la,a))
            if b: row.addLayout(fgroup(lb,b))
            al.addLayout(row)
        r = QHBoxLayout()
        asgn_btn = QPushButton("✚  Assign Skill"); asgn_btn.setObjectName("primaryButton")
        asgn_btn.clicked.connect(self._assign); r.addWidget(asgn_btn); r.addStretch()
        al.addLayout(r); layout.addWidget(asgn_c)

        eval_c, el = card("📊  EvalBus Benchmark Scores", border=PURP)
        self.eval_tbl = QTableWidget()
        setup_table(self.eval_tbl,["Model","Pearson r","AUC","vs Baseline"],0)
        self.eval_tbl.setMaximumHeight(110); self._populate_evalbus()
        el.addWidget(self.eval_tbl); layout.addWidget(eval_c)
        layout.addStretch(); self._refresh()

    def _refresh(self):
        self.table.setRowCount(len(model_skills))
        for r,s in enumerate(model_skills):
            for c,v in enumerate([s["id"],s["name"],get_project_title(s["project_id"]),
                                   s["lora_version"],str(s["threshold"]),
                                   s["benchmark"],s["status"],s["loaded"]]):
                it = QTableWidgetItem(str(v))
                if c==6: it.setForeground(QBrush(QColor(STATUS_CLR.get(s["status"],TXT_M))))
                self.table.setItem(r,c,it)

    def _populate_evalbus(self):
        rows = list(EVALBUS.items()); self.eval_tbl.setRowCount(len(rows))
        for r,(model,sc) in enumerate(rows):
            pos = sc["vs_baseline"].startswith("+")
            for c,v in enumerate([model,f"{sc['pearson_r']:.2f}",f"{sc['AUC']:.2f}",sc["vs_baseline"]]):
                it = QTableWidgetItem(str(v))
                if c==3: it.setForeground(QBrush(QColor(GREEN if pos else RED)))
                self.eval_tbl.setItem(r,c,it)

    def _set_status(self, status):
        row = self.table.currentRow()
        if row<0: QMessageBox.warning(self,"Selection","Select a row first."); return
        model_skills[row]["status"]=status
        add_audit("system","SKILL_STATUS",model_skills[row]["id"],f"→ {status}")
        self._refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row<0: QMessageBox.warning(self,"Selection","Select a row first."); return
        sk = model_skills.pop(row)
        add_audit("system","DELETE",sk["id"],"Removed"); self._refresh()
        QMessageBox.information(self,"Removed",f"{sk['id']} removed.")

    def _assign(self):
        lora = self.f_lora.text().strip()
        if not lora: QMessageBox.warning(self,"Validation","LoRA version required."); return
        pid=self.f_proj.currentData(); name=self.f_model.currentText()
        sk={"id":next_id(model_skills,"SK"),"name":name,"project_id":pid,
            "lora_version":lora,"threshold":self.f_thr.value(),
            "benchmark":self.f_bench.text().strip() or "default_eval",
            "status":"inactive","loaded":date.today().isoformat()}
        model_skills.append(sk)
        add_audit("system","ASSIGN_SKILL",f"{sk['id']} → {pid}",f"{name} {lora}")
        self._refresh(); self.f_lora.clear(); self.f_bench.clear()
        QMessageBox.information(self,"Assigned",f"{name} assigned (status: inactive).")
