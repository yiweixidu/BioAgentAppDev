# gui/tabs/projects_tab.py
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QGridLayout, QHBoxLayout)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import pyqtSignal
from gui.ui_helpers import card, scroll_wrap, setup_table, AMBER, TEAL, GREEN, RED, PURP, TXT_M
from dao.dao_project import ProjectDAO
from dao.dao_audit   import AuditDAO
from dao.dao_options import OptionsDAO
from models.project  import Project
from gui.manage_options_dialog import ManageOptionsDialog
from config.db_config          import MANAGE_ROLES

CURRENT_USER_ROLE = 'admin'
MANAGE_ITEM = '⚙  Manage options...'

STATUS_CLR = {'active': TEAL, 'planning': PURP, 'archived': TXT_M}


class ProjectsTab(QWidget):
    # Emitted after any successful add / update / delete.
    # MainWindow connects this to HypothesisTab.refresh_lookups and
    # InferenceTab.refresh_lookups so their project dropdowns stay in sync.
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.dao         = ProjectDAO()
        self.audit_dao   = AuditDAO()
        self.options_dao = OptionsDAO()

        # ------------Labels------------
        self.searchLabel   = QLabel('Search:')
        self.statusFLabel  = QLabel('Status Filter:')
        self.idLabel       = QLabel('Project ID:')
        self.titleLabel    = QLabel('Title:')
        self.piLabel       = QLabel('PI Name:')
        self.domainLabel   = QLabel('Domain:')
        self.grantLabel    = QLabel('Grant Type:')
        self.statusLabel   = QLabel('Status:')
        self.progressLabel = QLabel('Progress (%):')

        # ------------Input / Output------------
        self.searchLE        = QLineEdit()
        self.searchLE.setPlaceholderText('Title / Project ID')
        self.inputIdLE       = QLineEdit()
        self.inputIdLE.setPlaceholderText('Auto-generated')
        self.inputIdLE.setReadOnly(True)
        self.inputTitleLE    = QLineEdit()
        self.inputTitleLE.setPlaceholderText('Project title')
        self.inputPiLE       = QLineEdit()
        self.inputPiLE.setPlaceholderText('Principal Investigator')
        self.inputProgressLE = QLineEdit()
        self.inputProgressLE.setPlaceholderText('0-100')

        # ComboBoxes — populated dynamically from app_options
        self.statusFilterCB = QComboBox()
        self.domainCB       = QComboBox()
        self.grantCB        = QComboBox()
        self.statusCB       = QComboBox()

        self._reload_status_filter_cb()
        self._reload_domain_cb()
        self._reload_grant_cb()
        self._reload_status_cb()

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
            ['ID', 'Title', 'Domain', 'Grant', 'PI', 'Status', 'Progress'], 1)

        # ------------Signals------------
        self.searchButton.clicked.connect(self.search_button_was_clicked)
        self.clearButton.clicked.connect(self.clear_button_was_clicked)
        self.addButton.clicked.connect(self.add_button_was_clicked)
        self.updateButton.clicked.connect(self.update_button_was_clicked)
        self.deleteButton.clicked.connect(self.delete_button_was_clicked)
        self.resetButton.clicked.connect(self.reset_button_was_clicked)
        self.table.cellClicked.connect(self.table_row_was_clicked)
        self.domainCB.currentIndexChanged.connect(self.domain_cb_changed)
        self.grantCB.currentIndexChanged.connect(self.grant_cb_changed)
        self.statusCB.currentIndexChanged.connect(self.status_cb_changed)

        # ------------Layout------------
        _, layout = scroll_wrap(self)

        # Search card
        srch_c, sl = card('🔍  Search Projects', border=PURP)
        srch_grid = QGridLayout()
        srch_grid.addWidget(self.searchLabel,    0, 0)
        srch_grid.addWidget(self.searchLE,       0, 1)
        srch_grid.addWidget(self.statusFLabel,   0, 2)
        srch_grid.addWidget(self.statusFilterCB, 0, 3)
        srch_grid.addWidget(self.searchButton,   0, 4)
        srch_grid.addWidget(self.clearButton,    0, 5)
        sl.addLayout(srch_grid)
        layout.addWidget(srch_c)

        # Table card
        tbl_c, tl = card('📋  Project Registry', border=TEAL)
        tl.addWidget(self.table)
        layout.addWidget(tbl_c)

        # Add / Edit card
        form_c, fl = card('✏️  Add / Edit Project', border=AMBER)
        form_grid = QGridLayout()
        form_grid.addWidget(self.idLabel,         0, 0)
        form_grid.addWidget(self.inputIdLE,       0, 1)
        form_grid.addWidget(self.titleLabel,      0, 2)
        form_grid.addWidget(self.inputTitleLE,    0, 3)
        form_grid.addWidget(self.piLabel,         1, 0)
        form_grid.addWidget(self.inputPiLE,       1, 1)
        form_grid.addWidget(self.domainLabel,     1, 2)
        form_grid.addWidget(self.domainCB,        1, 3)
        form_grid.addWidget(self.grantLabel,      2, 0)
        form_grid.addWidget(self.grantCB,         2, 1)
        form_grid.addWidget(self.statusLabel,     2, 2)
        form_grid.addWidget(self.statusCB,        2, 3)
        form_grid.addWidget(self.progressLabel,   3, 0)
        form_grid.addWidget(self.inputProgressLE, 3, 1)
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
    # Reload helpers
    # -----------------------------------------------------------------------
    def _reload_status_filter_cb(self):
        """Status filter in Search card — All + current statuses, no Manage item."""
        current = self.statusFilterCB.currentText()
        self.statusFilterCB.blockSignals(True)
        self.statusFilterCB.clear()
        self.statusFilterCB.addItem('All', None)
        opts = self.options_dao.get_by_category('status')
        self.statusFilterCB.addItems(opts)
        idx = self.statusFilterCB.findText(current)
        self.statusFilterCB.setCurrentIndex(idx if idx >= 0 else 0)
        self.statusFilterCB.blockSignals(False)

    def _reload_status_cb(self):
        """Status dropdown in form — options + Manage item for allowed roles."""
        current = self.statusCB.currentText()
        self.statusCB.blockSignals(True)
        self.statusCB.clear()
        opts = self.options_dao.get_by_category('status')
        self.statusCB.addItems(opts)
        if CURRENT_USER_ROLE in MANAGE_ROLES:
            self.statusCB.insertSeparator(len(opts))
            self.statusCB.addItem(MANAGE_ITEM)
        idx = self.statusCB.findText(current)
        self.statusCB.setCurrentIndex(idx if idx >= 0 else 0)
        self.statusCB.blockSignals(False)

    def _reload_domain_cb(self):
        current = self.domainCB.currentText()
        self.domainCB.blockSignals(True)
        self.domainCB.clear()
        opts = self.options_dao.get_by_category('domain')
        self.domainCB.addItems(opts)
        if CURRENT_USER_ROLE in MANAGE_ROLES:
            self.domainCB.insertSeparator(len(opts))
            self.domainCB.addItem(MANAGE_ITEM)
        idx = self.domainCB.findText(current)
        if idx >= 0:
            self.domainCB.setCurrentIndex(idx)
        self.domainCB.blockSignals(False)

    def _reload_grant_cb(self):
        current = self.grantCB.currentText()
        self.grantCB.blockSignals(True)
        self.grantCB.clear()
        opts = self.options_dao.get_by_category('grant')
        self.grantCB.addItems(opts)
        if CURRENT_USER_ROLE in MANAGE_ROLES:
            self.grantCB.insertSeparator(len(opts))
            self.grantCB.addItem(MANAGE_ITEM)
        idx = self.grantCB.findText(current)
        if idx >= 0:
            self.grantCB.setCurrentIndex(idx)
        self.grantCB.blockSignals(False)

    # -----------------------------------------------------------------------
    # Manage option dialog handlers
    # -----------------------------------------------------------------------
    def status_cb_changed(self, index):
        if self.statusCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('status', 'Manage Status Options', self)
            dlg.exec()
            self._reload_status_cb()
            self._reload_status_filter_cb()

    def domain_cb_changed(self, index):
        if self.domainCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('domain', 'Manage Domain Options', self)
            dlg.exec()
            self._reload_domain_cb()

    def grant_cb_changed(self, index):
        if self.grantCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('grant', 'Manage Grant Type Options', self)
            dlg.exec()
            self._reload_grant_cb()

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------
    def _refresh(self):
        self._reload_status_filter_cb()
        self._reload_status_cb()
        self._reload_domain_cb()
        self._reload_grant_cb()
        try:
            projects = self.dao.get_all()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(projects)

    def _populate_table(self, projects):
        self.table.setRowCount(len(projects))
        for r, p in enumerate(projects):
            for c, v in enumerate([
                p.getProjId(), p.getTitle(),  p.getDomain(),
                p.getGrant(),  p.getPi(),     p.getStatus(),
                str(p.getProgress()) + '%'
            ]):
                it = QTableWidgetItem(str(v))
                if c == 5:
                    it.setForeground(QBrush(QColor(
                        STATUS_CLR.get(p.getStatus(), TXT_M))))
                self.table.setItem(r, c, it)

    def table_row_was_clicked(self, row, col):
        self.inputIdLE.setText(self.table.item(row, 0).text())
        self.inputTitleLE.setText(self.table.item(row, 1).text())
        domain = self.table.item(row, 2).text()
        grant  = self.table.item(row, 3).text()
        self.inputPiLE.setText(self.table.item(row, 4).text())
        status = self.table.item(row, 5).text()
        prog   = self.table.item(row, 6).text().replace('%', '')
        self.inputProgressLE.setText(prog)
        idx = self.domainCB.findText(domain)
        if idx >= 0: self.domainCB.setCurrentIndex(idx)
        idx = self.grantCB.findText(grant)
        if idx >= 0: self.grantCB.setCurrentIndex(idx)
        idx = self.statusCB.findText(status)
        if idx >= 0: self.statusCB.setCurrentIndex(idx)

    # -----------------------------------------------------------------------
    # Search / clear
    # -----------------------------------------------------------------------
    def search_button_was_clicked(self):
        keyword = self.searchLE.text().strip()
        status  = self.statusFilterCB.currentText()
        status  = None if status == 'All' else status
        try:
            results = self.dao.search(keyword, status)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(results)

    def clear_button_was_clicked(self):
        self.searchLE.setText('')
        self.statusFilterCB.setCurrentIndex(0)
        self._refresh()

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------
    def add_button_was_clicked(self):
        title = self.inputTitleLE.text().strip()
        if not title:
            QMessageBox.warning(self, 'Validation', 'Title is required.'); return
        if (self.statusCB.currentText() == MANAGE_ITEM or
                self.domainCB.currentText() == MANAGE_ITEM or
                self.grantCB.currentText() == MANAGE_ITEM):
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid option.'); return
        try:
            nid = f"PRJ-{self.dao.count() + 200}"
            p   = Project(
                nid, title,
                self.domainCB.currentText(),
                self.grantCB.currentText(),
                self.inputPiLE.text().strip() or 'Unknown',
                self.statusCB.currentText(),
                None,
                int(self.inputProgressLE.text() or 0)
            )
            self.dao.insert(p)
            self.audit_dao.add('system', 'CREATE',
                               f'Project {nid}', f"'{title}' registered")
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Added', f'{nid} created.')

    def update_button_was_clicked(self):
        pid = self.inputIdLE.text().strip()
        if not pid:
            QMessageBox.warning(self, 'Validation', 'Select a row first.'); return
        title = self.inputTitleLE.text().strip()
        if not title:
            QMessageBox.warning(self, 'Validation', 'Title is required.'); return
        if (self.statusCB.currentText() == MANAGE_ITEM or
                self.domainCB.currentText() == MANAGE_ITEM or
                self.grantCB.currentText() == MANAGE_ITEM):
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid option.'); return
        try:
            p = Project(
                pid, title,
                self.domainCB.currentText(),
                self.grantCB.currentText(),
                self.inputPiLE.text().strip() or 'Unknown',
                self.statusCB.currentText(),
                None,
                int(self.inputProgressLE.text() or 0)
            )
            self.dao.update(p)
            self.audit_dao.add('system', 'UPDATE',
                               f'Project {pid}', f"'{title}' updated")
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Updated', f'{pid} updated.')

    def delete_button_was_clicked(self):
        pid = self.inputIdLE.text().strip()
        if not pid:
            QMessageBox.warning(self, 'Validation', 'Select a row first.'); return
        reply = QMessageBox.question(
            self, 'Confirm Delete', f'Delete project {pid}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            self.dao.delete(pid)
            self.audit_dao.add('system', 'DELETE',
                               f'Project {pid}', 'Deleted')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Deleted', f'{pid} removed.')

    def reset_button_was_clicked(self):
        for w in [self.inputIdLE, self.inputTitleLE,
                  self.inputPiLE, self.inputProgressLE]:
            w.setText('')
        self.domainCB.setCurrentIndex(0)
        self.grantCB.setCurrentIndex(0)
        self.statusCB.setCurrentIndex(0)