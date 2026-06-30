# gui/tabs/inference_tab.py  — Phase 1 + Report Update
"""
InferenceTab — wires the four real skills to the UI.
L0: every run is logged to audit_chain with ip_owner.
IP: result box shows ownership. Model picker separates platform vs lab/shared.

New in this version:
  - Double-click history row → full result viewer dialog
  - 📄 Export Project Report button → PI-ready PDF
  - dao.insert() now saves full_output JSON + ip_owner + confidence
"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QTextEdit, QGridLayout, QHBoxLayout,
    QButtonGroup, QProgressBar, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, QThread
from datetime import datetime
import os, shutil

from gui.ui_helpers import (card, scroll_wrap, setup_table,
                            AMBER, TEAL, GREEN, BLUE, PURP, RED, TXT_M)
from dao.dao_inference    import InferenceDAO
from dao.dao_project      import ProjectDAO
from dao.dao_model_skill  import ModelSkillDAO
from core.audit_chain     import AuditChain
from core.project_context import ProjectContext
from engine.skill_registry import list_for_ui, get, refresh as registry_refresh
from models.inference_record import InferenceRecord

# ── Inference type definitions ─────────────────────────────────
TYPES = [
    ('🧬', 'DNA Variant',          'LocalLLM-DNABERT-2'),
    ('🧪', 'Protein FASTA',        'LocalLLM-ESM-2'),
    ('🤝', 'PPI Antibody–Antigen', 'LocalLLM-PPI'),
    ('📚', 'Literature RAG',       'LocalLLM-RAG'),
]
TYPE_PH = {
    'DNA Variant':          'chr12:25398284 A>T hg38',
    'Protein FASTA':        '>Ab_VH\nEVQLVESGGG...',
    'PPI Antibody–Antigen': 'Paste VH sequence\n\nPaste antigen sequence',
    'Literature RAG':       'KRAS G12C inhibitor resistance mechanisms',
}
IP_COLOR = {'platform': TEAL, 'lab': AMBER, 'shared': GREEN}

_SEP_BASE   = '── Base Models (Platform IP) ──'
_SEP_SKILLS = '── Fine-tuned Skills (Lab / Shared IP) ──'


# ── Background worker (prevents UI freeze) ────────────────────
class InferenceWorker(QThread):
    finished = pyqtSignal(object)   # emits SkillResult
    error    = pyqtSignal(str)

    def __init__(self, skill_id: str, input_text: str, context: dict):
        super().__init__()
        self.skill_id   = skill_id
        self.input_text = input_text
        self.context    = context

    def run(self):
        try:
            skill = get(self.skill_id)
            if skill is None:
                self.error.emit(f"Skill '{self.skill_id}' not found in registry")
                return
            result = skill.run(self.input_text, self.context)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ── Main tab ──────────────────────────────────────────────────
class InferenceTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.dao         = InferenceDAO()
        self.project_dao = ProjectDAO()
        self.skill_dao   = ModelSkillDAO()
        self._worker     = None   # keep reference to prevent GC

        # ── Filter widgets ──
        self.typeFLabel   = QLabel('Type Filter:')
        self.projFLabel   = QLabel('Project Filter:')
        self.typeFCB      = QComboBox()
        self.typeFCB.addItem('All Types', None)
        for _, t, _ in TYPES:
            self.typeFCB.addItem(t, t)
        self.projFilterCB = QComboBox()
        self.projFilterCB.addItem('All Projects', None)

        # ── Config widgets ──
        self.modelLabel = QLabel('AI Model / Skill:')
        self.projLabel  = QLabel('Save to Project:')
        self.modelCB    = QComboBox()
        self.projCB     = QComboBox()

        # ── IP badge label ──
        self.ipLabel = QLabel('IP: —')
        self.ipLabel.setStyleSheet(f'color:{TEAL};font-weight:700;font-size:11px;')

        # ── Input / output ──
        self.inputBox = QTextEdit()
        self.inputBox.setMaximumHeight(90)
        self.resultBox = QTextEdit()
        self.resultBox.setObjectName('ResultBox')
        self.resultBox.setReadOnly(True)
        self.resultBox.setMinimumHeight(130)
        self.resultBox.setPlaceholderText(
            'Results will appear here after running inference.')

        # ── Progress bar (shown during inference) ──
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)   # indeterminate
        self.progressBar.setVisible(False)
        self.progressBar.setMaximumHeight(4)

        # ── Type pills ──
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self._type_btns = {}
        for icon, typ, _ in TYPES:
            btn = QPushButton(f'{icon}  {typ}')
            btn.setObjectName('typeBtn')
            btn.setCheckable(True)
            self.btn_group.addButton(btn)
            self._type_btns[typ] = btn
        self._type_btns['DNA Variant'].setChecked(True)

        # ── Buttons ──
        self.searchButton = QPushButton('🔍  Search History')
        self.clearButton  = QPushButton('Clear')
        self.runButton    = QPushButton('▶  Run Inference')
        self.runButton.setObjectName('primaryButton')
        self.resetButton  = QPushButton('Reset Input')
        self.verifyButton = QPushButton('🔒  Verify Audit Chain')
        self.exportBtn    = QPushButton('📄  Export Project Report')

        # ── History table ──
        self.histTbl = QTableWidget()
        setup_table(self.histTbl,
            ['Job ID', 'Type', 'Model / Skill', 'IP Owner',
             'Input', 'Result Summary', 'Project', 'Timestamp'], 5)
        self.histTbl.setMaximumHeight(200)

        # ── Populate dropdowns ──
        self._reload_project_cb()
        self._reload_model_cb()

        # ── Signals ──
        self.searchButton.clicked.connect(self._search)
        self.clearButton.clicked.connect(self._clear_search)
        self.runButton.clicked.connect(self._run)
        self.resetButton.clicked.connect(self._reset_input)
        self.verifyButton.clicked.connect(self._verify_chain)
        self.exportBtn.clicked.connect(self._export_project_report)
        self.btn_group.buttonClicked.connect(self._type_pill_clicked)
        self.modelCB.currentIndexChanged.connect(self._model_changed)
        # Double-click row → full result viewer
        self.histTbl.cellDoubleClicked.connect(self._open_result_dialog)

        # ── Layout ──
        _, layout = scroll_wrap(self)

        srch_c, sl = card('🔍  Search Inference History', border=PURP)
        g = QGridLayout()
        g.addWidget(self.typeFLabel,   0,0); g.addWidget(self.typeFCB,      0,1)
        g.addWidget(self.projFLabel,   0,2); g.addWidget(self.projFilterCB, 0,3)
        g.addWidget(self.searchButton, 0,4); g.addWidget(self.clearButton,  0,5)
        sl.addLayout(g)
        layout.addWidget(srch_c)

        hist_c, hl = card(
            '🕐  Inference History  —  double-click row for full result',
            border=TEAL)
        hl.addWidget(self.histTbl)
        exp_row = QHBoxLayout()
        exp_row.addStretch()
        exp_row.addWidget(self.exportBtn)
        hl.addLayout(exp_row)
        layout.addWidget(hist_c)

        conf_c, cl = card('🧬  Run New Inference', border=AMBER)
        pill_row = QHBoxLayout()
        pill_row.setSpacing(8)
        for btn in self._type_btns.values():
            pill_row.addWidget(btn)
        pill_row.addStretch()
        cl.addLayout(pill_row)

        conf_g = QGridLayout()
        conf_g.addWidget(self.modelLabel, 0,0); conf_g.addWidget(self.modelCB, 0,1)
        conf_g.addWidget(self.projLabel,  0,2); conf_g.addWidget(self.projCB,  0,3)
        conf_g.addWidget(self.ipLabel,    1,0, 1,4)
        cl.addLayout(conf_g)
        layout.addWidget(conf_c)

        inp_c, il = card('📝  Input', border=GREEN)
        self.inputBox.setPlaceholderText(TYPE_PH['DNA Variant'])
        il.addWidget(self.inputBox)
        il.addWidget(self.progressBar)
        run_row = QHBoxLayout()
        run_row.addWidget(self.runButton)
        run_row.addWidget(self.resetButton)
        run_row.addWidget(self.verifyButton)
        run_row.addStretch()
        il.addLayout(run_row)
        layout.addWidget(inp_c)

        res_c, rl = card('📊  Prediction Result', border=BLUE)
        rl.addWidget(self.resultBox)
        layout.addWidget(res_c)

        layout.addStretch()
        self._refresh_history()

    # ── Dropdown reloaders ────────────────────────────────────

    def _reload_project_cb(self):
        for cb in (self.projFilterCB, self.projCB):
            cb.blockSignals(True)
            cb.clear()
        self.projFilterCB.addItem('All Projects', None)
        try:
            for p in self.project_dao.get_all():
                lbl = f"{p.getProjId()} – {p.getTitle()}"
                self.projFilterCB.addItem(lbl, p.getProjId())
                self.projCB.addItem(lbl, p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))
        for cb in (self.projFilterCB, self.projCB):
            cb.blockSignals(False)

    def _reload_model_cb(self):
        cur = self.modelCB.currentData()
        self.modelCB.blockSignals(True)
        self.modelCB.clear()

        self.modelCB.addItem(_SEP_BASE)
        self.modelCB.model().item(self.modelCB.count()-1).setEnabled(False)

        skills = list_for_ui()
        for s in skills:
            if s["is_base"]:
                self.modelCB.addItem(s["label"], s["skill_id"])

        self.modelCB.addItem(_SEP_SKILLS)
        self.modelCB.model().item(self.modelCB.count()-1).setEnabled(False)

        lab_skills = [s for s in skills if not s["is_base"]]
        if lab_skills:
            for s in lab_skills:
                self.modelCB.addItem(s["label"], s["skill_id"])
        else:
            idx = self.modelCB.count()
            self.modelCB.addItem('  (no active lab skills)')
            self.modelCB.model().item(idx).setEnabled(False)

        restore = self.modelCB.findData(cur)
        self.modelCB.setCurrentIndex(restore if restore >= 0 else 1)
        self.modelCB.blockSignals(False)
        self._update_ip_label()

    def refresh_lookups(self):
        """Called by MainWindow when ProjectTab or KnowledgeTab saves."""
        registry_refresh()
        self._reload_project_cb()
        self._reload_model_cb()

    # ── IP label ─────────────────────────────────────────────

    def _update_ip_label(self):
        skill_id = self.modelCB.currentData()
        if not skill_id:
            self.ipLabel.setText('IP: —')
            return
        skill = get(skill_id)
        if skill:
            owner = skill.owner
            color = IP_COLOR.get(owner, TXT_M)
            self.ipLabel.setStyleSheet(
                f'color:{color};font-weight:700;font-size:11px;')
            self.ipLabel.setText(
                f'IP ownership: {owner.upper()}   '
                f'{"(BioAgent exclusive)" if owner=="platform" else "(lab data contributed)"}'
            )

    def _model_changed(self, _):
        self._update_ip_label()
        skill_id = self.modelCB.currentData()
        mapping = {
            'LocalLLM-DNABERT-2': 'DNA Variant',
            'LocalLLM-ESM-2':     'Protein FASTA',
            'LocalLLM-PPI':       'PPI Antibody–Antigen',
            'LocalLLM-RAG':       'Literature RAG',
        }
        suggested = mapping.get(skill_id)
        if suggested and suggested in self._type_btns:
            self._type_btns[suggested].setChecked(True)
            self.inputBox.setPlaceholderText(TYPE_PH[suggested])

    # ── Type pill ────────────────────────────────────────────

    def _type_pill_clicked(self, btn):
        typ = next(t for t, b in self._type_btns.items() if b is btn)
        self.inputBox.setPlaceholderText(TYPE_PH.get(typ, ''))
        default_map = {
            'DNA Variant':          'LocalLLM-DNABERT-2',
            'Protein FASTA':        'LocalLLM-ESM-2',
            'PPI Antibody–Antigen': 'LocalLLM-PPI',
            'Literature RAG':       'LocalLLM-RAG',
        }
        skill_id = default_map.get(typ)
        if skill_id:
            idx = self.modelCB.findData(skill_id)
            if idx >= 0:
                self.modelCB.setCurrentIndex(idx)

    # ── Run inference ─────────────────────────────────────────

    def _run(self):
        inp = self.inputBox.toPlainText().strip()
        if not inp:
            QMessageBox.warning(self, 'Input', 'Provide input data.'); return

        skill_id = self.modelCB.currentData()
        if not skill_id:
            QMessageBox.warning(self, 'Model', 'Select a model/skill.'); return

        proj_id = self.projCB.currentData()
        try:
            ctx     = ProjectContext.load(proj_id) if proj_id else ProjectContext.load("UNKNOWN")
            context = ctx.to_dict()
        except Exception:
            context = {"project_id": proj_id or ""}

        self.runButton.setEnabled(False)
        self.progressBar.setVisible(True)
        self.resultBox.setPlainText('Running inference…')

        self._worker = InferenceWorker(skill_id, inp, context)
        self._worker.finished.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_result(self, result):
        """Called in main thread when inference completes."""
        self.progressBar.setVisible(False)
        self.runButton.setEnabled(True)
        self.resultBox.setPlainText(result.to_display_text())

        proj_id = self.projCB.currentData()
        inp     = self.inputBox.toPlainText().strip()
        typ     = next((t for t, b in self._type_btns.items()
                        if b.isChecked()), 'Unknown')
        try:
            jid = f"INF-{self.dao.count() + 1:03d}"
            rec = InferenceRecord(
                jid, typ, result.skill_id, proj_id,
                (inp[:42] + '…') if len(inp) > 42 else inp,
                result.to_summary_line(),
                str(datetime.now().strftime('%Y-%m-%d %H:%M')),
            )
            # Attach extras so DAO can persist them
            rec.confidence = result.confidence
            rec.ip_owner   = result.ip_owner

            # Pass full_output for provenance storage
            self.dao.insert(rec, full_output=result.full_output)

            # L0: log to audit chain with IP owner
            AuditChain.log(
                user_id     = "system",
                action      = "INFERENCE",
                entity_type = "inference",
                entity_id   = jid,
                detail      = (f"type={typ} skill={result.skill_id} "
                               f"conf={result.confidence:.2f}"),
                project_id  = proj_id,
                ip_owner    = result.ip_owner,
            )
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return

        self.data_changed.emit()
        self._refresh_history()

    def _on_error(self, msg: str):
        self.progressBar.setVisible(False)
        self.runButton.setEnabled(True)
        self.resultBox.setPlainText(f'[ERROR]\n{msg}')

    # ── Audit chain verify ────────────────────────────────────

    def _verify_chain(self):
        try:
            ok, msg = AuditChain.verify_chain(limit=500)
        except Exception as e:
            QMessageBox.warning(self, 'Audit', str(e)); return
        icon = '✅' if ok else '❌'
        QMessageBox.information(self, 'Audit Chain Integrity',
                                f'{icon}  {msg}')

    # ── Full result dialog (double-click) ─────────────────────

    def _open_result_dialog(self, row: int, col: int):
        """Double-click a history row → open full result viewer."""
        inf_id_item = self.histTbl.item(row, 0)
        if not inf_id_item:
            return
        try:
            records = self.dao.get_all()
            record  = next((r for r in records
                            if r.getInfId() == inf_id_item.text()), None)
            if not record:
                return
            proj_id = record.getProjectId()
            project = None
            if proj_id:
                project = next((p for p in self.project_dao.get_all()
                                if p.getProjId() == proj_id), None)
            from gui.tabs.inference_result_dialog import InferenceResultDialog
            dlg = InferenceResultDialog(record, project, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

    # ── Export project report ─────────────────────────────────

    def _export_project_report(self):
        """Export all inference results for selected project as PDF."""
        proj_id = self.projFilterCB.currentData()
        try:
            records = (self.dao.get_by_project(proj_id)
                       if proj_id else self.dao.get_all())
            if not records:
                QMessageBox.information(
                    self, 'No Data',
                    'No inference records found for selected project.')
                return

            project    = None
            grants     = []
            hypotheses = []
            if proj_id:
                project = next((p for p in self.project_dao.get_all()
                                if p.getProjId() == proj_id), None)
                from dao.dao_grant      import GrantDAO
                from dao.dao_hypothesis import HypothesisDAO
                grants     = [g for g in GrantDAO().get_all()
                              if g.getProjectId() == proj_id]
                hypotheses = HypothesisDAO().get_by_project(proj_id)

            default_name = f"BioAgent_{proj_id or 'All'}_Report.pdf"
            path, _ = QFileDialog.getSaveFileName(
                self, 'Save PDF Report', default_name,
                'PDF Files (*.pdf)')
            if not path:
                return

            from core.report_generator import ReportGenerator
            out = ReportGenerator.generate_project_report(
                project_id = proj_id or "ALL",
                records    = records,
                project    = project,
                grants     = grants,
                hypotheses = hypotheses,
                output_dir = os.path.dirname(path) or ".",
            )
            if out != path:
                shutil.move(out, path)
            QMessageBox.information(
                self, 'Report Exported', f'PDF saved:\n{path}')
        except Exception as e:
            QMessageBox.warning(self, 'Export Error', str(e))

    # ── History ───────────────────────────────────────────────

    def _refresh_history(self):
        try:
            history = self.dao.get_all()
            titles  = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.histTbl.setRowCount(len(history))
        for r, h in enumerate(history):
            for c, v in enumerate([
                h.getInfId(), h.getType(), h.getModel(),
                getattr(h, 'ip_owner', '—'),
                h.getInput(), h.getResultSummary(),
                titles.get(h.getProjectId(), h.getProjectId() or '—'),
                h.getTimestamp(),
            ]):
                self.histTbl.setItem(r, c, QTableWidgetItem(str(v)))

    def _search(self):
        typ_f  = self.typeFCB.currentData()
        proj_f = self.projFilterCB.currentData()
        try:
            history = self.dao.get_all()
            titles  = self.project_dao.get_titles()
            if typ_f:
                history = [h for h in history if h.getType() == typ_f]
            if proj_f:
                history = [h for h in history if h.getProjectId() == proj_f]
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.histTbl.setRowCount(len(history))
        for r, h in enumerate(history):
            for c, v in enumerate([
                h.getInfId(), h.getType(), h.getModel(),
                getattr(h, 'ip_owner', '—'),
                h.getInput(), h.getResultSummary(),
                titles.get(h.getProjectId(), '—'), h.getTimestamp(),
            ]):
                self.histTbl.setItem(r, c, QTableWidgetItem(str(v)))

    def _clear_search(self):
        self.typeFCB.setCurrentIndex(0)
        self.projFilterCB.setCurrentIndex(0)
        self._refresh_history()

    def _reset_input(self):
        self.inputBox.setPlainText('')
        self.resultBox.setPlainText('')