# gui/tabs/researcher_tab.py
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QGridLayout, QHBoxLayout)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import pyqtSignal
from gui.ui_helpers import card, scroll_wrap, setup_table, AMBER, TEAL, GREEN, RED, TXT_M, PURP
from dao.dao_project     import ProjectDAO
from dao.dao_researcher  import ResearcherDAO
from dao.dao_audit       import AuditDAO
from dao.dao_options     import OptionsDAO
from models.researcher   import Researcher
from gui.manage_options_dialog import ManageOptionsDialog
from config.db_config          import MANAGE_ROLES

CURRENT_USER_ROLE = 'admin'
MANAGE_ITEM       = '⚙  Manage options...'
ROLE_CLR = {'admin': AMBER, 'lab_manager': TEAL, 'researcher': GREEN}


class ResearcherTab(QWidget):
    # Emitted after any successful add / update / delete.
    # MainWindow connects this to HypothesisTab.refresh_lookups so its
    # researcher dropdown stays in sync.
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.dao         = ResearcherDAO()
        self.audit_dao   = AuditDAO()
        self.project_dao = ProjectDAO()
        self.options_dao = OptionsDAO()

        # ------------Labels------------
        self.searchLabel = QLabel('Search:')
        self.idLabel     = QLabel('Researcher ID:')
        self.nameLabel   = QLabel('Name:')
        self.instLabel   = QLabel('Institution:')
        self.piLabel     = QLabel('PI Name:')
        self.emailLabel  = QLabel('Email:')
        self.domainLabel = QLabel('Domain:')
        self.roleLabel   = QLabel('Role:')
        self.pwLabel     = QLabel('Password:')

        # ------------Input / Output------------
        self.searchLE     = QLineEdit()
        self.searchLE.setPlaceholderText('Name / ID / Email')
        self.inputIdLE    = QLineEdit()
        self.inputIdLE.setPlaceholderText('Auto-generated')
        self.inputIdLE.setReadOnly(True)
        self.inputNameLE  = QLineEdit()
        self.inputNameLE.setPlaceholderText('Full name')
        self.inputInstLE  = QLineEdit()
        self.inputInstLE.setPlaceholderText('Institution / lab')
        self.inputPiLE    = QLineEdit()
        self.inputPiLE.setPlaceholderText('Principal Investigator')
        self.inputEmailLE = QLineEdit()
        self.inputEmailLE.setPlaceholderText('email@institution.ca')
        self.inputPwLE    = QLineEdit()
        self.inputPwLE.setPlaceholderText('Password')
        self.inputPwLE.setEchoMode(QLineEdit.EchoMode.Password)

        self.domainCB = QComboBox()
        self._reload_domain_cb()
        self.roleCB = QComboBox()
        self._reload_role_cb()

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
            ['ID', 'Name', 'Institution', 'PI', 'Domain', 'Role', 'Email'], 6)

        # ------------Signals------------
        self.searchButton.clicked.connect(self.search_button_was_clicked)
        self.clearButton.clicked.connect(self.clear_button_was_clicked)
        self.addButton.clicked.connect(self.add_button_was_clicked)
        self.updateButton.clicked.connect(self.update_button_was_clicked)
        self.deleteButton.clicked.connect(self.delete_button_was_clicked)
        self.resetButton.clicked.connect(self.reset_button_was_clicked)
        self.table.cellClicked.connect(self.table_row_was_clicked)
        self.domainCB.currentIndexChanged.connect(self.domain_cb_changed)
        self.roleCB.currentIndexChanged.connect(self.role_cb_changed)

        # ------------Layout------------
        _, layout = scroll_wrap(self)

        # Search card
        srch_c, sl = card('🔍  Search Researchers', border=PURP)
        srch_grid = QGridLayout()
        srch_grid.addWidget(self.searchLabel,  0, 0)
        srch_grid.addWidget(self.searchLE,     0, 1)
        srch_grid.addWidget(self.searchButton, 0, 2)
        srch_grid.addWidget(self.clearButton,  0, 3)
        sl.addLayout(srch_grid)
        layout.addWidget(srch_c)

        # Table card
        tbl_c, tl = card('📋  Researcher Registry', border=TEAL)
        tl.addWidget(self.table)
        layout.addWidget(tbl_c)

        # Add / Edit card
        form_c, fl = card('✏️  Add / Edit Researcher', border=AMBER)
        form_grid = QGridLayout()
        form_grid.addWidget(self.idLabel,       0, 0)
        form_grid.addWidget(self.inputIdLE,     0, 1)
        form_grid.addWidget(self.nameLabel,     0, 2)
        form_grid.addWidget(self.inputNameLE,   0, 3)
        form_grid.addWidget(self.instLabel,     1, 0)
        form_grid.addWidget(self.inputInstLE,   1, 1)
        form_grid.addWidget(self.piLabel,       1, 2)
        form_grid.addWidget(self.inputPiLE,     1, 3)
        form_grid.addWidget(self.emailLabel,    2, 0)
        form_grid.addWidget(self.inputEmailLE,  2, 1)
        form_grid.addWidget(self.domainLabel,   2, 2)
        form_grid.addWidget(self.domainCB,      2, 3)
        form_grid.addWidget(self.roleLabel,     3, 0)
        form_grid.addWidget(self.roleCB,        3, 1)
        form_grid.addWidget(self.pwLabel,       3, 2)
        form_grid.addWidget(self.inputPwLE,     3, 3)
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
    def _reload_domain_cb(self):
        """Reload domain options from app_options table."""
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

    def _reload_role_cb(self):
        """Reload role options from app_options table."""
        current = self.roleCB.currentText()
        self.roleCB.blockSignals(True)
        self.roleCB.clear()
        opts = self.options_dao.get_by_category('role')
        self.roleCB.addItems(opts)
        if CURRENT_USER_ROLE in MANAGE_ROLES:
            self.roleCB.insertSeparator(len(opts))
            self.roleCB.addItem(MANAGE_ITEM)
        idx = self.roleCB.findText(current)
        if idx >= 0:
            self.roleCB.setCurrentIndex(idx)
        self.roleCB.blockSignals(False)

    def domain_cb_changed(self, index):
        if self.domainCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('domain', 'Manage Domain Options', self)
            dlg.exec()
            self._reload_domain_cb()

    def role_cb_changed(self, index):
        if self.roleCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog('role', 'Manage Role Options', self)
            dlg.exec()
            self._reload_role_cb()

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------
    def _refresh(self):
        self._reload_domain_cb()
        self._reload_role_cb()
        try:
            researchers = self.dao.get_all()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(researchers)

    def _populate_table(self, researchers):
        self.table.setRowCount(len(researchers))
        for r, res in enumerate(researchers):
            for c, v in enumerate([
                res.getResId(),       res.getName(),
                res.getInstitution(), res.getPi(),
                res.getDomain(),      res.getRole(),
                res.getEmail()
            ]):
                it = QTableWidgetItem(str(v))
                if c == 5:
                    it.setForeground(QBrush(QColor(
                        ROLE_CLR.get(res.getRole(), TXT_M))))
                self.table.setItem(r, c, it)

    def table_row_was_clicked(self, row, col):
        self.inputIdLE.setText(self.table.item(row, 0).text())
        self.inputNameLE.setText(self.table.item(row, 1).text())
        self.inputInstLE.setText(self.table.item(row, 2).text())
        self.inputPiLE.setText(self.table.item(row, 3).text())
        domain = self.table.item(row, 4).text()
        role   = self.table.item(row, 5).text()
        self.inputEmailLE.setText(self.table.item(row, 6).text())
        idx = self.domainCB.findText(domain)
        if idx >= 0: self.domainCB.setCurrentIndex(idx)
        idx = self.roleCB.findText(role)
        if idx >= 0: self.roleCB.setCurrentIndex(idx)

    # -----------------------------------------------------------------------
    # Search / clear
    # -----------------------------------------------------------------------
    def search_button_was_clicked(self):
        keyword = self.searchLE.text().strip()
        if not keyword:
            self._refresh(); return
        try:
            results = self.dao.search(keyword)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_table(results)

    def clear_button_was_clicked(self):
        self.searchLE.setText('')
        self._refresh()

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------
    def add_button_was_clicked(self):
        name = self.inputNameLE.text().strip()
        if not name:
            QMessageBox.warning(self, 'Validation', 'Name is required.'); return
        if self.domainCB.currentText() == MANAGE_ITEM:
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid domain.'); return
        if self.roleCB.currentText() == MANAGE_ITEM:
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid role.'); return
        try:
            nid = f"RES-{self.dao.count() + 1:03d}"
            res = Researcher(
                nid, name,
                self.inputInstLE.text().strip()  or '—',
                self.inputPiLE.text().strip()    or '—',
                self.domainCB.currentText(),
                self.roleCB.currentText(),
                self.inputEmailLE.text().strip()
            )
            self.dao.insert(res)
            self.audit_dao.add(name, 'CREATE',
                               f'Researcher {nid}', 'Registered')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Added', f'{nid} registered.')

    def update_button_was_clicked(self):
        rid = self.inputIdLE.text().strip()
        if not rid:
            QMessageBox.warning(self, 'Validation',
                                'Select a row first or enter a Researcher ID.'); return
        name = self.inputNameLE.text().strip()
        if not name:
            QMessageBox.warning(self, 'Validation', 'Name is required.'); return
        if self.domainCB.currentText() == MANAGE_ITEM:
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid domain.'); return
        if self.roleCB.currentText() == MANAGE_ITEM:
            QMessageBox.warning(self, 'Validation',
                                'Please select a valid role.'); return
        try:
            res = Researcher(
                rid, name,
                self.inputInstLE.text().strip()  or '—',
                self.inputPiLE.text().strip()    or '—',
                self.domainCB.currentText(),
                self.roleCB.currentText(),
                self.inputEmailLE.text().strip()
            )
            self.dao.update(res)
            self.audit_dao.add(name, 'UPDATE',
                               f'Researcher {rid}', 'Updated')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Updated', f'{rid} updated.')

    def delete_button_was_clicked(self):
        rid = self.inputIdLE.text().strip()
        if not rid:
            QMessageBox.warning(self, 'Validation',
                                'Select a row first or enter a Researcher ID.'); return
        reply = QMessageBox.question(
            self, 'Confirm Delete', f'Delete researcher {rid}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            self.dao.delete(rid)
            self.audit_dao.add('system', 'DELETE',
                               f'Researcher {rid}', 'Removed')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self.data_changed.emit()
        self._refresh()
        self.reset_button_was_clicked()
        QMessageBox.information(self, 'Deleted', f'{rid} removed.')

    def reset_button_was_clicked(self):
        for w in [self.inputIdLE, self.inputNameLE, self.inputInstLE,
                  self.inputPiLE, self.inputEmailLE, self.inputPwLE]:
            w.setText('')
        self.domainCB.setCurrentIndex(0)
        self.roleCB.setCurrentIndex(0)