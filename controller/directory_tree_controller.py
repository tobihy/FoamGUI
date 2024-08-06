from typing import Callable

from PyQt6.QtCore import QItemSelection, QModelIndex, QObject, pyqtSignal

from controller.commands.command import (
    ClearDictCommand,
    CreateChildCommand,
    CreateFileCommand,
    CreateItemCommand,
    DeleteFileCommand,
    DeleteItemCommand,
    StandardiseFieldCommand,
)
from controller.commands.command_handler import CommandHandler
from controller.crud_manager import CRUDManager
from controller.error_handler import ErrorHandler
from env_var.environment import EnvironmentVariables
from model.custom_ordered_dict import CustomOrderedDict
from model.model import OrderedDictModel
from util.constants import ModelCreateType, ModelDeleteType
from util.exceptions import InvalidModelIndexError
from view.components.directory_tree import DirectoryTree


class DirectoryTreeController(QObject):
    tree_selection_changed = pyqtSignal(QItemSelection, QItemSelection)
    operation_completed = pyqtSignal(str)

    def __init__(
        self,
        view: DirectoryTree,
        model: OrderedDictModel,
        env_var: EnvironmentVariables,
        crud_manager: CRUDManager,
        command_handler: CommandHandler,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.model = model
        self.view = view
        self.env_var = env_var

        # handler for CRUD operations
        self.crud_manager = crud_manager

        # handler for errors
        self.error_handler = ErrorHandler()

        # handler for commands
        self.command_handler = command_handler

        self.setup_connections()

    def setup_connections(self):
        # refresh view on case directory update
        self.env_var.caseDirectoryChanged.connect(self.view.initUI)

        tree_selection_model = self.view.selectionModel()
        if tree_selection_model:
            tree_selection_model.selectionChanged.connect(
                self.tree_selection_changed.emit
            )

        # connections for context menus
        self.view.show_dict_menu.connect(self.crud_manager.show_dict_menu)
        self.view.show_field_menu.connect(self.crud_manager.show_field_menu)

        # connections for CRUD operations
        # C - create
        self.crud_manager.new_file_created.connect(
            lambda index, file_name: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateFileCommand(self.model, index, file_name)
                ),
                f"New file '{file_name}' created.",
            )
        )
        self.crud_manager.new_nested_entry.connect(
            lambda index, key, value: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateChildCommand(
                        self.model, ModelCreateType.CHILD, index, key, value
                    )
                ),
                f"Nested item {key}:{value} inserted.",
            )
        )
        self.crud_manager.new_nested_dict.connect(
            lambda index, key: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateChildCommand(
                        self.model,
                        ModelCreateType.CHILD,
                        index,
                        key,
                        CustomOrderedDict(),
                    )
                ),
                f"Nested dictionary with name {key} inserted.",
            )
        )
        self.crud_manager.add_dict_above.connect(
            lambda index, key: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateItemCommand(
                        self.model,
                        ModelCreateType.BEFORE,
                        index,
                        key,
                        CustomOrderedDict(),
                    )
                ),
                f"Dictionary {key} added.",
            )
        )
        self.crud_manager.add_dict_below.connect(
            lambda index, key: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateItemCommand(
                        self.model,
                        ModelCreateType.AFTER,
                        index,
                        key,
                        CustomOrderedDict(),
                    )
                ),
                f"Dictionary {key} added.",
            )
        )
        self.crud_manager.add_row_above.connect(
            lambda index, key, value: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateItemCommand(
                        self.model, ModelCreateType.BEFORE, index, key, value
                    )
                ),
                f"Item {key}:{value} added.",
            )
        )
        self.crud_manager.add_row_below.connect(
            lambda index, key, value: self.safe_execute(
                lambda: self.command_handler.execute(
                    CreateItemCommand(
                        self.model, ModelCreateType.AFTER, index, key, value
                    )
                ),
                f"Item {key}:{value} added.",
            )
        )

        # U - update
        self.crud_manager.fields_standardised.connect(
            lambda index: self.safe_execute(
                lambda: self.command_handler.execute(
                    StandardiseFieldCommand(self.model, index)
                ),
                "Boundary fields standardised.",
            )
        )

        # D - delete
        self.crud_manager.item_deleted.connect(
            lambda index: self.safe_execute(
                lambda: self.command_handler.execute(
                    DeleteItemCommand(self.model, ModelDeleteType.KEY_VALUE, index)
                ),
                f"Item deleted.",
            )
        )
        self.crud_manager.file_deleted.connect(
            lambda index: self.safe_execute(
                lambda: self.command_handler.execute(
                    DeleteFileCommand(self.model, index)
                ),
                "File deleted.",
            )
        )
        self.crud_manager.entries_cleared.connect(
            lambda index: self.safe_execute(
                lambda: self.command_handler.execute(
                    ClearDictCommand(self.model, index)
                ),
                "Entries in dictionary cleared.",
            )
        )

    def safe_execute(
        self, func: Callable, default_message: str = "Operation completed successfully."
    ):
        try:
            res = func()
            if res:
                self.operation_completed.emit(res)
            else:
                self.operation_completed.emit(default_message)
        except Exception as e:
            self.error_handler.handle_error(e)

    def jump_to_item(self, index: QModelIndex):
        if not index.isValid():
            raise InvalidModelIndexError(index)

        self.view.expand_selection(index)
        self.view.setCurrentIndex(index)
