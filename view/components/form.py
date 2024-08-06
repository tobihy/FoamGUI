from PyQt6.QtCore import (
    QItemSelection,
    QModelIndex,
    QPersistentModelIndex,
    QSize,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from controller.custom_combo_box_controller import CustomComboBoxController
from model.model import (
    DictionaryEntryItem,
    OrderedDictItem,
    OrderedDictModel,
    QStandardItem,
)
from util.boundary_conditions import DROPDOWN_CHOICES
from util.constants import ODictType
from view.components.custom_combo_box import CustomComboBox
from view.components.information_display import InformationDisplay


class FieldEditor(QWidget):
    current_selection_changed = pyqtSignal(QItemSelection)
    go_to_item = pyqtSignal(QStandardItem)
    combobox_highlighted = pyqtSignal(QStandardItem)
    combobox_closed = pyqtSignal()
    add_field = pyqtSignal()

    key_updated = pyqtSignal(QModelIndex, str)
    value_updated = pyqtSignal(QModelIndex, str)
    combobox_updated = pyqtSignal(QModelIndex, str)

    def __init__(
        self,
        model: OrderedDictModel,
        parent=None,
    ) -> None:
        super().__init__(parent)

        # Set minimum size of editor
        window = self.window()
        if window:
            self.setMinimumSize(window.width() // 4, 0)

        # Model containing the data of the fields in the form
        self.model = model

        # Main layout of the editor
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Stacked layout which displays the various form views
        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # Information display of highlighted selection
        self.information_display = InformationDisplay(self)
        self.main_layout.addWidget(self.information_display)

        # Maps model indexes to the button they are associated with
        self.index_to_button: dict[QPersistentModelIndex, QPushButton] = {}

    def sizeHint(self) -> QSize:
        window = self.window()
        if window:
            return QSize(window.size().width() // 2, window.size().height())
        return super().sizeHint()

    def is_boundary_condition(self, test_value: str):
        """
        The function checks if the test_value is a valid boundary condition value
        in OpenFOAM.
        """
        for condition_dict in DROPDOWN_CHOICES.values():
            if test_value in condition_dict.keys():
                return True
        return False

    def add_odict_item(self, item: OrderedDictItem | QStandardItem, form: QFormLayout):
        item_type = item.data(OrderedDictItem.ROLE_TYPE)
        key_field = QLineEdit(item.text())
        if item_type not in [ODictType.OTHER, ODictType.BOUNDARY_FIELD]:
            key_field.setReadOnly(True)
        goto_button = QPushButton(f"Go to '{item.text()}'", self)
        goto_button.clicked.connect(lambda: self.on_goto_button_pressed(item))
        form.addRow(key_field, goto_button)

        # Map the item to the button for future updates
        self.index_to_button[QPersistentModelIndex(item.index())] = goto_button

        self.emit_changes(item, key_field, goto_button)

    def add_kv_pair(self, item: DictionaryEntryItem, form: QFormLayout):
        key_field = QLineEdit(item.key)

        if self.is_boundary_condition(item.value):
            value_field = CustomComboBox(self)
            combo_box_controller = CustomComboBoxController(
                value_field, DROPDOWN_CHOICES, item.value
            )
            combo_box_controller.combo_item_highlighted.connect(
                self.on_combo_item_highlighted
            )
            combo_box_controller.combo_focus_lost.connect(self.on_combo_closed)
        else:
            value_field = QLineEdit(item.value)

        if item.no_value():
            form.addRow(key_field)
        else:
            form.addRow(key_field, value_field)

        self.emit_changes(item, key_field, value_field)

    def emit_changes(
        self,
        item: QStandardItem | OrderedDictItem | DictionaryEntryItem,
        key_field: QLineEdit | QLabel,
        value_field: QLineEdit | QPushButton | CustomComboBox,
    ):
        if isinstance(key_field, QLineEdit):
            key_field.editingFinished.connect(
                lambda: self.key_updated.emit(item.index(), key_field.text())
            )

        if isinstance(value_field, QLineEdit):
            value_field.editingFinished.connect(
                lambda: self.value_updated.emit(item.index(), value_field.text())
            )

        if isinstance(value_field, CustomComboBox):
            value_field.currentTextChanged.connect(
                lambda: self.combobox_updated.emit(
                    item.index(), value_field.currentText()
                )
            )

    def create_form_widget(
        self, parent_item: QStandardItem | OrderedDictItem | DictionaryEntryItem | None
    ):
        if not parent_item:
            return

        form_widget = QWidget(self)
        form_layout = QFormLayout()
        form_widget.setLayout(form_layout)

        if not parent_item.hasChildren() and isinstance(
            parent_item, DictionaryEntryItem
        ):
            # we have a dictionary entry item
            self.add_kv_pair(parent_item, form_layout)
        elif isinstance(parent_item, (QStandardItem, OrderedDictItem)):
            for row in range(parent_item.rowCount()):
                item = parent_item.child(row)
                if item:
                    if isinstance(item, DictionaryEntryItem):
                        self.add_kv_pair(item, form_layout)
                    elif isinstance(item, OrderedDictItem):
                        self.add_odict_item(item, form_layout)

            # button for easier adding of fields
            add_btn = QPushButton("Add...", form_widget)
            add_btn.clicked.connect(self.on_add_btn_pressed)
            form_layout.addRow(add_btn)

        return form_widget

    def update_form_widget(self, widget: QWidget):
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(widget)
        self.stacked_layout.addWidget(self.scroll_area)
        self.stacked_layout.setCurrentWidget(self.scroll_area)

    def on_combo_item_highlighted(self, item: QStandardItem):
        self.combobox_highlighted.emit(item)

    def on_combo_closed(self):
        self.combobox_closed.emit()

    def on_goto_button_pressed(self, item: QStandardItem):
        self.go_to_item.emit(item)

        widget = self.create_form_widget(item)
        if widget:
            self.update_form_widget(widget)

    def on_add_btn_pressed(self):
        self.add_field.emit()

    def get_button_from_index(self, index: QPersistentModelIndex):
        return self.index_to_button.get(index)

    def update_info_display(self, text: str):
        self.information_display.set_information(text)

    def clear_info_display(self):
        self.information_display.clear_information()
