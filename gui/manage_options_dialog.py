# gui/manage_options_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton,
                             QListWidget, QListWidgetItem,
                             QMessageBox)
from PyQt6.QtCore import Qt
from dao.dao_options import OptionsDAO


class ManageOptionsDialog(QDialog):
    """
    Generic dialog to add/delete dropdown options.
    category: 'domain' | 'grant' | 'role'
    title:    dialog window title
    """
    def __init__(self, category: str, title: str, parent=None):
        super().__init__(parent)
        self.category   = category
        self.dao        = OptionsDAO()
        self.setWindowTitle(title)
        self.setMinimumWidth(360)

        # ------------Labels------------
        self.titleLbl   = QLabel(f'<b>{title}</b>')
        self.inputLabel = QLabel('New option:')

        # ------------Input------------
        self.inputLE = QLineEdit()
        self.inputLE.setPlaceholderText('Enter new option...')

        # ------------Buttons------------
        self.addButton    = QPushButton('➕  Add')
        self.addButton.setObjectName('primaryButton')
        self.deleteButton = QPushButton('✕  Delete selected')
        self.deleteButton.setObjectName('dangerButton')
        self.doneButton   = QPushButton('Done')

        # ------------List------------
        self.listWidget = QListWidget()
        self._reload_list()

        # ------------Signals------------
        self.addButton.clicked.connect(self.add_button_was_clicked)
        self.deleteButton.clicked.connect(self.delete_button_was_clicked)
        self.doneButton.clicked.connect(self.accept)

        # ------------Layout------------
        layout = QVBoxLayout(self)
        layout.addWidget(self.titleLbl)
        layout.addWidget(self.listWidget)

        input_row = QHBoxLayout()
        input_row.addWidget(self.inputLabel)
        input_row.addWidget(self.inputLE)
        input_row.addWidget(self.addButton)
        layout.addLayout(input_row)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.deleteButton)
        btn_row.addStretch()
        btn_row.addWidget(self.doneButton)
        layout.addLayout(btn_row)

    # ------------Slots------------
    def _reload_list(self):
        self.listWidget.clear()
        options = self.dao.get_by_category(self.category)
        for opt in options:
            self.listWidget.addItem(QListWidgetItem(opt))

    def add_button_was_clicked(self):
        value = self.inputLE.text().strip()
        if not value:
            QMessageBox.warning(self, 'Validation',
                                'Please enter a value.'); return
        try:
            self.dao.add(self.category, value)
            self.inputLE.setText('')
            self._reload_list()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))

    def delete_button_was_clicked(self):
        item = self.listWidget.currentItem()
        if not item:
            QMessageBox.warning(self, 'Selection',
                                'Select an item to delete.'); return
        value = item.text()
        reply = QMessageBox.question(
            self, 'Confirm', f"Delete '{value}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            self.dao.delete(self.category, value)
            self._reload_list()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error', str(e))