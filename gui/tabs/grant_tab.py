# gui/tabs/grant_tab.py
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QComboBox, QGridLayout, QHBoxLayout)
from PyQt6.QtGui import QColor, QBrush
from datetime import date
from gui.ui_helpers import (card, scroll_wrap, setup_table, prog_bar,
                            AMBER, TEAL, GREEN, RED, BLUE, TXT_M, PURP)
from gui.manage_options_dialog import ManageOptionsDialog
from dao.dao_grant   import GrantDAO
from dao.dao_project import ProjectDAO
from dao.dao_audit   import AuditDAO
from dao.dao_options import OptionsDAO
from models.milestone  import Milestone
from core.session import Session

# role now read from Session at runtime
MANAGE_ITEM       = '⚙  Manage options...'


class GrantTab(QWidget):
    def __init__(self):
        super().__init__()

        # ------------DAO------------
        self.dao         = GrantDAO()
        self.project_dao = ProjectDAO()
        self.audit_dao   = AuditDAO()
        self.options_dao = OptionsDAO()

        # ------------Labels (Alert)------------
        self.alertLabel = QLabel()
        self.alertLabel.setWordWrap(True)

        # ------------Labels (Grant Search)------------
        self.grantTypeFLabel = QLabel('Grant Type Filter:')

        # ------------Labels (Milestone Form)------------
        self.msIdLabel  = QLabel('Milestone ID:')
        self.grantLabel = QLabel('Grant:')
        self.descLabel  = QLabel('Description:')
        self.dueLabel   = QLabel('Due Date:')
        self.msFLabel   = QLabel('Grant Filter:')

        # ------------Input/Output (Grant Search)------------
        self.grantTypeFilterCB = QComboBox()
        self._reload_grant_filter_cb()

        # ------------Input/Output (Milestone)------------
        self.inputMsIdLE = QLineEdit()
        self.inputMsIdLE.setPlaceholderText('Milestone ID')
        self.inputMsIdLE.setReadOnly(True)
        self.inputDescLE = QLineEdit()
        self.inputDescLE.setPlaceholderText('Milestone description')
        self.inputDueLE  = QLineEdit()
        self.inputDueLE.setPlaceholderText('YYYY-MM-DD')

        self.msGrantFilterCB = QComboBox()
        self.msGrantFilterCB.addItem('All Grants', None)

        # grantCB: existing grants + Manage option
        self.grantCB = QComboBox()
        self._reload_grant_cb()

        # ------------Buttons (Grant)------------
        self.searchGrantButton = QPushButton('🔍  Search Grants')
        self.clearGrantButton  = QPushButton('Clear')
        self.exportButton      = QPushButton('📄  Export Report  (DOCX mock)')

        # ------------Buttons (Milestone)------------
        self.searchMsButton = QPushButton('🔍  Search')
        self.clearMsButton  = QPushButton('Clear')
        self.addMsButton    = QPushButton('➕  Add Milestone')
        self.addMsButton.setObjectName('primaryButton')
        self.markDoneButton = QPushButton('✔  Mark Complete')
        self.markDoneButton.setObjectName('primaryButton')
        self.deleteMsButton = QPushButton('🗑  Delete Milestone')
        self.deleteMsButton.setObjectName('dangerButton')
        self.resetMsButton  = QPushButton('Reset Form')

        # ------------Tables------------
        self.grTbl = QTableWidget()
        setup_table(self.grTbl,
            ['Grant ID', 'Project', 'Grant Type', 'Deadline',
             'Budget Used', 'Total', 'Budget %'], 1)
        self.grTbl.setMinimumHeight(120)

        self.msTbl = QTableWidget()
        setup_table(self.msTbl,
            ['ID', 'Grant', 'Description', 'Due Date', 'Status'], 2)
        self.msTbl.setMinimumHeight(120)

        # ------------Signals------------
        self.searchGrantButton.clicked.connect(self.search_grant_button_was_clicked)
        self.clearGrantButton.clicked.connect(self.clear_grant_button_was_clicked)
        self.exportButton.clicked.connect(self.export_button_was_clicked)
        self.searchMsButton.clicked.connect(self.search_ms_button_was_clicked)
        self.clearMsButton.clicked.connect(self.clear_ms_button_was_clicked)
        self.addMsButton.clicked.connect(self.add_ms_button_was_clicked)
        self.markDoneButton.clicked.connect(self.mark_done_button_was_clicked)
        self.deleteMsButton.clicked.connect(self.delete_ms_button_was_clicked)
        self.resetMsButton.clicked.connect(self.reset_ms_button_was_clicked)
        self.msTbl.cellClicked.connect(self.ms_table_row_was_clicked)
        self.grantCB.currentIndexChanged.connect(self.grant_cb_changed)

        # ------------Layout------------
        _, layout = scroll_wrap(self)
        layout.addWidget(self.alertLabel)

        # Grant Search card
        gs_c, gsl = card('🔍  Search Grants', border=PURP)
        gs_grid = QGridLayout()
        gs_grid.addWidget(self.grantTypeFLabel,    0, 0)
        gs_grid.addWidget(self.grantTypeFilterCB,  0, 1)
        gs_grid.addWidget(self.searchGrantButton,  0, 2)
        gs_grid.addWidget(self.clearGrantButton,   0, 3)
        gsl.addLayout(gs_grid)
        layout.addWidget(gs_c)

        # Grant Table card
        gr_c, gl = card('📅  Active Grants', border=TEAL)
        gl.addWidget(self.grTbl)
        exp_row = QHBoxLayout()
        exp_row.addWidget(self.exportButton)
        exp_row.addStretch()
        gl.addLayout(exp_row)
        layout.addWidget(gr_c)

        # Milestone Search card
        ms_srch_c, msl = card('🔍  Search Milestones', border=AMBER)
        ms_grid = QGridLayout()
        ms_grid.addWidget(self.msFLabel,        0, 0)
        ms_grid.addWidget(self.msGrantFilterCB, 0, 1)
        ms_grid.addWidget(self.searchMsButton,  0, 2)
        ms_grid.addWidget(self.clearMsButton,   0, 3)
        msl.addLayout(ms_grid)
        layout.addWidget(ms_srch_c)

        # Milestone Table card
        ms_c, ml = card('📌  Milestones', border=GREEN)
        ml.addWidget(self.msTbl)
        layout.addWidget(ms_c)

        # Milestone Add / Edit card
        form_c, fl = card('✏️  Add / Edit Milestone', border=BLUE)
        form_grid = QGridLayout()
        form_grid.addWidget(self.msIdLabel,   0, 0)
        form_grid.addWidget(self.inputMsIdLE, 0, 1)
        form_grid.addWidget(self.grantLabel,  0, 2)
        form_grid.addWidget(self.grantCB,     0, 3)
        form_grid.addWidget(self.descLabel,   1, 0)
        form_grid.addWidget(self.inputDescLE, 1, 1)
        form_grid.addWidget(self.dueLabel,    1, 2)
        form_grid.addWidget(self.inputDueLE,  1, 3)
        fl.addLayout(form_grid)

        btn_row = QHBoxLayout()
        for b in [self.addMsButton, self.markDoneButton,
                  self.deleteMsButton, self.resetMsButton]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        fl.addLayout(btn_row)
        layout.addWidget(form_c)

        layout.addStretch()
        self._refresh()

    # ── Reload helpers ────────────────────────────────────────

    def _reload_grant_filter_cb(self):
        """Grant Type filter from project table grant_src values."""
        current = self.grantTypeFilterCB.currentText()
        self.grantTypeFilterCB.blockSignals(True)
        self.grantTypeFilterCB.clear()
        self.grantTypeFilterCB.addItem('All', None)
        try:
            grant_types = self.project_dao.get_distinct_grants()
            self.grantTypeFilterCB.addItems(grant_types)
        except Exception:
            self.grantTypeFilterCB.addItems(['CIHR', 'NSERC', 'MITACS'])
        idx = self.grantTypeFilterCB.findText(current)
        self.grantTypeFilterCB.setCurrentIndex(idx if idx >= 0 else 0)
        self.grantTypeFilterCB.blockSignals(False)

    def _reload_grant_cb(self):
        """
        Grant selector in milestone form.
        Shows existing grants (GR-001 — Project Title).
        Allowed roles see Manage option at bottom to add/remove grants.
        Note: 'grants' here means grant fund records (GR-001, GR-002),
        not grant types (CIHR, NSERC).
        """
        current_data = self.grantCB.currentData()
        self.grantCB.blockSignals(True)
        self.grantCB.clear()

        try:
            titles = self.project_dao.get_titles()
            grants = self.dao.get_all()
            for g in grants:
                label = (f"{g.getGrantId()} — "
                         f"{titles.get(g.getProjectId(), g.getProjectId())}"
                         f"  [{g.getGrantType()}]")
                self.grantCB.addItem(label, g.getGrantId())
            # Also reload msGrantFilterCB in sync
            self.msGrantFilterCB.blockSignals(True)
            self.msGrantFilterCB.clear()
            self.msGrantFilterCB.addItem('All Grants', None)
            for g in grants:
                label = (f"{g.getGrantId()} — "
                         f"{titles.get(g.getProjectId(), g.getProjectId())}")
                self.msGrantFilterCB.addItem(label, g.getGrantId())
            self.msGrantFilterCB.blockSignals(False)
        except Exception as e:
            pass

        if Session.can_manage_options():
            self.grantCB.insertSeparator(self.grantCB.count())
            self.grantCB.addItem(MANAGE_ITEM)

        # Restore previous selection
        for i in range(self.grantCB.count()):
            if self.grantCB.itemData(i) == current_data:
                self.grantCB.setCurrentIndex(i)
                break

        self.grantCB.blockSignals(False)

    # ── Manage option dialog handler ──────────────────────────

    def grant_cb_changed(self, index):
        if self.grantCB.currentText() == MANAGE_ITEM:
            dlg = ManageOptionsDialog(
                'grant', 'Manage Grant Type Options', self)
            dlg.exec()
            self._reload_grant_filter_cb()
            self.grantCB.blockSignals(True)
            self._reload_grant_cb()
            self.grantCB.setCurrentIndex(0)
            self.grantCB.blockSignals(False)

    # ── Slots ─────────────────────────────────────────────────

    def _refresh(self):
        self._reload_grant_filter_cb()
        self._reload_grant_cb()
        try:
            grants     = self.dao.get_all()
            milestones = self.dao.get_milestones()
            titles     = self.project_dao.get_titles()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._update_alert(milestones)
        self._populate_grant_table(grants, titles)
        self._populate_ms_table(milestones)

    def _update_alert(self, milestones):
        today   = date.today().isoformat()
        overdue = [m.getDesc() for m in milestones
                   if not m.isCompleted() and m.getDue() < today]
        if overdue:
            self.alertLabel.setObjectName('AlertBar')
            self.alertLabel.setText(f"⚠  Overdue: {' · '.join(overdue)}")
        else:
            self.alertLabel.setObjectName('OkBar')
            self.alertLabel.setText('✅  No overdue milestones')
        self.alertLabel.setStyleSheet(self.alertLabel.styleSheet())

    def _populate_grant_table(self, grants, titles):
        self.grTbl.setRowCount(len(grants))
        for r, g in enumerate(grants):
            pct    = g.getBudgetPct()
            over_g = g.isOverdue()
            for c, v in enumerate([
                g.getGrantId(),
                titles.get(g.getProjectId(), g.getProjectId()),
                g.getGrantType(),
                g.getDeadline(),
                f"${g.getUsed():,.0f}",
                f"${g.getTotal():,.0f}",
                ''
            ]):
                if c == 6: continue
                it = QTableWidgetItem(str(v))
                if c == 3 and over_g:
                    it.setForeground(QBrush(QColor(RED)))
                elif c == 2:
                    it.setForeground(QBrush(QColor(AMBER)))
                self.grTbl.setItem(r, c, it)
            bar = prog_bar(pct, RED if over_g else TEAL, 10)
            bar.setTextVisible(True)
            bar.setFormat(f' {pct}%')
            self.grTbl.setCellWidget(r, 6, bar)
            self.grTbl.setRowHeight(r, 34)

    def _populate_ms_table(self, milestones):
        today = date.today().isoformat()
        self.msTbl.setRowCount(len(milestones))
        for r, m in enumerate(milestones):
            overdue_m = not m.isCompleted() and m.getDue() < today
            for c, v in enumerate([
                str(m.getId()), m.getGrantId(),
                m.getDesc(),    m.getDue(),
                '✔ Done' if m.isCompleted()
                else ('⚠ Overdue' if overdue_m else 'Pending')
            ]):
                it = QTableWidgetItem(str(v))
                if c == 4:
                    it.setForeground(QBrush(QColor(
                        GREEN if m.isCompleted()
                        else RED if overdue_m else TXT_M)))
                elif c == 3 and overdue_m:
                    it.setForeground(QBrush(QColor(RED)))
                self.msTbl.setItem(r, c, it)

    def ms_table_row_was_clicked(self, row, col):
        self.inputMsIdLE.setText(self.msTbl.item(row, 0).text())
        grant_id = self.msTbl.item(row, 1).text()
        self.inputDescLE.setText(self.msTbl.item(row, 2).text())
        self.inputDueLE.setText(self.msTbl.item(row, 3).text())
        for i in range(self.grantCB.count()):
            if self.grantCB.itemData(i) == grant_id:
                self.grantCB.setCurrentIndex(i)
                break

    def search_grant_button_was_clicked(self):
        grant_type = self.grantTypeFilterCB.currentText()
        try:
            grants = self.dao.get_all()
            titles = self.project_dao.get_titles()
            if grant_type != 'All':
                grants = [g for g in grants
                          if g.getGrantType() == grant_type]
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_grant_table(grants, titles)

    def clear_grant_button_was_clicked(self):
        self.grantTypeFilterCB.setCurrentIndex(0)
        try:
            grants = self.dao.get_all()
            titles = self.project_dao.get_titles()
            self._populate_grant_table(grants, titles)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))

    def search_ms_button_was_clicked(self):
        gid = self.msGrantFilterCB.currentData()
        try:
            milestones = self.dao.get_milestones()
            if gid:
                milestones = [m for m in milestones
                              if m.getGrantId() == gid]
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._populate_ms_table(milestones)

    def clear_ms_button_was_clicked(self):
        self.msGrantFilterCB.setCurrentIndex(0)
        try:
            milestones = self.dao.get_milestones()
            self._populate_ms_table(milestones)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))

    def add_ms_button_was_clicked(self):
        desc = self.inputDescLE.text().strip()
        due  = self.inputDueLE.text().strip()
        if not desc or not due:
            QMessageBox.warning(self, 'Validation',
                'Description and due date required.'); return
        gid = self.grantCB.currentData()
        if not gid:
            QMessageBox.warning(self, 'Validation',
                'Please select a valid grant.'); return
        try:
            m = Milestone(gid, desc, due, False)
            self.dao.add_milestone(m)
            self.audit_dao.add('system', 'ADD_MILESTONE', gid, desc)
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._refresh()
        self.reset_ms_button_was_clicked()
        QMessageBox.information(self, 'Added', 'Milestone added.')

    def mark_done_button_was_clicked(self):
        mid_txt = self.inputMsIdLE.text().strip()
        if not mid_txt:
            QMessageBox.warning(self, 'Validation',
                'Select a milestone row first.'); return
        try:
            self.dao.mark_milestone_done(int(mid_txt))
            self.audit_dao.add('system', 'MILESTONE_DONE',
                               f'Milestone {mid_txt}', 'Completed')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._refresh()
        self.reset_ms_button_was_clicked()
        QMessageBox.information(self, 'Done', 'Milestone marked complete.')

    def delete_ms_button_was_clicked(self):
        mid_txt = self.inputMsIdLE.text().strip()
        if not mid_txt:
            QMessageBox.warning(self, 'Validation',
                'Select a milestone row first.'); return
        reply = QMessageBox.question(
            self, 'Confirm Delete', f'Delete milestone {mid_txt}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            self.dao.delete_milestone(int(mid_txt))
            self.audit_dao.add('system', 'DELETE',
                               f'Milestone {mid_txt}', 'Deleted')
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e)); return
        self._refresh()
        self.reset_ms_button_was_clicked()
        QMessageBox.information(self, 'Deleted',
                                f'Milestone {mid_txt} removed.')

    def export_button_was_clicked(self):
        QMessageBox.information(self, 'Export',
            'DOCX report generation triggered (mock mode).')

    def reset_ms_button_was_clicked(self):
        self.inputMsIdLE.setText('')
        self.inputDescLE.setText('')
        self.inputDueLE.setText('')
        self.grantCB.setCurrentIndex(0)