from PyQt6.QtCore import QModelIndex, QObject, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from model.model import ModelCreateType, ModelDeleteType
from util.constants import DictMenuFlag


class CRUDManager(QObject):
    new_file_created = pyqtSignal(QModelIndex, str)
    item_deleted = pyqtSignal(QModelIndex)
    file_deleted = pyqtSignal(QModelIndex)
    new_nested_entry = pyqtSignal(QModelIndex, str, str)
    new_nested_dict = pyqtSignal(QModelIndex, str)
    entries_cleared = pyqtSignal(QModelIndex)
    add_dict_above = pyqtSignal(QModelIndex, str)
    add_dict_below = pyqtSignal(QModelIndex, str)
    add_row_above = pyqtSignal(QModelIndex, str, str)
    add_row_below = pyqtSignal(QModelIndex, str, str)
    fields_standardised = pyqtSignal(QModelIndex)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # Actions
        self.new_file = QAction("New file", self)
        self.delete_item = QAction("Delete", self)
        self.delete_file = QAction("Delete", self)
        self.clear_entries = QAction("Clear entries", self)
        self.new_entry = QAction("New entry", self)
        self.add_row_menu = QMenu("Add row...")
        self.add_above = QAction("Add above", self)
        self.add_below = QAction("Add below", self)
        self.add_row_menu.addActions([self.add_above, self.add_below])
        self.standardise_fields = QAction("Standardise boundary fields", self)

        # Current item index selected
        self.current_index = QModelIndex()

        # Connect actions to their handlers
        self.new_file.triggered.connect(
            lambda: self.show_new_file_dialog(self.current_index)
        )
        self.delete_item.triggered.connect(
            lambda: self.show_delete_dialog(
                ModelDeleteType.KEY_VALUE, self.current_index
            )
        )
        self.delete_file.triggered.connect(
            lambda: self.show_delete_dialog(ModelDeleteType.FILE, self.current_index)
        )
        self.add_above.triggered.connect(
            lambda: self.show_add_row_dialog(ModelCreateType.BEFORE, self.current_index)
        )
        self.add_below.triggered.connect(
            lambda: self.show_add_row_dialog(ModelCreateType.AFTER, self.current_index)
        )
        self.new_entry.triggered.connect(
            lambda: self.show_add_row_dialog(ModelCreateType.CHILD, self.current_index)
        )
        self.clear_entries.triggered.connect(
            lambda: self.show_clear_entries_dialog(self.current_index)
        )
        self.standardise_fields.triggered.connect(
            lambda: self.show_standardise_fields_dialog(self.current_index)
        )

    def show_field_menu(self, pos: QPoint, index: QModelIndex):
        self.current_index = index

        # Create a context menu
        field_menu = QMenu()

        field_menu.addAction(self.delete_item)
        field_menu.addSeparator()
        field_menu.addMenu(self.add_row_menu)

        field_menu.exec(pos)

    def show_dict_menu(self, pos: QPoint, flag: DictMenuFlag, index: QModelIndex):
        self.current_index = index

        # Create a context menu
        dict_menu = QMenu()
        if flag == DictMenuFlag.SUB_DIR:
            dict_menu.addAction(self.new_file)
            dict_menu.exec(pos)
        elif flag == DictMenuFlag.FILE:
            dict_menu.addAction(self.new_entry)
            dict_menu.addSeparator()
            dict_menu.addAction(self.delete_file)
            dict_menu.exec(pos)
        else:
            dict_menu.addAction(self.delete_item)
            dict_menu.addSeparator()
            dict_menu.addActions([self.new_entry, self.clear_entries])
            dict_menu.addSeparator()
            dict_menu.addMenu(self.add_row_menu)
            dict_menu.addSeparator()
            dict_menu.addAction(self.standardise_fields)

            if flag != DictMenuFlag.BOUNDARY_FIELD:
                self.standardise_fields.setDisabled(True)
            else:
                self.standardise_fields.setEnabled(True)

            dict_menu.exec(pos)

    def show_new_file_dialog(self, index: QModelIndex):
        modal = QInputDialog(
            None, Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )
        file_name, ok = modal.getText(
            None,
            "Create new file",
            "File name:",
            QLineEdit.EchoMode.Normal,
        )

        if not (file_name and ok):
            return

        self.handle_create_new_file(index, file_name)

    def show_delete_dialog(self, type: ModelDeleteType, index: QModelIndex):
        if type == ModelDeleteType.FILE:
            title, text = "Delete file", "Are you sure you want to delete this file?"
        elif type == ModelDeleteType.KEY_VALUE:
            title, text = "Delete item", "Are you sure you want to delete this item?"

        response = QMessageBox.question(
            None,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if response == QMessageBox.StandardButton.Yes:
            if type == ModelDeleteType.FILE:
                self.handle_delete_file(index)
            elif type == ModelDeleteType.KEY_VALUE:
                self.handle_delete_item(index)

    def show_add_row_dialog(self, type: ModelCreateType, index: QModelIndex):
        choice_box = QWidget()
        choice_box.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )
        layout = QVBoxLayout()
        choice_box.setLayout(layout)

        choice_box.setWindowTitle("Add row")

        description = QLabel("I want to add a new...", choice_box)
        layout.addWidget(description)

        def handle_dict_entry():
            self.show_dict_entry_modal(type, index)
            choice_box.close()

        def handle_dict_item():
            self.show_dict_item_modal(type, index)
            choice_box.close()

        dict_entry_btn = QPushButton("Dictionary entry")
        dict_item_btn = QPushButton("Dictionary item")
        dict_entry_btn.pressed.connect(handle_dict_entry)
        dict_item_btn.pressed.connect(handle_dict_item)

        btns = QHBoxLayout()
        btns.addWidget(dict_entry_btn)
        btns.addWidget(dict_item_btn)
        layout.addLayout(btns)

        choice_box.show()

    def show_dict_entry_modal(self, type: ModelCreateType, index: QModelIndex):
        modal = QWidget()
        modal.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        layout = QVBoxLayout()
        modal.setLayout(layout)

        modal.setWindowTitle("Add new dictionary entry")

        key_field, value_field = QLineEdit(), QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow("Key", key_field)
        form_layout.addRow("Value", value_field)
        layout.addLayout(form_layout)

        add_btn = QPushButton("Add", modal)

        def handle_add():
            key, value = key_field.text(), value_field.text()
            if type == ModelCreateType.BEFORE:
                self.handle_add_row_above(index, key, value)
            elif type == ModelCreateType.AFTER:
                self.handle_add_row_below(index, key, value)
            elif type == ModelCreateType.CHILD:
                self.handle_add_nested_entry(index, key, value)
            modal.close()

        add_btn.pressed.connect(handle_add)
        add_btn.setAutoDefault(True)
        layout.addWidget(add_btn)
        modal.show()

    def show_dict_item_modal(self, type: ModelCreateType, index: QModelIndex):
        modal = QInputDialog(
            None, Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )
        dict_name, ok = modal.getText(
            None,
            "Add new subdictionary",
            "Dictionary name:",
            QLineEdit.EchoMode.Normal,
        )

        if not (dict_name and ok):
            return

        if type == ModelCreateType.BEFORE:
            self.handle_add_dict_above(index, dict_name)
        elif type == ModelCreateType.AFTER:
            self.handle_add_dict_below(index, dict_name)
        elif type == ModelCreateType.CHILD:
            self.handle_add_nested_dict(index, dict_name)

    def show_clear_entries_dialog(self, index: QModelIndex):
        response = QMessageBox.question(
            None,
            "Clear dictionary",
            "Are you sure you want to clear this dictionary?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if response == QMessageBox.StandardButton.Yes:
            self.handle_clear_entries_action(index)

    def show_standardise_fields_dialog(self, index: QModelIndex):
        response = QMessageBox.question(
            None,
            "Standardise boundary field",
            "Are you sure you want to standardise the boundary fields?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if response == QMessageBox.StandardButton.Yes:
            self.handle_standardise_fields(index)

    def handle_create_new_file(self, index: QModelIndex, file_name: str):
        self.new_file_created.emit(index, file_name)

    def handle_delete_item(self, index: QModelIndex):
        self.item_deleted.emit(index)

    def handle_delete_file(self, index: QModelIndex):
        self.file_deleted.emit(index)

    def handle_add_nested_entry(self, index: QModelIndex, key: str, value: str):
        self.new_nested_entry.emit(index, key, value)

    def handle_add_nested_dict(self, index: QModelIndex, key: str):
        self.new_nested_dict.emit(index, key)

    def handle_clear_entries_action(self, index: QModelIndex):
        self.entries_cleared.emit(index)

    def handle_add_dict_above(self, index: QModelIndex, key: str):
        self.add_dict_above.emit(index, key)

    def handle_add_dict_below(self, index: QModelIndex, key: str):
        self.add_dict_below.emit(index, key)

    def handle_add_row_above(self, index: QModelIndex, key: str, value: str):
        self.add_row_above.emit(index, key, value)

    def handle_add_row_below(self, index: QModelIndex, key: str, value: str):
        self.add_row_below.emit(index, key, value)

    def handle_standardise_fields(self, index: QModelIndex):
        self.fields_standardised.emit(index)
