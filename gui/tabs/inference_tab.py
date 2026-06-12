# gui/tabs/inference_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                             QComboBox, QPushButton, QTextEdit,
                             QTableWidget, QTableWidgetItem,
                             QMessageBox, QButtonGroup)
from datetime import datetime
from gui.ui_helpers import (card, scroll_wrap, setup_table, fgroup,
                            AMBER, TEAL, GREEN, BLUE)
from dao.dao_inference import InferenceDAO
from dao.dao_project   import ProjectDAO
from dao.dao_audit     import AuditDAO
from models.inference_record import InferenceRecord

TYPES = [("🧬","DNA Variant"),("🧪","Protein FASTA"),
         ("🤝","PPI Antibody–Antigen"),("📚","Literature RAG")]
TYPE_MODELS = {
    "DNA Variant":          "DNABERT-2",
    "Protein FASTA":        "ESM-2",
    "PPI Antibody–Antigen": "PPI Predictor",
    "Literature RAG":       "LangChain-RAG"
}
TYPE_PH = {
    "DNA Variant":          "chr12:25398284 A>T hg38",
    "Protein FASTA":        ">Ab_VH\nEVQLVESGGG...",
    "PPI Antibody–Antigen": "VH/VL sequence  +  antigen PDB ID: 6XR8",
    "Literature RAG":       "KRAS G12C inhibitor resistance mechanisms"
}
MOCK = {
    "DNA Variant": (
        "DNABERT-2  ·  Variant Effect Prediction\n" + "─"*44 + "\n"
        "Variant:        chr12:25398284 A>T (hg38)\n"
        "Gene:           KRAS  (p.Gly12Cys)\n"
        "Effect score:   -1.83   [95% CI: -2.10, -1.56]\n"
        "Pathogenicity:  LIKELY DAMAGING\n"
        "Provenance:     PMID:38201847  ·  PMID:36754893  ·  PDB:6XR8"),
    "Protein FASTA": (
        "ESM-2  ·  Binding Affinity\n" + "─"*44 + "\n"
        "dG binding:     -12.4 kcal/mol\nKd estimate:    2.3 nM\n"
        "Stability:      0.81  (stable)\n"
        "PDB template:   6XR8, 7KDL\nAdapter:        flu-ha-v3"),
    "PPI Antibody–Antigen": (
        "PPI Predictor  ·  Interface Scoring\n" + "─"*44 + "\n"
        "Interaction prob.:  0.92  (HIGH CONFIDENCE)\n"
        "ddG interface:      -3.2 kcal/mol\n"
        "Epitope residues:   27-35, 52-58\n"
        "Provenance:         PDB:6XR8  ·  PMID:38201847"),
    "Literature RAG": (
        "LangChain-RAG  ·  FAISS Literature Synthesis\n" + "─"*44 + "\n"
        "  •  MAPK reactivation (PMID:35039682)\n"
        "  •  Secondary mutations Y96D/H95D (PMID:36521447)\n"
        "  •  SOS1 combination (PMID:37123890)\n"
        "Citation validation:  3/3 sourced"),
}


class InferenceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dao         = InferenceDAO()
        self.project_dao = ProjectDAO()
        self.audit_dao   = AuditDAO()
        _, layout = scroll_wrap(self)

        conf_c, cl = card("🧬  Inference Configuration", border=TEAL)
        pill_row = QHBoxLayout(); pill_row.setSpacing(8)
        self.btn_group = QButtonGroup(self); self.btn_group.setExclusive(True)
        self._type_btns = {}
        for icon, typ in TYPES:
            btn = QPushButton(f"{icon}  {typ}")
            btn.setObjectName("typeBtn"); btn.setCheckable(True)
            self.btn_group.addButton(btn)
            self._type_btns[typ] = btn; pill_row.addWidget(btn)
        pill_row.addStretch()
        self._type_btns["DNA Variant"].setChecked(True)
        cl.addLayout(pill_row)
        self.btn_group.buttonClicked.connect(self._on_type)
        row = QHBoxLayout(); row.setSpacing(12)
        self.f_model = QComboBox()
        self.f_model.addItems(["DNABERT-2","ESM-2","PPI Predictor","LangChain-RAG"])
        self.f_proj = QComboBox()
        try:
            for p in self.project_dao.get_all():
                self.f_proj.addItem(
                    f"{p.getProjId()} – {p.getTitle()}", p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e))
        row.addLayout(fgroup("AI Model", self.f_model))
        row.addLayout(fgroup("Save to Project", self.f_proj))
        cl.addLayout(row); layout.addWidget(conf_c)

        inp_c, il = card("📝  Input", border=AMBER)
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText(TYPE_PH["DNA Variant"])
        self.input_box.setMaximumHeight(90); il.addWidget(self.input_box)
        run_r = QHBoxLayout()
        self.run_btn = QPushButton("▶  Run Inference")
        self.run_btn.setObjectName("primaryButton")
        self.run_btn.clicked.connect(self._run)
        run_r.addWidget(self.run_btn); run_r.addStretch()
        il.addLayout(run_r); layout.addWidget(inp_c)

        res_c, rl = card("📊  Prediction Result", border=GREEN)
        self.result_box = QTextEdit()
        self.result_box.setObjectName("ResultBox")
        self.result_box.setReadOnly(True)
        self.result_box.setMinimumHeight(130)
        self.result_box.setPlaceholderText(
            "Results will appear here after running inference.")
        rl.addWidget(self.result_box); layout.addWidget(res_c)

        hist_c, hl = card("🕐  Inference History", border=BLUE)
        self.hist_tbl = QTableWidget()
        setup_table(self.hist_tbl,
            ["Job ID","Type","Model","Input",
             "Result Summary","Project","Timestamp"], 4)
        self.hist_tbl.setMaximumHeight(160); hl.addWidget(self.hist_tbl)
        layout.addWidget(hist_c); layout.addStretch()
        self._refresh_history()

    def _current_type(self):
        return next(t for t, b in self._type_btns.items() if b.isChecked())

    def _on_type(self, btn):
        typ = next(t for t, b in self._type_btns.items() if b is btn)
        self.input_box.setPlaceholderText(TYPE_PH.get(typ, "Enter input…"))
        mdl = TYPE_MODELS.get(typ, "DNABERT-2")
        idx = self.f_model.findText(mdl)
        if idx >= 0: self.f_model.setCurrentIndex(idx)

    def _run(self):
        inp = self.input_box.toPlainText().strip()
        if not inp:
            QMessageBox.warning(self, "Input", "Provide input data."); return
        typ   = self._current_type()
        model = self.f_model.currentText()
        pid   = self.f_proj.currentData()
        txt   = MOCK.get(typ, "Result unavailable.")
        self.result_box.setPlainText(txt)
        try:
            jid = f"INF-{self.dao.count() + 1:03d}"
            rec = InferenceRecord(
                jid, typ, model, pid,
                (inp[:42] + "…") if len(inp) > 42 else inp,
                txt.split("\n")[2] if "\n" in txt else txt[:50],
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            self.dao.insert(rec)
            self.audit_dao.add(model, "INFERENCE", jid,
                               f"Type={typ} · Project={pid}")
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self._refresh_history()

    def _refresh_history(self):
        try:
            history = self.dao.get_all()
            titles  = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, "DB Error", str(e)); return
        self.hist_tbl.setRowCount(len(history))
        for r, h in enumerate(history):
            for c, v in enumerate([
                h.getInfId(),    h.getType(),   h.getModel(),
                h.getInput(),    h.getResultSummary(),
                titles.get(h.getProjectId(), h.getProjectId()),
                h.getTimestamp()
            ]):
                self.hist_tbl.setItem(r, c, QTableWidgetItem(str(v)))