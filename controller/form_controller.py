from typing import Callable

from PyQt6.QtCore import QItemSelection, QModelIndex, QObject, pyqtSignal
from PyQt6.QtGui import QStandardItem

from controller.commands.command import Command, UpdateItemCommand
from controller.commands.command_handler import CommandHandler
from controller.crud_manager import CRUDManager
from controller.error_handler import ErrorHandler
from model.model import ComboBoxModel, OrderedDictItem, OrderedDictModel
from util.boundary_conditions import DROPDOWN_CHOICES
from util.constants import ModelCreateType, ModelUpdateType, ODictType
from view.components.form import FieldEditor


class FieldEditorController(QObject):
    jump_to_item = pyqtSignal(QModelIndex)
    operation_completed = pyqtSignal(str)

    def __init__(
        self,
        model: OrderedDictModel,
        view: FieldEditor,
        crud_manager: CRUDManager,
        command_handler: CommandHandler,
    ):
        super().__init__()
        self.model = model
        self.view = view
        self.crud_manager = crud_manager
        self.command_handler = command_handler
        self.error_handler = ErrorHandler()

        # Connect signals and slots
        self.view.current_selection_changed.connect(self.handle_selection_change)
        self.view.go_to_item.connect(self.handle_go_to_item)
        self.model.dataChanged.connect(self.handle_model_data_changed)
        self.view.combobox_highlighted.connect(self.handle_combo_selection)
        self.view.combobox_closed.connect(self.handle_combo_defocus)
        self.view.add_field.connect(self.handle_add_field)

        self.view.key_updated.connect(self.on_key_editing_finished)
        self.view.value_updated.connect(self.on_value_editing_finished)
        self.view.combobox_updated.connect(self.on_value_editing_finished)

    def handle_model_data_changed(
        self, top_left: QModelIndex, bottom_right: QModelIndex, roles
    ):
        for row in range(top_left.row(), bottom_right.row() + 1):
            for col in range(top_left.column(), bottom_right.column() + 1):
                # update view by rerendering parent item
                item = self.model.customItemFromIndex(self.current_selection)
                updated_widget = self.view.create_form_widget(item)
                if updated_widget:
                    self.view.update_form_widget(updated_widget)

    def handle_selection_change(
        self, selected: QItemSelection, deselected: QItemSelection | None = None
    ):
        for selection in selected.indexes():
            self.current_selection = selection
            item = self.model.customItemFromIndex(selection)
            form_widget = self.view.create_form_widget(item)
            if form_widget:
                self.view.update_form_widget(form_widget)

    def handle_go_to_item(self, item: QStandardItem):
        selection = self.model.indexFromItem(item)
        self.jump_to_item.emit(selection)

    def handle_combo_selection(self, item: QStandardItem):
        category = item.data(ComboBoxModel.ROLE_BOUNDARY_CATEGORY)
        choice = item.text()
        description = DROPDOWN_CHOICES.get(category, {}).get(
            choice, "No description available"
        )
        self.view.update_info_display(description)

    def handle_combo_defocus(self):
        self.view.clear_info_display()

    def handle_add_field(self):
        item = self.current_selection
        item_type = item.data(OrderedDictItem.ROLE_TYPE)

        if item_type in {
            ODictType.ZERO_DIR,
            ODictType.SYSTEM_DIR,
            ODictType.CONSTANT_DIR,
        }:
            self.crud_manager.show_new_file_dialog(item)
        else:
            self.crud_manager.show_add_row_dialog(
                ModelCreateType.CHILD, self.current_selection
            )

    def on_key_editing_finished(self, index: QModelIndex, new_key: str):
        self.safe_execute(
            UpdateItemCommand(self.model, ModelUpdateType.KEY, index, new_key),
        )

    def on_value_editing_finished(self, index: QModelIndex, new_value: str):
        self.safe_execute(
            UpdateItemCommand(self.model, ModelUpdateType.VALUE, index, new_value),
        )

    def safe_execute(self, command: Command):
        try:
            success_message = self.command_handler.execute(command)
            self.operation_completed.emit(success_message)
        except Exception as e:
            self.error_handler.handle_error(e)
