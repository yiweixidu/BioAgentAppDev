# gui/tabs/knowledge_tab.py
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QSpinBox, QGridLayout, QHBoxLayout)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import pyqtSignal
from datetime import date
from gui.ui_helpers import card, scroll_wrap, setup_table, AMBER, TEAL, GREEN, RED, PURP, TXT_M
from dao.dao_model_skill       import ModelSkillDAO
from dao.dao_project           import ProjectDAO
from dao.dao_audit             import AuditDAO
from dao.dao_options           import OptionsDAO
from models.model_skill        import ModelSkill
from gui.manage_options_dialog import ManageOptionsDialog
from config.db_config          import MANAGE_ROLES

# ---------------------------------------------------------------------------
# Role that controls whether "Manage options..." appears in dropdowns.
# In production, replace with the value from the active login session.
# ---------------------------------------------------------------------------
CURRENT_USER_ROLE = 'admin'
MANAGE_ITEM       = '⚙  Manage options...'

STATUS_CLR = {'active': TEAL, 'inactive': TXT_M}

# ---------------------------------------------------------------------------
# Fine-tuning methods seeded into app_options on first run.
# Stored under category='finetune_method'.
# ---------------------------------------------------------------------------
DEFAULT_FINETUNE_METHODS = [
    'LoRA',
    'QLoRA',
    'Prefix Tuning',
    'IA³',
    'Adapter',
    'Full Fine-Tuning',
]

# ---------------------------------------------------------------------------
# LoRA adapter versions seeded into app_options on first run.
# Stored under category='lora_version'.
# Visible only when the selected fine-tuning method is 'LoRA'.
# ---------------------------------------------------------------------------
DEFAULT_LORA_VERSIONS = [
    'flu-ha-v3',
    'flu-ha-v4',
    'oncology-somatic-v2',
    'ppi-base-v1',
]

# ---------------------------------------------------------------------------
# EvalBus schema per fine-tuning method.
#
# Structure:
#   EVALBUS_SCHEMA[method] = {
#       'headers': [col0_label, col1_label, ...],   # first col is always 'Model'
#       'highlight_col': int,                        # column index rendered green/red
#       'highlight_positive': str,                   # prefix that means "good" ('+' or '>')
#       'rows': [
#           {'model': str, col1_key: value, ...},
#       ]
#   }
#
# 'highlight_col' is 0-based within the full column list (including 'Model').
# Values that start with 'highlight_positive' are coloured GREEN; others RED.
# ---------------------------------------------------------------------------
EVALBUS_SCHEMA = {
    'LoRA': {
        'headers':           ['Model', 'Pearson r', 'AUC', 'vs Baseline', 'Trainable %'],
        'highlight_col':     3,
        'highlight_positive': '+',
        'rows': [
            {'model': 'DNABERT-2',     'Pearson r': '0.74', 'AUC': '0.89', 'vs Baseline': '+0.03', 'Trainable %': '0.8%'},
            {'model': 'ESM-2',         'Pearson r': '0.81', 'AUC': '0.93', 'vs Baseline': '+0.05', 'Trainable %': '0.6%'},
            {'model': 'PPI Predictor', 'Pearson r': '0.68', 'AUC': '0.86', 'vs Baseline': '+0.02', 'Trainable %': '1.1%'},
        ],
    },
    'QLoRA': {
        'headers':           ['Model', 'AUC', 'Perplexity', 'Memory (GB)', 'vs Baseline'],
        'highlight_col':     4,
        'highlight_positive': '+',
        'rows': [
            {'model': 'DNABERT-2',     'AUC': '0.87', 'Perplexity': '3.21', 'Memory (GB)': '6.4',  'vs Baseline': '+0.01'},
            {'model': 'ESM-2',         'AUC': '0.91', 'Perplexity': '2.88', 'Memory (GB)': '8.1',  'vs Baseline': '+0.03'},
            {'model': 'PPI Predictor', 'AUC': '0.84', 'Perplexity': '4.05', 'Memory (GB)': '5.9',  'vs Baseline': '-0.01'},
        ],
    },
    'Prefix Tuning': {
        'headers':           ['Model', 'Pearson r', 'AUC', 'Prefix Length', 'vs Full FT'],
        'highlight_col':     4,
        'highlight_positive': '+',
        'rows': [
            {'model': 'DNABERT-2',     'Pearson r': '0.71', 'AUC': '0.85', 'Prefix Length': '20', 'vs Full FT': '-0.04'},
            {'model': 'ESM-2',         'Pearson r': '0.78', 'AUC': '0.90', 'Prefix Length': '30', 'vs Full FT': '-0.02'},
            {'model': 'PPI Predictor', 'Pearson r': '0.65', 'AUC': '0.82', 'Prefix Length': '20', 'vs Full FT': '-0.05'},
        ],
    },
    'IA³': {
        'headers':           ['Model', 'AUC', 'F1 (few-shot)', 'vs Zero-shot', 'Trainable %'],
        'highlight_col':     3,
        'highlight_positive': '+',
        'rows': [
            {'model': 'DNABERT-2',     'AUC': '0.83', 'F1 (few-shot)': '0.76', 'vs Zero-shot': '+0.12', 'Trainable %': '0.01%'},
            {'model': 'ESM-2',         'AUC': '0.88', 'F1 (few-shot)': '0.82', 'vs Zero-shot': '+0.15', 'Trainable %': '0.01%'},
            {'model': 'PPI Predictor', 'AUC': '0.80', 'F1 (few-shot)': '0.71', 'vs Zero-shot': '+0.09', 'Trainable %': '0.01%'},
        ],
    },
    'Adapter': {
        'headers':           ['Model', 'Pearson r', 'AUC', 'vs Baseline', 'Adapter (M params)'],
        'highlight_col':     3,
        'highlight_positive': '+',
        'rows': [
            {'model': 'DNABERT-2',     'Pearson r': '0.73', 'AUC': '0.87', 'vs Baseline': '+0.01', 'Adapter (M params)': '2.1'},
            {'model': 'ESM-2',         'Pearson r': '0.80', 'AUC': '0.92', 'vs Baseline': '+0.04', 'Adapter (M params)': '3.4'},
            {'model': 'PPI Predictor', 'Pearson r': '0.67', 'AUC': '0.85', 'vs Baseline': '+0.02', 'Adapter (M params)': '1.8'},
        ],
    },
    'Full Fine-Tuning': {
        'headers':           ['Model', 'Pearson r', 'AUC', 'vs Baseline', 'Epochs', 'GPU hrs'],
        'highlight_col':     3,
        'highlight_positive': '+',
        'rows': [
            {'model': 'DNABERT-2',     'Pearson r': '0.77', 'AUC': '0.91', 'vs Baseline': '+0.05', 'Epochs': '10', 'GPU hrs': '4.2'},
            {'model': 'ESM-2',         'Pearson r': '0.83', 'AUC': '0.95', 'vs Baseline': '+0.07', 'Epochs': '8',  'GPU hrs': '6.8'},
            {'model': 'PPI Predictor', 'Pearson r': '0.70', 'AUC': '0.88', 'vs Baseline': '+0.05', 'Epochs': '12', 'GPU hrs': '3.9'},
        ],
    },
}

# Fallback schema shown when the selected method has no entry in EVALBUS_SCHEMA.
EVALBUS_FALLBACK = {
    'headers':           ['Model', 'Pearson r', 'AUC', 'vs Baseline'],
    'highlight_col':     3,
    'highlight_positive': '+',
    'rows': [],
}


class KnowledgeTab(QWidget):
    # Emitted after any successful add / update / delete.
    # MainWindow connects this to InferenceTab.refresh_lookups so the
    # model/skill picker reflects the latest active skills immediately.
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.dao         = ModelSkillDAO()
        self.project_dao = ProjectDAO()
        self.audit_dao   = AuditDAO()
        self.options_dao = OptionsDAO()

        # Seed default options on first run if the DB categories are empty.
        self._seed_defaults()

        # ------------Labels------------
        self.projFLabel   = QLabel('Project Filter:')
        self.statFLabel   = QLabel('Status Filter:')
        self.idLabel      = QLabel('Skill ID:')
        self.projLabel    = QLabel('Project:')
        self.methodLabel  = QLabel('Fine-tune Method:')
        self.loraVerLabel = QLabel('LoRA Version:')       # shown only when LoRA selected
        self.benchLabel   = QLabel('Benchmark:')
        self.thrLabel     = QLabel('Threshold:')
        self.statusLabel  = QLabel('Status:')

        # ------------Input / Output------------
        self.inputIdLE    = QLineEdit()
        self.inputIdLE.setPlaceholderText('Auto-generated')
        self.inputIdLE.setReadOnly(True)

        self.inputBenchLE = QLineEdit()
        self.inputBenchLE.setPlaceholderText('e.g. HA_binding_eval')

        self.thrSB = QSpinBox()
        self.thrSB.setRange(50, 1000)
        self.thrSB.setValue(200)

        # Filter dropdowns (search card)
        self.projFilterCB = QComboBox()
        self.projFilterCB.addItem('All Projects', None)
        self.statFilterCB = QComboBox()
        self.statFilterCB.addItems(['All', 'active', 'inactive'])

        # Form dropdowns
        self.projCB   = QComboBox()
        self.statusCB = QComboBox()
        self.statusCB.addItems(['active', 'inactive'])

        # Fine-tune method dropdown — options managed via app_options table.
        self.methodCB = QComboBox()
        self._reload_method_cb()

        # LoRA version dropdown — options managed via app_options table.
        # Visible only when methodCB current text == 'LoRA'.
        self.loraVersionCB = QComboBox()
        self._reload_lora_version_cb()

        # Populate project lists
        try:
            for p in self.project_dao.get_all():
                label = f"{p.getProjId()} – {p.getTitle()}"
                self.projFilterCB.addItem(label, p.getProjId())
                self.projCB.addItem(label, p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))

        # ------------Buttons------------
        self.searchButton = QPushButton('🔍  Search')
        self.clearButton  = QPushButton('Clear')
        self.addButton    = QPushButton('➕  Add')
        self.addButton.setObjectName('primaryButton')
        self.updateButton = QPushButton('✔  Update Status')
        self.updateButton.setObjectName('primaryButton')
        self.deleteButton = QPushButton('🗑  Delete')
        self.deleteButton.setObjectName('dangerButton')
        self.resetButton  = QPushButton('Reset Form')

        # ------------Tables------------
        self.table = QTableWidget()
        setup_table(self.table,
            ['ID', 'Fine-tune Method', 'Project', 'LoRA Version',
             'Threshold', 'Benchmark', 'Status', 'Loaded'], 2)

        # EvalBus table — columns are rebuilt dynamically by _populate_evalbus().
        self.evalTbl = QTableWidget()
        self.evalTbl.setMaximumHeight(130)
        self.evalTbl.setAlternatingRowColors(True)
        self.evalTbl.verticalHeader().setVisible(False)
        self.evalTbl.setShowGrid(False)

        # ------------Signals------------
        self.searchButton.clicked.connect(self.search_button_was_clicked)
        self.clearButton.clicked.connect(self.clear_button_was_clicked)
        self.addButton.clicked.connect(self.add_button_was_clicked)
        self.updateButton.clicked.connect(self.update_button_was_clicked)
        self.deleteButton.clicked.connect(self.delete_button_was_clicked)
        self.resetButton.clicked.connect(self.reset_button_was_clicked)
        self.table.cellClicked.connect(self.table_row_was_clicked)
        self.methodCB.currentIndexChanged.connect(self.method_cb_changed)
        self.loraVersionCB.currentIndexChanged.connect(self.lora_version_cb_changed)

        # ------------Layout------------
        _, layout = scroll_wrap(self)

        # Search card
        srch_c, sl = card('🔍  Search Model Skills', border=PURP)
        srch_grid = QGridLayout()
        srch_grid.addWidget(self.projFLabel,    0, 0)
        srch_grid.addWidget(self.projFilterCB,  0, 1)
        srch_grid.addWidget(self.statFLabel,    0, 2)
        srch_grid.addWidget(self.statFilterCB,  0, 3)
        srch_grid.addWidget(self.searchButton,  0, 4)
        srch_grid.addWidget(self.clearButton,   0, 5)
        sl.addLayout(srch_grid)
        layout.addWidget(srch_c)

        # Registry table card
        tbl_c, tl = card('📦  Model Skill Registry', border=TEAL)
        tl.addWidget(self.table)
        layout.addWidget(tbl_c)

        # Add / Edit card
        form_c, fl = card('✏️  Add / Edit Model Skill', border=AMBER)
        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(10)

        # Row 0: Skill ID | Project
        form_grid.addWidget(self.idLabel,       0, 0)
        form_grid.addWidget(self.inputIdLE,     0, 1)
        form_grid.addWidget(self.projLabel,     0, 2)
        form_grid.addWidget(self.projCB,        0, 3)

        # Row 1: Fine-tune method | LoRA version (hidden unless LoRA is selected)
        form_grid.addWidget(self.methodLabel,   1, 0)
        form_grid.addWidget(self.methodCB,      1, 1)
        form_grid.addWidget(self.loraVerLabel,  1, 2)
        form_grid.addWidget(self.loraVersionCB, 1, 3)

        # Row 2: Benchmark | Threshold
        form_grid.addWidget(self.benchLabel,    2, 0)
        form_grid.addWidget(self.inputBenchLE,  2, 1)
        form_grid.addWidget(self.thrLabel,      2, 2)
        form_grid.addWidget(self.thrSB,         2, 3)

        # Row 3: Status
        form_grid.addWidget(self.statusLabel,   3, 0)
        form_grid.addWidget(self.statusCB,      3, 1)

        fl.addLayout(form_grid)

        btn_row = QHBoxLayout()
        for b in [self.addButton, self.updateButton,
                  self.deleteButton, self.resetButton]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        fl.addLayout(btn_row)
        layout.addWidget(form_c)

        # EvalBus card — title updated dynamically via _populate_evalbus()
        self.evalCard, el = card('📊  EvalBus Benchmark Scores', border=GREEN)
        el.addWidget(self.evalTbl)
        # Keep a reference to the card's title label so we can update it.
        # The card() helper places a QLabel as the second child of the header's
        # layout; we locate it by walking the widget tree.
        self._evalbus_title_lbl = self.evalCard.findChild(QLabel)
        layout.addWidget(self.evalCard)

        layout.addStretch()

        # Sync visibility and paint initial EvalBus table before first show.
        self._sync_lora_row_visibility()
        self._populate_evalbus()
        self._refresh()

    # -----------------------------------------------------------------------
    # First-run seeding
    # -----------------------------------------------------------------------
    def _seed_defaults(self):
        """Write default options to app_options if the DB category is still empty."""
        if not self.options_dao.get_by_category('finetune_method'):
            for m in DEFAULT_FINETUNE_METHODS:
                try:
                    self.options_dao.add('finetune_method', m)
                except Exception:
                    pass

        if not self.options_dao.get_by_category('lora_version'):
            for v in DEFAULT_LORA_VERSIONS:
                try:
                    self.options_dao.add('lora_version', v)
                except Exception:
                    pass

    # -----------------------------------------------------------------------
    # Dropdown reload helpers
    # -----------------------------------------------------------------------
    def _reload_method_cb(self):
        """Reload fine-tuning method options from app_options (category='finetune_method')."""
        current = self.methodCB.currentText()
        self.methodCB.blockSignals(True)
        self.methodCB.clear()
        opts = self.options_dao.get_by_category('finetune_method')
        self.methodCB.addItems(opts)
        if CURRENT_USER_ROLE in MANAGE_ROLES:
            self.methodCB.insertSeparator(len(opts))
            self.methodCB.addItem(MANAGE_ITEM)
        idx = self.methodCB.findText(current)
        if idx >= 0:
            self.methodCB.setCurrentIndex(idx)
        self.methodCB.blockSignals(False)

    def _reload_lora_version_cb(self):
        """Reload LoRA version options from app_options (category='lora_version')."""
        current = self.loraVersionCB.currentText()
        self.loraVersionCB.blockSignals(True)
        self.loraVersionCB.clear()
        opts = self.options_dao.get_by_category('lora_version')
        self.loraVersionCB.addItems(opts)
        if CURRENT_USER_ROLE in MANAGE_ROLES:
            self.loraVersionCB.insertSeparator(len(opts))
            self.loraVersionCB.addItem(MANAGE_ITEM)
        idx = self.loraVersionCB.findText(current)
        if idx >= 0:
            self.loraVersionCB.setCurrentIndex(idx)
        self.loraVersionCB.blockSignals(False)

    def _sync_lora_row_visibility(self):
        """Show the LoRA version label+dropdown only when method is 'LoRA'."""
        is_lora = self.methodCB.currentText() == 'LoRA'
        self.loraVerLabel.setVisible(is_lora)
        self.loraVersionCB.setVisible(is_lora)

    def _get_lora_version_value(self):
        """
        Return the value to store in the lora_version DB column:
          'LoRA' method  -> selected version string (e.g. 'flu-ha-v4')
          any other      -> empty string
        """
        if self.methodCB.currentText() == 'LoRA':
            v = self.loraVersionCB.currentText()
            return '' if v == MANAGE_ITEM else v
        return ''

    # -----------------------------------------------------------------------
    # EvalBus — dynamic columns
    # -----------------------------------------------------------------------
    def _populate_evalbus(self):
        """
        Rebuild the EvalBus table to match the currently selected fine-tune
        method.  Column headers and highlighted column are read from
        EVALBUS_SCHEMA; an empty-row fallback is shown for unknown methods.
        """
        method = self.methodCB.currentText()
        if method == MANAGE_ITEM or method not in EVALBUS_SCHEMA:
            schema = EVALBUS_FALLBACK
        else:
            schema = EVALBUS_SCHEMA[method]

        headers      = schema['headers']
        hi_col       = schema['highlight_col']
        hi_positive  = schema['highlight_positive']
        rows         = schema['rows']

        # Rebuild columns
        self.evalTbl.setColumnCount(len(headers))
        self.evalTbl.setHorizontalHeaderLabels(headers)
        self.evalTbl.setRowCount(len(rows))

        from PyQt6.QtWidgets import QHeaderView, QAbstractItemView
        hdr = self.evalTbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.evalTbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.evalTbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        for r, row_data in enumerate(rows):
            # Column 0 is always 'model'
            values = [row_data.get('model', '')] + [
                str(row_data.get(h, '')) for h in headers[1:]
            ]
            for c, v in enumerate(values):
                it = QTableWidgetItem(v)
                if c == hi_col:
                    positive = str(v).startswith(hi_positive)
                    it.setForeground(QBrush(QColor(GREEN if positive else RED)))
                self.evalTbl.setItem(r, c, it)

        # Update the card title to reflect the active method
        if self._evalbus_title_lbl:
            self._evalbus_title_lbl.setText(
                f'📊  EvalBus — {method}' if method and method != MANAGE_ITEM
                else '📊  EvalBus Benchmark Scores'
            )

    # -----------------------------------------------------------------------
    # Signals
    # -----------------------------------------------------------------------
    def method_cb_changed(self, index):
        """Handle fine-tune method selection: manage dialog or update EvalBus."""
        if self.methodCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('finetune_method', 'Manage Fine-tune Methods', self)
            dlg.exec()
            self._reload_method_cb()
        self._sync_lora_row_visibility()
        self._populate_evalbus()           # refresh EvalBus for the new method

    def lora_version_cb_changed(self, index):
        """Open manage dialog when the user picks the manage item."""
        if self.loraVersionCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('lora_version', 'Manage LoRA Versions', self)
            dlg.exec()
            self._reload_lora_version_cb()

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------
    def _refresh(self):
        self._reload_method_cb()
        self._reload_lora_version_cb()
        self._sync_lora_row_visibility()
        try:
            skills = self.dao.get_all()
            titles = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(skills, titles)

    def _populate_table(self, skills, titles=None):
        if titles is None:
            try:
                titles = self.project_dao.get_titles()
            except Exception:
                titles = {}
        self.table.setRowCount(len(skills))
        for r, s in enumerate(skills):
            for c, v in enumerate([
                s.getSkillId(),
                s.getName(),                                        # fine-tune method
                titles.get(s.getProjectId(), s.getProjectId()),
                s.getLoraVersion(),                                 # version or ''
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

    def table_row_was_clicked(self, row, col):
        """Populate the edit form from the clicked table row."""
        self.inputIdLE.setText(self.table.item(row, 0).text())

        # Fine-tune method — also refreshes EvalBus via signal
        method = self.table.item(row, 1).text()
        idx = self.methodCB.findText(method)
        if idx >= 0:
            self.methodCB.setCurrentIndex(idx)   # triggers method_cb_changed
        self._sync_lora_row_visibility()

        # LoRA version (only meaningful when method == 'LoRA')
        lora_ver = self.table.item(row, 3).text()
        if method == 'LoRA' and lora_ver:
            idx = self.loraVersionCB.findText(lora_ver)
            if idx >= 0:
                self.loraVersionCB.setCurrentIndex(idx)

        # Project
        proj_title = self.table.item(row, 2).text()
        for i in range(self.projCB.count()):
            if proj_title in self.projCB.itemText(i):
                self.projCB.setCurrentIndex(i); break

        # Threshold
        try:
            self.thrSB.setValue(int(self.table.item(row, 4).text()))
        except Exception:
            pass

        self.inputBenchLE.setText(self.table.item(row, 5).text())

        # Status
        idx = self.statusCB.findText(self.table.item(row, 6).text())
        if idx >= 0:
            self.statusCB.setCurrentIndex(idx)

    # -----------------------------------------------------------------------
    # Search / clear
    # -----------------------------------------------------------------------
    def search_button_was_clicked(self):
        pid  = self.projFilterCB.currentData()
        stat = self.statFilterCB.currentText()
        try:
            skills = self.dao.get_all()
            titles = self.project_dao.get_titles()
            if pid:
                skills = [s for s in skills if s.getProjectId() == pid]
            if stat != 'All':
                skills = [s for s in skills if s.getStatus() == stat]
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(skills, titles)

    def clear_button_was_clicked(self):
        self.projFilterCB.setCurrentIndex(0)
        self.statFilterCB.setCurrentIndex(0)
        self._refresh()

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------
    def add_button_was_clicked(self):
        method = self.methodCB.currentText()
        if not method or method == MANAGE_ITEM:
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid fine-tune method.'); return

        lora_ver = self._get_lora_version_value()
        if method == 'LoRA' and not lora_ver:
            QMessageBox.warning(self, 'Validation',
                                'LoRA method requires a version selection.'); return

        try:
            nid = f"SK-{self.dao.count() + 1:03d}"
            sk  = ModelSkill(
                nid,
                method,                                            # stored in 'name' column
                self.projCB.currentData(),
                lora_ver,                                          # stored in 'lora_version' column
                self.thrSB.value(),
                self.inputBenchLE.text().strip() or 'default_eval',
                self.statusCB.currentText(),
                str(date.today())
            )
            self.dao.insert(sk)
            detail = method + (f' / {lora_ver}' if lora_ver else '')
            self.audit_dao.add('system', 'ASSIGN_SKILL',
                               f'{nid} -> {sk.getProjectId()}', detail)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return

        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Added', f'{nid} assigned.')

    def update_button_was_clicked(self):
        sid = self.inputIdLE.text().strip()
        if not sid:
            QMessageBox.warning(self, 'Validation', 'Select a row first.'); return
        status = self.statusCB.currentText()
        try:
            self.dao.update_status(sid, status)
            self.audit_dao.add('system', 'SKILL_STATUS', sid, f'-> {status}')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Updated', f'{sid} status -> {status}.')

    def delete_button_was_clicked(self):
        sid = self.inputIdLE.text().strip()
        if not sid:
            QMessageBox.warning(self, 'Validation', 'Select a row first.'); return
        reply = QMessageBox.question(
            self, 'Confirm Delete', f'Delete skill {sid}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            self.dao.delete(sid)
            self.audit_dao.add('system', 'DELETE', sid, 'Removed')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Removed', f'{sid} removed.')

    def reset_button_was_clicked(self):
        self.inputIdLE.setText('')
        self.inputBenchLE.setText('')
        self.thrSB.setValue(200)
        self.methodCB.setCurrentIndex(0)
        self.loraVersionCB.setCurrentIndex(0)
        self.projCB.setCurrentIndex(0)
        self.statusCB.setCurrentIndex(0)
        self._sync_lora_row_visibility()
        self._populate_evalbus()