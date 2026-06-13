# gui/tabs/hypothesis_tab.py
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QGridLayout, QHBoxLayout, QTextEdit)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import pyqtSignal
from gui.ui_helpers import (card, scroll_wrap, setup_table,
                            AMBER, TEAL, GREEN, RED, BLUE, TXT_S,
                            STATUS_FG, STATUS_ROW_BG, PURP)
from dao.dao_hypothesis  import HypothesisDAO
from dao.dao_project     import ProjectDAO
from dao.dao_researcher  import ResearcherDAO
from dao.dao_audit       import AuditDAO
from models.hypothesis   import Hypothesis


class HypothesisTab(QWidget):
    # Emitted after any successful add / update / delete so MainWindow can
    # forward the signal to other tabs that depend on hypothesis data.
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.dao            = HypothesisDAO()
        self.project_dao    = ProjectDAO()
        self.researcher_dao = ResearcherDAO()
        self.audit_dao      = AuditDAO()

        # ------------Labels------------
        self.projFLabel  = QLabel('Project Filter:')
        self.statFLabel  = QLabel('Status Filter:')
        self.idLabel     = QLabel('Hypothesis ID:')
        self.projLabel   = QLabel('Project:')
        self.textLabel   = QLabel('Hypothesis Text:')
        self.statusLabel = QLabel('Status:')
        self.confLabel   = QLabel('Confidence:')
        self.pmidsLabel  = QLabel('PMIDs:')
        self.noteLabel   = QLabel('Note:')
        self.resLabel    = QLabel('Researcher:')

        # ------------Input / Output------------
        self.inputIdLE    = QLineEdit()
        self.inputIdLE.setPlaceholderText('e.g. H22')
        self.inputTextTE  = QTextEdit()
        self.inputTextTE.setMaximumHeight(60)
        self.inputTextTE.setPlaceholderText('Enter hypothesis text...')
        self.inputConfLE  = QLineEdit()
        self.inputConfLE.setPlaceholderText('0.0 - 1.0')
        self.inputPmidsLE = QLineEdit()
        self.inputPmidsLE.setPlaceholderText('PMID:12345678')
        self.inputNoteLE  = QLineEdit()
        self.inputNoteLE.setPlaceholderText('Observation note')

        # Status dropdown (fixed values)
        self.statusCB = QComboBox()
        self.statusCB.addItems(['supported', 'refuted', 'pending'])

        # Filter dropdowns
        self.projFilterCB = QComboBox()
        self.projFilterCB.addItem('All Projects', None)
        self.statFilterCB = QComboBox()
        self.statFilterCB.addItems(['All Statuses', 'supported', 'refuted', 'pending'])

        # Form dropdowns — linked to ProjectTab and ResearcherTab via DB
        self.projCB = QComboBox()   # mirrors project table
        self.resCB  = QComboBox()   # mirrors researcher table

        self._reload_project_cb()
        self._reload_researcher_cb()

        # ------------Buttons------------
        self.searchButton = QPushButton('🔍  Search')
        self.clearButton  = QPushButton('Clear')
        self.addButton    = QPushButton('➕  Add')
        self.addButton.setObjectName('primaryButton')
        self.updateButton = QPushButton('✔  Update')
        self.updateButton.setObjectName('primaryButton')
        self.deleteButton = QPushButton('🗑  Delete')
        self.deleteButton.setObjectName('dangerButton')
        self.resetButton  = QPushButton('Reset Form')

        # ------------Table------------
        self.table = QTableWidget()
        setup_table(self.table,
            ['ID', 'Hypothesis Text', 'Status', 'Confidence',
             'PMIDs', 'Project', 'Note'], 1)

        # ------------Signals------------
        self.searchButton.clicked.connect(self.search_button_was_clicked)
        self.clearButton.clicked.connect(self.clear_button_was_clicked)
        self.addButton.clicked.connect(self.add_button_was_clicked)
        self.updateButton.clicked.connect(self.update_button_was_clicked)
        self.deleteButton.clicked.connect(self.delete_button_was_clicked)
        self.resetButton.clicked.connect(self.reset_button_was_clicked)
        self.table.cellClicked.connect(self.table_row_was_clicked)

        # ------------Layout------------
        _, layout = scroll_wrap(self)

        # Search card
        srch_c, sl = card('🔍  Search Hypotheses', border=PURP)
        srch_grid = QGridLayout()
        srch_grid.addWidget(self.projFLabel,    0, 0)
        srch_grid.addWidget(self.projFilterCB,  0, 1)
        srch_grid.addWidget(self.statFLabel,    0, 2)
        srch_grid.addWidget(self.statFilterCB,  0, 3)
        srch_grid.addWidget(self.searchButton,  0, 4)
        srch_grid.addWidget(self.clearButton,   0, 5)
        sl.addLayout(srch_grid)
        layout.addWidget(srch_c)

        # Table card
        tbl_c, tl = card('📋  Hypothesis List', border=TEAL)
        tl.addWidget(self.table)
        layout.addWidget(tbl_c)

        # Add / Edit card
        form_c, fl = card('✏️  Add / Edit Hypothesis', border=AMBER)
        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(10)

        # Row 0: Hypothesis ID | Project (linked to ProjectTab)
        form_grid.addWidget(self.idLabel,      0, 0)
        form_grid.addWidget(self.inputIdLE,    0, 1)
        form_grid.addWidget(self.projLabel,    0, 2)
        form_grid.addWidget(self.projCB,       0, 3)

        # Row 1: Hypothesis text spanning full width
        form_grid.addWidget(self.textLabel,    1, 0)
        form_grid.addWidget(self.inputTextTE,  1, 1, 1, 3)

        # Row 2: Status | Confidence
        form_grid.addWidget(self.statusLabel,  2, 0)
        form_grid.addWidget(self.statusCB,     2, 1)
        form_grid.addWidget(self.confLabel,    2, 2)
        form_grid.addWidget(self.inputConfLE,  2, 3)

        # Row 3: PMIDs | Note
        form_grid.addWidget(self.pmidsLabel,   3, 0)
        form_grid.addWidget(self.inputPmidsLE, 3, 1)
        form_grid.addWidget(self.noteLabel,    3, 2)
        form_grid.addWidget(self.inputNoteLE,  3, 3)

        # Row 4: Researcher (linked to ResearcherTab)
        form_grid.addWidget(self.resLabel,     4, 0)
        form_grid.addWidget(self.resCB,        4, 1)

        fl.addLayout(form_grid)

        btn_row = QHBoxLayout()
        for b in [self.addButton, self.updateButton,
                  self.deleteButton, self.resetButton]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        fl.addLayout(btn_row)
        layout.addWidget(form_c)

        layout.addStretch()
        self._refresh()

    # -----------------------------------------------------------------------
    # Dropdown reload helpers — stay in sync with ProjectTab / ResearcherTab
    # -----------------------------------------------------------------------
    def _reload_project_cb(self):
        """Reload project options from the project table (mirrors ProjectTab)."""
        cur_data = self.projCB.currentData()
        self.projCB.blockSignals(True)
        self.projFilterCB.blockSignals(True)
        self.projCB.clear()
        self.projFilterCB.clear()
        self.projFilterCB.addItem('All Projects', None)
        try:
            for p in self.project_dao.get_all():
                label = f"{p.getProjId()} – {p.getTitle()}"
                self.projFilterCB.addItem(label, p.getProjId())
                self.projCB.addItem(label, p.getProjId())
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))
        for i in range(self.projCB.count()):
            if self.projCB.itemData(i) == cur_data:
                self.projCB.setCurrentIndex(i); break
        self.projCB.blockSignals(False)
        self.projFilterCB.blockSignals(False)

    def _reload_researcher_cb(self):
        """Reload researcher options from the researcher table (mirrors ResearcherTab)."""
        cur_data = self.resCB.currentData()
        self.resCB.blockSignals(True)
        self.resCB.clear()
        self.resCB.addItem('— select researcher —', None)
        try:
            for r in self.researcher_dao.get_all():
                label = f"{r.getResId()} – {r.getName()}"
                self.resCB.addItem(label, r.getResId())
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))
        for i in range(self.resCB.count()):
            if self.resCB.itemData(i) == cur_data:
                self.resCB.setCurrentIndex(i); break
        self.resCB.blockSignals(False)

    # -----------------------------------------------------------------------
    # Public slot — called by MainWindow when ProjectTab or ResearcherTab saves
    # -----------------------------------------------------------------------
    def refresh_lookups(self):
        """Re-sync project and researcher dropdowns without resetting the form."""
        self._reload_project_cb()
        self._reload_researcher_cb()

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------
    def _refresh(self):
        self._reload_project_cb()
        self._reload_researcher_cb()
        try:
            hypotheses = self.dao.get_all()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(hypotheses)

    def _populate_table(self, hypotheses):
        self.table.setRowCount(len(hypotheses))
        for r, h in enumerate(hypotheses):
            bg = STATUS_ROW_BG.get(h.getStatus())
            for c, v in enumerate([
                h.getHypId(),  h.getText(),    h.getStatus(),
                str(h.getConfidence()), h.getPmids(),
                h.getProjectId(), h.getNote()
            ]):
                it = QTableWidgetItem(str(v))
                if bg:
                    it.setBackground(QBrush(bg))
                if c == 2:
                    it.setForeground(QBrush(QColor(
                        STATUS_FG.get(h.getStatus(), TXT_S))))
                self.table.setItem(r, c, it)

    def table_row_was_clicked(self, row, col):
        self.inputIdLE.setText(self.table.item(row, 0).text())
        self.inputTextTE.setPlainText(self.table.item(row, 1).text())
        status  = self.table.item(row, 2).text()
        proj_id = self.table.item(row, 5).text()
        self.inputConfLE.setText(self.table.item(row, 3).text())
        self.inputPmidsLE.setText(self.table.item(row, 4).text())
        self.inputNoteLE.setText(self.table.item(row, 6).text())
        idx = self.statusCB.findText(status)
        if idx >= 0:
            self.statusCB.setCurrentIndex(idx)
        for i in range(self.projCB.count()):
            if self.projCB.itemData(i) == proj_id:
                self.projCB.setCurrentIndex(i); break

    # -----------------------------------------------------------------------
    # Search / clear
    # -----------------------------------------------------------------------
    def search_button_was_clicked(self):
        pid  = self.projFilterCB.currentData()
        stat = self.statFilterCB.currentText()
        stat = None if stat == 'All Statuses' else stat
        try:
            results = self.dao.search(pid, stat)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(results)

    def clear_button_was_clicked(self):
        self.projFilterCB.setCurrentIndex(0)
        self.statFilterCB.setCurrentIndex(0)
        self._refresh()

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------
    def add_button_was_clicked(self):
        hid  = self.inputIdLE.text().strip()
        text = self.inputTextTE.toPlainText().strip()
        if not hid or not text:
            QMessageBox.warning(self, 'Validation',
                                'Hypothesis ID and text are required.'); return
        try:
            h = Hypothesis(
                hid,
                self.projCB.currentData(),
                text,
                self.statusCB.currentText(),
                float(self.inputConfLE.text() or 0.5),
                self.inputPmidsLE.text().strip(),
                self.inputNoteLE.text().strip()
            )
            self.dao.insert(h)
            res_id = self.resCB.currentData() or 'system'
            self.audit_dao.add(res_id, 'CREATE',
                               f'Hypothesis {hid}', text[:50])
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Added', f'{hid} added.')

    def update_button_was_clicked(self):
        hid = self.inputIdLE.text().strip()
        if not hid:
            QMessageBox.warning(self, 'Validation', 'Select a row first.'); return
        stat   = self.statusCB.currentText()
        note   = self.inputNoteLE.text().strip()
        res_id = self.resCB.currentData() or 'system'
        try:
            self.dao.update_status(hid, stat, note)
            self.audit_dao.add(res_id, 'UPDATE',
                               f'Hypothesis {hid}', f'-> {stat}')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Updated', f'{hid} updated.')

    def delete_button_was_clicked(self):
        hid = self.inputIdLE.text().strip()
        if not hid:
            QMessageBox.warning(self, 'Validation', 'Select a row first.'); return
        reply = QMessageBox.question(
            self, 'Confirm Delete', f'Delete hypothesis {hid}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            self.dao.delete(hid)
            self.audit_dao.add('system', 'DELETE',
                               f'Hypothesis {hid}', 'Deleted')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Deleted', f'{hid} removed.')

    def reset_button_was_clicked(self):
        self.inputIdLE.setText('')
        self.inputTextTE.setPlainText('')
        self.inputConfLE.setText('')
        self.inputPmidsLE.setText('')
        self.inputNoteLE.setText('')
        self.statusCB.setCurrentIndex(0)
        self.projCB.setCurrentIndex(0)
        self.resCB.setCurrentIndex(0)