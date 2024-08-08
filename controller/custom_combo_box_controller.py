from typing import Union

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QStandardItem

from model.model import ComboBoxModel
from view.components.custom_combo_box import CustomComboBox


class CustomComboBoxController(QObject):
    combo_item_highlighted = pyqtSignal(QStandardItem)
    combo_focus_lost = pyqtSignal()

    def __init__(
        self, view: CustomComboBox, data: dict, current_choice: Union[str, None] = None
    ):
        super().__init__()
        self.view = view
        self.item_model = ComboBoxModel(data, self.view)

        self.default_item = QStandardItem("Select...")
        self.default_item.setSelectable(False)
        self.item_model.appendRow(self.default_item)
        self.item_model.load_model(data)

        self.view.set_data(self.item_model)
        self.view.highlighted.connect(lambda index: self.on_highlighted(index))
        self.view.currentIndexChanged.connect(self.on_new_choice_selected)
        self.view.focus_out_event.connect(self.on_focus_lost)

        if current_choice:
            self.view.set_current_choice(current_choice)

    def set_data(self, data: dict):
        self.item_model.clear()
        self.item_model.load_model(data)

    def on_highlighted(self, index: int):
        item = self.item_model.item(index)
        if item:
            self.combo_item_highlighted.emit(item)

    def on_focus_lost(self):
        self.combo_focus_lost.emit()

    def on_new_choice_selected(self):
        self.combo_focus_lost.emit()
