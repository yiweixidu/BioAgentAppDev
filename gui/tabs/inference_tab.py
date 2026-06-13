# gui/tabs/inference_tab.py
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QTextEdit, QGridLayout,
                             QHBoxLayout, QButtonGroup)
from PyQt6.QtCore import pyqtSignal
from datetime import datetime
from gui.ui_helpers import card, scroll_wrap, setup_table, AMBER, TEAL, GREEN, BLUE, PURP, TXT_M
from dao.dao_inference   import InferenceDAO
from dao.dao_project     import ProjectDAO
from dao.dao_model_skill import ModelSkillDAO
from dao.dao_audit       import AuditDAO
from models.inference_record import InferenceRecord

# ---------------------------------------------------------------------------
# Inference type pill definitions
# ---------------------------------------------------------------------------
TYPES = [
    ('🧬', 'DNA Variant'),
    ('🧪', 'Protein FASTA'),
    ('🤝', 'PPI Antibody–Antigen'),
    ('📚', 'Literature RAG'),
]

TYPE_PH = {
    'DNA Variant':          'chr12:25398284 A>T hg38',
    'Protein FASTA':        '>Ab_VH\nEVQLVESGGG...',
    'PPI Antibody–Antigen': 'VH/VL sequence  +  antigen PDB ID: 6XR8',
    'Literature RAG':       'KRAS G12C inhibitor resistance mechanisms',
}

# ---------------------------------------------------------------------------
# LocalLLM base models — platform-owned, exclusive copyright.
# Labs may NOT share these externally without consent.
# ---------------------------------------------------------------------------
LOCAL_LLM_MODELS = [
    'LocalLLM-DNABERT-2',
    'LocalLLM-ESM-2',
    'LocalLLM-PPI',
    'LocalLLM-RAG',
]

# Default base model suggested when a type pill is selected.
TYPE_DEFAULT_MODEL = {
    'DNA Variant':          'LocalLLM-DNABERT-2',
    'Protein FASTA':        'LocalLLM-ESM-2',
    'PPI Antibody–Antigen': 'LocalLLM-PPI',
    'Literature RAG':       'LocalLLM-RAG',
}

# Mock results — placeholder until real AI inference is wired in.
MOCK = {
    'DNA Variant': (
        'LocalLLM-DNABERT-2  ·  Variant Effect Prediction\n' + '─' * 44 + '\n'
        'Variant:        chr12:25398284 A>T (hg38)\n'
        'Gene:           KRAS  (p.Gly12Cys)\n'
        'Effect score:   -1.83   [95% CI: -2.10, -1.56]\n'
        'Pathogenicity:  LIKELY DAMAGING\n'
        'Provenance:     PMID:38201847  ·  PMID:36754893  ·  PDB:6XR8'),
    'Protein FASTA': (
        'LocalLLM-ESM-2  ·  Binding Affinity\n' + '─' * 44 + '\n'
        'dG binding:     -12.4 kcal/mol\nKd estimate:    2.3 nM\n'
        'Stability:      0.81  (stable)\n'
        'PDB template:   6XR8, 7KDL'),
    'PPI Antibody–Antigen': (
        'LocalLLM-PPI  ·  Interface Scoring\n' + '─' * 44 + '\n'
        'Interaction prob.:  0.92  (HIGH CONFIDENCE)\n'
        'ddG interface:      -3.2 kcal/mol\n'
        'Epitope residues:   27-35, 52-58\n'
        'Provenance:         PDB:6XR8  ·  PMID:38201847'),
    'Literature RAG': (
        'LocalLLM-RAG  ·  FAISS Literature Synthesis\n' + '─' * 44 + '\n'
        '  •  MAPK reactivation (PMID:35039682)\n'
        '  •  Secondary mutations Y96D/H95D (PMID:36521447)\n'
        '  •  SOS1 combination (PMID:37123890)\n'
        'Citation validation:  3/3 sourced'),
}

# Dropdown section-header labels (inserted as disabled items for visual grouping).
_SEP_BASE   = '── Base LocalLLM Models ──'
_SEP_SKILLS = '── Fine-tuned Lab Skills (active) ──'


class InferenceTab(QWidget):
    # Emitted after a successful inference run so MainWindow can forward it.
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.dao         = InferenceDAO()
        self.project_dao = ProjectDAO()
        self.skill_dao   = ModelSkillDAO()
        self.audit_dao   = AuditDAO()

        # ------------Labels (search card)------------
        self.typeFLabel = QLabel('Type Filter:')
        self.projFLabel = QLabel('Project Filter:')

        # ------------Labels (config card)------------
        self.modelLabel = QLabel('AI Model / Skill:')
        self.projLabel  = QLabel('Save to Project:')

        # ------------Input / Output------------
        self.inputBox = QTextEdit()
        self.inputBox.setMaximumHeight(90)

        self.resultBox = QTextEdit()
        self.resultBox.setObjectName('ResultBox')
        self.resultBox.setReadOnly(True)
        self.resultBox.setMinimumHeight(130)
        self.resultBox.setPlaceholderText(
            'Results will appear here after running inference.')

        # Filter dropdowns
        self.typeFCB = QComboBox()
        self.typeFCB.addItem('All Types', None)
        for _, t in TYPES:
            self.typeFCB.addItem(t, t)

        self.projFilterCB = QComboBox()
        self.projFilterCB.addItem('All Projects', None)

        # Combined model + skill picker (rebuilt by _reload_model_cb)
        self.modelCB = QComboBox()

        # Project selector for saving results
        self.projCB = QComboBox()

        # Populate project lists and model picker from DB
        self._reload_project_cb()
        self._reload_model_cb()

        # ------------Type pill buttons------------
        self.btn_group  = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self._type_btns = {}
        for icon, typ in TYPES:
            btn = QPushButton(f'{icon}  {typ}')
            btn.setObjectName('typeBtn')
            btn.setCheckable(True)
            self.btn_group.addButton(btn)
            self._type_btns[typ] = btn
        self._type_btns['DNA Variant'].setChecked(True)

        # ------------Buttons------------
        self.searchButton = QPushButton('🔍  Search History')
        self.clearButton  = QPushButton('Clear')
        self.runButton    = QPushButton('▶  Run Inference')
        self.runButton.setObjectName('primaryButton')
        self.resetButton  = QPushButton('Reset Input')

        # ------------Table------------
        self.histTbl = QTableWidget()
        setup_table(self.histTbl,
            ['Job ID', 'Type', 'Model / Skill', 'Input',
             'Result Summary', 'Project', 'Timestamp'], 4)
        self.histTbl.setMaximumHeight(180)

        # ------------Signals------------
        self.searchButton.clicked.connect(self.search_button_was_clicked)
        self.clearButton.clicked.connect(self.clear_button_was_clicked)
        self.runButton.clicked.connect(self.run_button_was_clicked)
        self.resetButton.clicked.connect(self.reset_button_was_clicked)
        self.btn_group.buttonClicked.connect(self.type_button_was_clicked)

        # ------------Layout------------
        _, layout = scroll_wrap(self)

        # Search card
        srch_c, sl = card('🔍  Search Inference History', border=PURP)
        srch_grid = QGridLayout()
        srch_grid.addWidget(self.typeFLabel,    0, 0)
        srch_grid.addWidget(self.typeFCB,       0, 1)
        srch_grid.addWidget(self.projFLabel,    0, 2)
        srch_grid.addWidget(self.projFilterCB,  0, 3)
        srch_grid.addWidget(self.searchButton,  0, 4)
        srch_grid.addWidget(self.clearButton,   0, 5)
        sl.addLayout(srch_grid)
        layout.addWidget(srch_c)

        # History table card
        hist_c, hl = card('🕐  Inference History', border=TEAL)
        hl.addWidget(self.histTbl)
        layout.addWidget(hist_c)

        # Config card — model/skill picker + project selector
        conf_c, cl = card('🧬  Run New Inference', border=AMBER)
        pill_row = QHBoxLayout()
        pill_row.setSpacing(8)
        for btn in self._type_btns.values():
            pill_row.addWidget(btn)
        pill_row.addStretch()
        cl.addLayout(pill_row)

        conf_grid = QGridLayout()
        conf_grid.addWidget(self.modelLabel, 0, 0)
        conf_grid.addWidget(self.modelCB,    0, 1)
        conf_grid.addWidget(self.projLabel,  0, 2)
        conf_grid.addWidget(self.projCB,     0, 3)
        cl.addLayout(conf_grid)
        layout.addWidget(conf_c)

        # Input card
        inp_c, il = card('📝  Input', border=GREEN)
        self.inputBox.setPlaceholderText(TYPE_PH['DNA Variant'])
        il.addWidget(self.inputBox)
        run_row = QHBoxLayout()
        run_row.addWidget(self.runButton)
        run_row.addWidget(self.resetButton)
        run_row.addStretch()
        il.addLayout(run_row)
        layout.addWidget(inp_c)

        # Result card
        res_c, rl = card('📊  Prediction Result', border=BLUE)
        rl.addWidget(self.resultBox)
        layout.addWidget(res_c)

        layout.addStretch()
        self._refresh_history()

    # -----------------------------------------------------------------------
    # Dropdown reload helpers — stay in sync with ProjectTab / KnowledgeTab
    # -----------------------------------------------------------------------
    def _reload_project_cb(self):
        """Reload project options from the project table (mirrors ProjectTab)."""
        cur_filter = self.projFilterCB.currentData()
        cur_save   = self.projCB.currentData()
        self.projFilterCB.blockSignals(True)
        self.projCB.blockSignals(True)
        self.projFilterCB.clear()
        self.projCB.clear()
        self.projFilterCB.addItem('All Projects', None)
        try:
            for p in self.project_dao.get_all():
                label = f"{p.getProjId()} – {p.getTitle()}"
                self.projFilterCB.addItem(label, p.getProjId())
                self.projCB.addItem(label, p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))
        for i in range(self.projFilterCB.count()):
            if self.projFilterCB.itemData(i) == cur_filter:
                self.projFilterCB.setCurrentIndex(i); break
        for i in range(self.projCB.count()):
            if self.projCB.itemData(i) == cur_save:
                self.projCB.setCurrentIndex(i); break
        self.projFilterCB.blockSignals(False)
        self.projCB.blockSignals(False)

    def _reload_model_cb(self):
        """
        Rebuild the AI model / skill picker.

        Dropdown structure:
          ── Base LocalLLM Models ──        (disabled header)
            🔬  LocalLLM-DNABERT-2
            🔬  LocalLLM-ESM-2
            ...
          ── Fine-tuned Lab Skills ──       (disabled header)
            🛠  SK-001 · LoRA / flu-ha-v3  [PRJ-101]
            🛠  SK-002 · QLoRA             [PRJ-102]
            ...

        Base models: platform-owned, exclusive copyright.
        Skills:      lab-owned, shared copyright, no third-party disclosure.
        Section headers are disabled items used purely for visual grouping.
        """
        cur_text = self.modelCB.currentText()
        self.modelCB.blockSignals(True)
        self.modelCB.clear()

        # Section 1 — base LocalLLM models
        self.modelCB.addItem(_SEP_BASE)
        self.modelCB.model().item(self.modelCB.count() - 1).setEnabled(False)
        for m in LOCAL_LLM_MODELS:
            self.modelCB.addItem(f'🔬  {m}', ('base', m))

        # Section 2 — active fine-tuned skills from model_skill table (KnowledgeTab)
        self.modelCB.addItem(_SEP_SKILLS)
        self.modelCB.model().item(self.modelCB.count() - 1).setEnabled(False)
        try:
            active_skills = self.skill_dao.get_active()
        except Exception:
            active_skills = []

        if active_skills:
            for s in active_skills:
                ver_part = f' / {s.getLoraVersion()}' if s.getLoraVersion() else ''
                label = (f'🛠  {s.getSkillId()} · {s.getName()}{ver_part}'
                         f'  [{s.getProjectId()}]')
                self.modelCB.addItem(label, ('skill', s.getSkillId(), s.getName()))
        else:
            ph_idx = self.modelCB.count()
            self.modelCB.addItem('  (no active skills — assign one in Model Skills tab)')
            self.modelCB.model().item(ph_idx).setEnabled(False)

        # Restore previous selection; fall back to first selectable item (index 1)
        idx = self.modelCB.findText(cur_text)
        self.modelCB.setCurrentIndex(idx if idx >= 0 else 1)
        self.modelCB.blockSignals(False)

    # -----------------------------------------------------------------------
    # Public slot — called by MainWindow when ProjectTab or KnowledgeTab saves
    # -----------------------------------------------------------------------
    def refresh_lookups(self):
        """Re-sync project and model/skill dropdowns without resetting form data."""
        self._reload_project_cb()
        self._reload_model_cb()

    # -----------------------------------------------------------------------
    # History table
    # -----------------------------------------------------------------------
    def _refresh_history(self):
        try:
            history = self.dao.get_all()
            titles  = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(history, titles)

    def _populate_table(self, history, titles=None):
        if titles is None:
            try:
                titles = self.project_dao.get_titles()
            except Exception:
                titles = {}
        self.histTbl.setRowCount(len(history))
        for r, h in enumerate(history):
            for c, v in enumerate([
                h.getInfId(),    h.getType(),   h.getModel(),
                h.getInput(),    h.getResultSummary(),
                titles.get(h.getProjectId(), h.getProjectId()),
                h.getTimestamp()
            ]):
                self.histTbl.setItem(r, c, QTableWidgetItem(str(v)))

    # -----------------------------------------------------------------------
    # Signals
    # -----------------------------------------------------------------------
    def type_button_was_clicked(self, btn):
        typ = next(t for t, b in self._type_btns.items() if b is btn)
        self.inputBox.setPlaceholderText(TYPE_PH.get(typ, 'Enter input...'))

        # Suggest the matching base model only if the user has not picked a skill
        cur_data = self.modelCB.currentData()
        if cur_data is None or (isinstance(cur_data, tuple) and cur_data[0] == 'base'):
            suggested = TYPE_DEFAULT_MODEL.get(typ)
            if suggested:
                for i in range(self.modelCB.count()):
                    if self.modelCB.itemData(i) == ('base', suggested):
                        self.modelCB.setCurrentIndex(i); break

    def search_button_was_clicked(self):
        typ_filter  = self.typeFCB.currentData()
        proj_filter = self.projFilterCB.currentData()
        try:
            history = self.dao.get_all()
            titles  = self.project_dao.get_titles()
            if typ_filter:
                history = [h for h in history if h.getType() == typ_filter]
            if proj_filter:
                history = [h for h in history if h.getProjectId() == proj_filter]
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(history, titles)

    def clear_button_was_clicked(self):
        self.typeFCB.setCurrentIndex(0)
        self.projFilterCB.setCurrentIndex(0)
        self._refresh_history()

    def run_button_was_clicked(self):
        inp = self.inputBox.toPlainText().strip()
        if not inp:
            QMessageBox.warning(self, 'Input', 'Provide input data.'); return

        typ = next(t for t, b in self._type_btns.items() if b.isChecked())
        pid = self.projCB.currentData()

        # Determine human-readable model label for storage
        cur_data = self.modelCB.currentData()
        if isinstance(cur_data, tuple) and cur_data[0] == 'base':
            model_label = cur_data[1]                           # e.g. 'LocalLLM-DNABERT-2'
        elif isinstance(cur_data, tuple) and cur_data[0] == 'skill':
            model_label = f"{cur_data[1]} ({cur_data[2]})"     # e.g. 'SK-001 (LoRA)'
        else:
            model_label = self.modelCB.currentText().strip()

        # Use mock result; replace with real inference call when AI is wired in
        txt = MOCK.get(typ, 'Result unavailable.')
        self.resultBox.setPlainText(txt)

        try:
            jid = f"INF-{self.dao.count() + 1:03d}"
            rec = InferenceRecord(
                jid, typ, model_label, pid,
                (inp[:42] + '…') if len(inp) > 42 else inp,
                txt.split('\n')[2] if '\n' in txt else txt[:50],
                datetime.now().strftime('%Y-%m-%d %H:%M')
            )
            self.dao.insert(rec)
            self.audit_dao.add(model_label, 'INFERENCE', jid,
                               f'Type={typ} · Project={pid}')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return

        self.data_changed.emit()
        self._refresh_history()

    def reset_button_was_clicked(self):
        self.inputBox.setPlainText('')
        self.resultBox.setPlainText('')