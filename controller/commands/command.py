from abc import ABC, abstractmethod
from pathlib import Path

from PyQt6.QtCore import QModelIndex, QPersistentModelIndex

from model.core.foamfile import FoamFile
from model.custom_ordered_dict import CustomOrderedDict
from model.model import (
    ModelCreateType,
    ModelDeleteType,
    ModelUpdateType,
    OrderedDictModel,
)
from util.exceptions import InvalidModelIndexError


class Command(ABC):
    def __init__(self, model: OrderedDictModel) -> None:
        super().__init__()
        self.model = model

    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass


class CreateFileCommand(Command):
    def __init__(
        self, model: OrderedDictModel, index: QModelIndex, file_name: str
    ) -> None:
        super().__init__(model)
        self.index = QPersistentModelIndex(index)
        self.file_name = file_name
        self.key_path = self.model.get_key_path(QModelIndex(self.index))

        self.file_created_index = None

    def undo(self):
        if not self.file_created_index:
            raise ValueError("Missing QModelIndex for command.")

        # if index has become invalid, refresh it by retrieving it
        if not self.file_created_index.isValid():
            self.file_created_index = self.model.index_from_key_path(self.key_path)

        if self.file_created_index and self.file_created_index.isValid():
            self.model.delete_data(
                ModelDeleteType.FILE, QModelIndex(self.file_created_index)
            )

        return f"File '{self.file_name}' deleted."

    def redo(self):
        self.file_created_index = QPersistentModelIndex(
            self.model.insert_new_file(QModelIndex(self.index), self.file_name)
        )

        return f"File '{self.file_name}' created."

    def __str__(self) -> str:
        return "CreateFileCommand"


class CreateItemCommand(Command):
    def __init__(
        self,
        model: OrderedDictModel,
        create_type: ModelCreateType,
        index: QModelIndex,
        key: str,
        value: str | CustomOrderedDict,
        duplicate_allowed: bool = False,
    ) -> None:
        super().__init__(model)
        self.target_row = index.row()
        self.target_col = index.column()
        self.create_type = create_type
        self.index = QPersistentModelIndex(index)
        self.parent_index = QPersistentModelIndex(index.parent())
        self.key = key
        self.value = value
        self.duplicate_allowed = duplicate_allowed

    def undo(self):
        target_index = self.model.index(
            self.target_row, self.target_col, QModelIndex(self.parent_index)
        )

        self.model.insert_new_data(
            self.create_type, target_index, self.key, self.value, self.duplicate_allowed
        )

        return f"Item '{self.key}' deleted."

    def redo(self):
        target_index = self.model.index(
            self.target_row, self.target_col, QModelIndex(self.parent_index)
        )
        self.model.insert_new_data(
            self.create_type,
            target_index,
            self.key,
            self.value,
            self.duplicate_allowed,
        )

        return f"Item '{self.key}' created."

    def __str__(self) -> str:
        return "CreateItemCommand"


class CreateChildCommand(Command):
    def __init__(
        self,
        model: OrderedDictModel,
        create_type: ModelCreateType,
        index: QModelIndex,
        key: str,
        value: str | CustomOrderedDict,
        duplicate_allowed: bool = False,
    ) -> None:
        super().__init__(model)
        self.target_row = index.row()
        self.target_col = index.column()
        self.create_type = create_type
        self.index = QPersistentModelIndex(index)
        self.parent_index = QPersistentModelIndex(index.parent())
        self.key = key
        self.value = value
        self.duplicate_allowed = duplicate_allowed

    def undo(self):
        target_index = self.model.index(
            self.inserted_row, self.inserted_col, QModelIndex(self.index)
        )
        self.model.delete_data(ModelDeleteType.KEY_VALUE, target_index)

        return f"Nested item with key '{self.key}' deleted."

    def redo(self):
        inserted_index = self.model.insert_new_data(
            ModelCreateType.CHILD,
            QModelIndex(self.index),
            self.key,
            self.value,
            self.duplicate_allowed,
        )
        self.inserted_row, self.inserted_col = (
            inserted_index.row(),
            inserted_index.column(),
        )

        return f"Nested item with key '{self.key}' created."


class DeleteFileCommand(Command):
    def __init__(self, model: OrderedDictModel, index: QModelIndex) -> None:
        super().__init__(model)
        self.target_row = index.row()
        self.target_col = index.column()
        self.index = QPersistentModelIndex(index)
        self.parent_index = QPersistentModelIndex(index.parent())
        self.file_name = ""
        self.foam_content = None

    def undo(self):
        if not self.parent_index.isValid():
            raise InvalidModelIndexError(QModelIndex(self.parent_index))

        self.model.insert_new_file(QModelIndex(self.parent_index), self.file_name, self.foam_content, self.target_row)  # type: ignore

        return f"File {self.file_name} restored."

    def redo(self):
        if not self.parent_index.isValid():
            raise InvalidModelIndexError(QModelIndex(self.parent_index))

        self.foam_file, self.foam_content = self.model.delete_data(
            ModelDeleteType.FILE,
            self.model.index(
                self.target_row, self.target_col, QModelIndex(self.parent_index)
            ),
        )
        if isinstance(self.foam_file, FoamFile):
            self.file_name = Path(self.foam_file.path).name

        return f"File {self.file_name} deleted."

    def __str__(self) -> str:
        return "DeleteFileCommand"


class DeleteItemCommand(Command):
    def __init__(
        self, model: OrderedDictModel, delete_type: ModelDeleteType, index: QModelIndex
    ) -> None:
        super().__init__(model)
        self.target_row = index.row()
        self.target_col = index.column()
        self.index = QPersistentModelIndex(index)
        self.parent_index = QPersistentModelIndex(index.parent())
        self.delete_type = delete_type
        self.deleted_key = None
        self.deleted_value = None

    def undo(self):
        if self.deleted_key is None or self.deleted_value is None:
            return

        parent_item = self.model.customItemFromIndex(QModelIndex(self.parent_index))

        if not parent_item:
            return

        parent_model_index = QModelIndex(self.parent_index)

        if self.target_row < self.model.rowCount(parent_model_index):
            insert_item = parent_item.child(self.target_row, self.target_col)
            if insert_item:
                insert_index = insert_item.index()
            self.model.insert_new_data(
                ModelCreateType.BEFORE,
                insert_index,
                self.deleted_key,  # type: ignore
                self.deleted_value,  # type: ignore
            )
        else:
            self.model.insert_new_data(
                ModelCreateType.CHILD,
                parent_model_index,
                self.deleted_key,  # type: ignore
                self.deleted_value,  # type: ignore
            )

        return f"Item with key '{self.deleted_key}' restored."

    def redo(self):
        curr_index = self.model.index(
            self.target_row, self.target_col, QModelIndex(self.parent_index)
        )

        self.deleted_key, self.deleted_value = self.model.delete_data(
            self.delete_type, curr_index
        )

        return f"Item with key '{self.deleted_key}' deleted."

    def __str__(self) -> str:
        return "DeleteItemCommand"


class ClearDictCommand(Command):
    def __init__(self, model: OrderedDictModel, index: QModelIndex) -> None:
        super().__init__(model)
        self.target_row = index.row()
        self.target_col = index.column()
        self.parent_index = QPersistentModelIndex(index.parent())

        self.deleted_dict = None

    def undo(self):
        if not self.parent_index.isValid():
            raise InvalidModelIndexError(QModelIndex(self.parent_index))

        target_index = self.model.index(
            self.target_row, self.target_col, QModelIndex(self.parent_index)
        )
        self.model.update_dict(target_index, CustomOrderedDict(self.deleted_dict))  # type: ignore

        return f"Dictionary with key '{self.name}' restored."

    def redo(self):
        if not self.parent_index.isValid():
            raise InvalidModelIndexError(QModelIndex(self.parent_index))

        self.name, self.deleted_dict = self.model.delete_data(
            ModelDeleteType.CLEAR_DICT,
            self.model.index(
                self.target_row, self.target_col, QModelIndex(self.parent_index)
            ),
        )

        return f"Dictionary with key '{self.name}' cleared."


class UpdateItemCommand(Command):
    SUCCESS_MESSAGE = "Item {attribute} has been updated from '{old}' to '{new}'."
    UPDATE_TO_ATTRIBUTE = {ModelUpdateType.KEY: "key", ModelUpdateType.VALUE: "value"}

    def __init__(
        self,
        model: OrderedDictModel,
        update_type: ModelUpdateType,
        index: QModelIndex,
        new_data: str,
    ) -> None:
        super().__init__(model)
        self.update_type = update_type
        self.index = QPersistentModelIndex(index)
        self.new_data = new_data

        self.old_data = None

    def undo(self):
        if self.old_data:
            self.model.update_data(
                self.update_type, QModelIndex(self.index), self.old_data
            )
            return self.get_success_message(
                self.update_type, self.new_data, self.old_data
            )

    def redo(self):
        self.old_data = self.model.update_data(
            self.update_type, QModelIndex(self.index), self.new_data
        )
        return self.get_success_message(self.update_type, self.old_data, self.new_data)

    def get_success_message(
        self, update_type: ModelUpdateType, old: str | None, new: str | None
    ):
        return self.SUCCESS_MESSAGE.format(
            attribute=self.UPDATE_TO_ATTRIBUTE[update_type], old=old, new=new
        )

    def __str__(self) -> str:
        return "UpdateItemCommand"


class StandardiseFieldCommand(Command):
    def __init__(self, model: OrderedDictModel, template_index: QModelIndex) -> None:
        super().__init__(model)
        self.template_index = QPersistentModelIndex(template_index)
        self.cache = dict()

    def undo(self):
        for key_path, prev_data in self.cache.items():
            print(key_path)
            target_index = self.model.index_from_key_path(key_path)
            self.model.update_dict(target_index, prev_data)

        return "Original fields restored."

    def redo(self):
        self.cache = self.model.standardise_all_items(QModelIndex(self.template_index))
        return f"Fields standardised successfully."

    def __str__(self) -> str:
        return "StandardiseFieldCommand"
