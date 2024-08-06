from pathlib import Path
from typing import Iterable

from PyQt6.QtCore import QModelIndex, QObject, Qt
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel

from model.custom_ordered_dict import CustomOrderedDict
from model.database import Database
from util.constants import ModelCreateType, ModelDeleteType, ModelUpdateType, ODictType
from util.exceptions import DuplicateKeyError, InvalidModelIndexError


class DictionaryEntryItem(QStandardItem):
    """
    DictionaryEntryItem is a subclass of QStandardItem that represents a key-value pair within a dictionary.

    Attributes:
        key (str): The key to the dictionary entry.
        value (str): The value of the dictionary entry.
        is_editable (bool): Flag indicating whether the item is editable.
    """

    def __init__(
        self, key: str, value: str, is_editable: bool = True, is_flag: bool = False
    ) -> None:
        super().__init__()
        self.key = key
        self.value = value
        self.dict_id = key
        self.is_flag = is_flag
        self.setEditable(is_editable)
        self.initUI()

    def initUI(self):
        self.update_display()

    def set_key(self, key: str):
        self.key = key
        self.dict_id = key
        self.update_display()

    def set_value(self, value: str):
        self.value = value
        self.update_display()

    def update_display(self):
        if not self.value:
            self.setText(f"{self.key}")
        else:
            self.setText(f"{self.key}: {self.value}")

    def no_value(self):
        return self.is_flag


class OrderedDictItem(QStandardItem):
    ROLE_KEY = Qt.ItemDataRole.UserRole + 1
    ROLE_TYPE = Qt.ItemDataRole.UserRole + 2

    """
    OrderedDictItem is a subclass of QStandardItem that represents a folder or dictionary name
    in OpenFOAM input files.

    Attributes:
        text (str): The text to be displayed for this item.
        is_editable (bool): A flag indicating whether this item is editable.
    """

    def __init__(self, text: str) -> None:
        super().__init__()
        self.dict_id = text
        self.set_key(text)
        self.initUI(text)

    def initUI(self, text: str):
        item_type = self.determine_item_type(text)
        self.setData(item_type, OrderedDictItem.ROLE_TYPE)
        self.set_display_text_and_icon(text, item_type)

    def determine_item_type(self, text: str):
        path = Path(text)
        if path.is_dir():
            name = path.name
            if name == "0":
                return ODictType.ZERO_DIR
            elif name == "constant":
                return ODictType.CONSTANT_DIR
            elif name == "system":
                return ODictType.SYSTEM_DIR
            else:
                return ODictType.OTHER_DIR
        elif path.is_file():
            return ODictType.FILE
        elif text == "boundaryField":
            return ODictType.BOUNDARY_FIELD
        else:
            return ODictType.OTHER

    def set_display_text_and_icon(self, text: str, type: ODictType):
        if type in {
            ODictType.ZERO_DIR,
            ODictType.CONSTANT_DIR,
            ODictType.SYSTEM_DIR,
            ODictType.OTHER_DIR,
            ODictType.FILE,
        }:
            name = Path(text).name
        else:
            name = text
        self.setText(name)

        if type in {ODictType.ZERO_DIR, ODictType.CONSTANT_DIR, ODictType.SYSTEM_DIR}:
            self.setIcon(QIcon.fromTheme("folder"))

    # only for dictionary items, not subdirectories
    def set_key(self, key: str):
        self.dict_id = key
        self.setData(key, OrderedDictItem.ROLE_KEY)
        self.key = key
        self.setText(key)


class OrderedDictModel(QStandardItemModel):
    """
    Custom model that stores and displays data extracted from a CustomOrderedDict.

    This class extends QStandardItemModel to create a model that can hold and display
    hierarchical data stored in a CustomOrderedDict. It provides methods to load and
    update the model with data from the CustomOrderedDict.

    Attributes:
        _data (CustomOrderedDict): The data to be stored and displayed in the model.

    Methods:
        load_model(data: CustomOrderedDict | str, parent_item: QStandardItem | None):
            Recursively loads data from a CustomOrderedDict object into the model.
        update_model():
            Updates the model by loading the data from the CustomOrderedDict into the
            invisible root item.
    """

    def __init__(self, db: Database, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self._data = self.db.get_dict()

    def flags(self, index):
        default_flags = super().flags(index)
        item = self.itemFromIndex(index)
        if item and item.isEditable():
            return default_flags | Qt.ItemFlag.ItemIsEditable
        return default_flags

    def handle_selection_change(self, item: QStandardItem):
        self.current_selection = item

    def is_duplicate_key(self, key: str, odict: CustomOrderedDict):
        if key in odict.keys():
            return True
        return False

    def load_model(
        self,
        data: CustomOrderedDict,
        parent_item: QStandardItem | OrderedDictItem | None,
    ):
        """
        Recursively loads data from a CustomOrderedDict object into the model.

        This method traverses the CustomOrderedDict and creates QStandardItem instances
        for each key-value pair. If a value is another CustomOrderedDict, the method
        calls itself recursively to process the nested dictionary. If a value is a
        string, it creates a QStandardItem with the string.

        Parameters:
        -----------
            data (CustomOrderedDict | str): The data to be loaded into the model.
            parent_item (QStandardItem | None): The parent item to which the data will be appended. If None, the method returns.
        """
        if not parent_item:
            return

        # Clear all entries in parent_item
        parent_item.removeRows(0, parent_item.rowCount())

        for key, value in data.items():
            if isinstance(value, CustomOrderedDict):
                # Create a new OrderedDictItem for nested dictionaries
                item = OrderedDictItem(key)
                self.load_model(value, item)
                parent_item.appendRow(item)
            else:
                # Create a new DictionaryEntryItem for normal key-value pairs
                if not value:
                    item = DictionaryEntryItem(
                        key, "-", is_editable=False, is_flag=True
                    )
                else:
                    item = DictionaryEntryItem(key, str(value))
                parent_item.appendRow(item)

    def update_model(self):
        """
        Updates the model by loading the data from the CustomOrderedDict into the
        invisible root item.

        This method clears the existing data in the model and reloads it from the
        CustomOrderedDict, ensuring that the model reflects the current state of the
        data. As such, all listeners dependent on the model will be rerendered.
        """
        self.load_model(self._data, self.invisibleRootItem())

    def get_key_path(self, index: QModelIndex) -> list[str]:
        key_path = []
        curr_index = index
        while curr_index.isValid():
            item = self.customItemFromIndex(curr_index)
            if not item:
                raise InvalidModelIndexError(curr_index)
            key_path.insert(0, item.dict_id)
            curr_index = curr_index.parent()

        return key_path

    def index_from_key_path(self, key_path: Iterable[str]) -> QModelIndex:
        # TODO: fix bug with this function
        """Converts a key_path (list of ids) back to a QModelIndex."""
        root_item = self.invisibleRootItem()  # Start from the root index
        if not root_item:
            raise ValueError(f"Root item not found.")

        curr_index = root_item.index()

        for item_id in key_path:
            item_found = False
            # Traverse child indices
            for row in range(self.rowCount(curr_index)):
                child_index = self.index(row, 0, curr_index)
                child_item = self.customItemFromIndex(child_index)
                if child_item and child_item.dict_id == item_id:
                    curr_index = child_index
                    item_found = True
                    break

            if not item_found:
                return QModelIndex()  # Return an invalid index if not found

        return curr_index

    def customItemFromIndex(self, index):
        item = self.itemFromIndex(index)
        if isinstance(item, (DictionaryEntryItem, OrderedDictItem)):
            return item
        return None

    def insert_new_file(
        self,
        index: QModelIndex,
        file_name: str,
        content: CustomOrderedDict = CustomOrderedDict(),
        target_row: int | None = None,
    ):
        """
        Inserts a new file into the model at the specified index.

        Parameters:
        -----------
        index : QModelIndex
            The index in the model where the new file will be inserted.
        file_name : str
            The name of the new file to be created and inserted.

        Returns:
        --------
        new_file_item : OrderedDictItem
            The newly created and inserted file item.

        Raises:
        -------
        InvalidModelIndexError
            If the provided index is invalid and does not correspond to a valid item in the model.
        """
        key_path = self.get_key_path(index)
        last_key = key_path[-1]

        item = self.customItemFromIndex(index)
        if not item:
            raise InvalidModelIndexError(index)

        new_file_path = Path(item.key, file_name)
        new_file_path_str = str(new_file_path)
        new_file_item = OrderedDictItem(new_file_path_str)
        new_file_item.setText(file_name)

        # create file
        self.db.create_file(last_key, new_file_path_str, "dictionary", content)

        # modify model
        row_count = item.rowCount()
        self._data.insert(key_path, file_name, content)
        if target_row is not None:
            item.insertRow(target_row, new_file_item)
        else:
            item.insertRow(row_count, new_file_item)

        if content:
            self.load_model(content, new_file_item)

        # notify observers of changes
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

        return new_file_item.index()

    def insert_new_data(
        self,
        create_type: ModelCreateType,
        index: QModelIndex,
        key: str,
        value: str | CustomOrderedDict,
        duplicate_allowed: bool = False,
    ):
        """
        Inserts new data into the model at the specified location based on the creation type.

        Parameters:
        -----------
        create_type : ModelCreateType
            The type of creation operation to perform (CHILD, BEFORE, or AFTER).
        index : QModelIndex
            The index in the model where the new data will be inserted.
        key : str
            The key for the new data entry.
        value : str or CustomOrderedDict
            The value for the new data entry.
        duplicate_allowed : bool, optional
            Whether duplicate keys are allowed in the current dictionary (default is False).

        Returns:
        --------
        new_item : DictionaryEntryItem or OrderedDictItem
            The newly created and inserted model item.

        Raises:
        -------
        ValueError
            If the current dictionary is not an instance of `CustomOrderedDict`.
        DuplicateKeyError
            If a duplicate key is detected and duplicates are not allowed.
        InvalidModelIndexError
            If the provided index or its parent is invalid.
        """
        key_path = self.get_key_path(index)
        last_key = key_path[-1]
        parent_key_path = self.get_key_path(index.parent())
        if create_type == ModelCreateType.CHILD:
            curr_dict = self._data.get_nested_value(key_path)
        elif (
            create_type == ModelCreateType.AFTER
            or create_type == ModelCreateType.BEFORE
        ):
            curr_dict = self._data.get_nested_value(parent_key_path)

        if not isinstance(curr_dict, CustomOrderedDict):
            raise ValueError(
                f"Expected CustomOrderedDict, got {str(type(curr_dict))} instead."
            )
        if not duplicate_allowed and self.is_duplicate_key(key, curr_dict):
            raise DuplicateKeyError(key)

        item = self.customItemFromIndex(index)
        if not item:
            raise InvalidModelIndexError(index)

        parent_item = item.parent()
        if not parent_item:
            raise InvalidModelIndexError(index)

        # create model item
        if isinstance(value, str):
            new_item = DictionaryEntryItem(key, value)
        elif isinstance(value, CustomOrderedDict):
            new_item = OrderedDictItem(key)
            self.load_model(value, new_item)

        row = index.row()
        parent_index = parent_item.index()
        # modify model
        if create_type == ModelCreateType.BEFORE:
            self._data.insert(parent_key_path, key, value, insert_key=item.key)
            parent_item.insertRow(row, new_item)
        elif create_type == ModelCreateType.AFTER:
            self._data.insert(
                parent_key_path, key, value, insert_key=item.key, after=True
            )
            parent_item.insertRow(row + 1, new_item)
        elif create_type == ModelCreateType.CHILD:
            self._data.insert(key_path, key, value)
            item.insertRow(item.rowCount(), new_item)

        # update database
        if Path(last_key).exists():
            self.db.update_file(key_path)
            index_changed = index
        else:
            self.db.update_file(parent_key_path)
            index_changed = parent_item.index()

        # notify observers of changes
        self.dataChanged.emit(
            index_changed, index_changed, [Qt.ItemDataRole.DisplayRole]
        )

        return new_item.index()

    def update_data(self, type: ModelUpdateType, index: QModelIndex, new_data: str):
        """
        Update data at the specified model index based on the given update type.

        Parameters:
        -----------
        type : ModelUpdateType
            The type of update operation to perform (KEY or VALUE).
        index : QModelIndex
            The index in the model where the data will be updated.
        new_data : str
            The new data to update (either a new key or a new value).

        Raises:
        -------
        InvalidModelIndexError
            If the provided index does not correspond to a valid item in the model.
        """
        item = self.customItemFromIndex(index)
        if not item:
            raise InvalidModelIndexError(index)

        old_data = None
        if type == ModelUpdateType.KEY:
            old_data = self.update_key(item, index, new_data)
        elif type == ModelUpdateType.VALUE and isinstance(item, DictionaryEntryItem):
            old_data = self.update_value(item, index, new_data)

        return old_data

    def update_key(
        self,
        item: DictionaryEntryItem | OrderedDictItem,
        index: QModelIndex,
        new_key: str,
    ):
        """
        Update key at the specified model item.

        Parameters:
        -----------
        item : DictionaryEntryItem | OrderedDictItem
            The model item whose key is to be updated.
        index : QModelIndex
            The index in the model where the item is located.
        new_key : str
            The new key to update to.

        Raises:
        -------
        ValueError
            If the current dictionary is not an instance of `CustomOrderedDict`.
        DuplicateKeyError
            If a duplicate key is detected in the current dictionary.
        """
        key_path = self.get_key_path(index.parent())
        curr_dict = self._data.get_nested_value(key_path)

        if not isinstance(curr_dict, CustomOrderedDict):
            raise ValueError("Expected CustomOrderedDict, got string instead.")

        if self.is_duplicate_key(new_key, curr_dict):
            raise DuplicateKeyError(new_key)

        old_key = item.key
        if isinstance(item, (DictionaryEntryItem, OrderedDictItem)):
            item.set_key(new_key)
        self._data.rename_key(key_path, old_key, new_key)
        self.db.update_file(key_path)

        return old_key

    def update_value(
        self,
        item: DictionaryEntryItem,
        index: QModelIndex,
        new_value: str,
    ):
        """
        Update value at the specified model item.

        Parameters:
        -----------
        item : DictionaryEntryItem
            The model item whose value is to be updated.
        index : QModelIndex
            The index in the model where the item is located.
        new_value : str
            The new value to update to.
        """

        old_value = item.value
        key_path = self.get_key_path(index.parent())
        item.set_value(new_value)
        self._data.update_nested_value(key_path, item.key, new_value)
        self.db.update_file(key_path)

        return old_value

    def update_dict(self, index: QModelIndex, data: CustomOrderedDict):
        target_item = self.customItemFromIndex(index)
        if not isinstance(target_item, OrderedDictItem):
            raise ValueError(
                "Expected OrderedDictItem, got DictionaryEntryItem instead."
            )

        key_path = self.get_key_path(index)[:-1]
        print(key_path)
        print(target_item.key)
        self._data.update_nested_value(key_path, target_item.key, data)
        self.db.update_file(key_path)
        self.load_model(data, target_item)

    def find_field(self, parent_item: QStandardItem, type: ODictType):
        """
        Searches for and returns an item with a specified ODictType among the children of the given parent item.

        Parameters:
        -----------
        parent_item : QStandardItem
            The parent item whose children will be searched.
        type : ODictType
            The type of ODictType to search for among the children of the parent item.

        Returns:
        --------
        QModelIndex
            The index of the found item with the specified ODictType, or an invalid QModelIndex if no matching item is found.
        """

        for row in range(parent_item.rowCount()):
            child_item = parent_item.child(row)
            if not child_item:
                return QModelIndex()
            if child_item.data(OrderedDictItem.ROLE_TYPE) == type:
                return self.indexFromItem(child_item)
        return QModelIndex()  # Return an invalid index if boundaryField is not found

    def standardise_all_items(self, template_item_index: QModelIndex):
        """
        Standardises a first-level dictionary item across all items within the current subdirectory.

        Parameters:
        -----------
        template_item_index : QModelIndex
            The index of the template item to use for standardisation.

        Raises:
        -------
        InvalidModelIndexError
            If the provided template item index or subdirectory item index does not correspond to a valid item in the model.
        ValueError
            If a child item is expected but not found, or if a target field required for standardisation is missing.
        """
        template_item = self.customItemFromIndex(template_item_index)
        if not template_item:
            raise InvalidModelIndexError(template_item_index)
        template_type = template_item.data(OrderedDictItem.ROLE_TYPE)

        file_index = template_item_index.parent()
        subdir_index = file_index.parent()

        # Get the parent item from the parent index
        subdir_item = self.customItemFromIndex(subdir_index)
        if not subdir_item:
            raise InvalidModelIndexError(subdir_index)

        # dictionary to store file:content mapping to be cached for undo/redo
        cache = dict()

        # Iterate through all children of parent item
        for row in range(subdir_item.rowCount()):
            child_item = subdir_item.child(row)
            if not child_item:
                raise ValueError(f"Expected item at row {row}, but got None")

            # Look for same item in child
            target_field_index = self.find_field(child_item, template_type)

            if target_field_index.isValid():
                key_path_to_child = self.get_key_path(target_field_index)
                key_path_tuple = tuple(key_path_to_child)

                # store in cache
                cache[key_path_tuple] = self._data.get_nested_value(
                    self.get_key_path(target_field_index)
                )
                self.standardise_to_item(target_field_index, template_item_index)
            else:
                raise ValueError(
                    f"Missing target field required to standardise in item '{child_item.text()}'"
                )

        return cache

    def standardise_to_item(
        self,
        target_index: QModelIndex,
        template_index: QModelIndex,
    ):
        """
        Given a target and a template item, map over all keys from the template to the target.
        If the target item contains the key, it retains the value associated with the key.
        If the target item does not contain the key, the associated value in the template is mapped over to the target.

        Parameters:
        -----------
        target_index : QModelIndex
            The index of the target item to be standardised.
        template_index : QModelIndex
            The index of the template item to use for standardisation.

        Raises:
        -------
        InvalidModelIndexError
            If the provided template index does not correspond to a valid item in the model.
        ValueError
            If the dictionary associated with the template item is not an instance of `CustomOrderedDict`.
        """
        # same field in the file
        if target_index == template_index:
            return

        template_item = self.customItemFromIndex(template_index)
        if not template_item:
            raise InvalidModelIndexError(template_index)

        # find the template
        template_key_path = self.get_key_path(template_index)
        template_dict = self._data.get_nested_value(template_key_path)
        if not isinstance(template_dict, CustomOrderedDict):
            raise ValueError("Dictionary expected, got str instead")

        target_item = self.customItemFromIndex(target_index)
        target_key_path = self.get_key_path(target_index)
        target_dict = self._data.get_nested_value(target_key_path)

        if isinstance(target_dict, CustomOrderedDict):
            revised_dict = template_dict.map_keys_to_target_dict(target_dict)
            self.load_model(revised_dict, target_item)
            self._data.update_nested_value(
                target_key_path[:-1], target_key_path[-1], revised_dict
            )
            self.db.update_file(target_key_path[:-1])
        else:
            self.delete_data(ModelDeleteType.KEY_VALUE, target_index)

    def delete_data(self, delete_type: ModelDeleteType, index: QModelIndex):
        """
        Delete data from the model with the given index, according to the given delete type.

        This function performs the following actions based on the delete type:
        - `ModelDeleteType.KEY_VALUE`: Removes a key-value pair from the model and updates the database.
        - `ModelDeleteType.CLEAR_DICT`: Removes all key-value pairs within a dictionary item in the model and updates the database.
        - `ModelDeleteType.FILE`: Deletes a file associated with the index from the database.

        Parameters:
        -----------
        type : ModelDeleteType
            The type of deletion operation to perform (KEY_VALUE, CLEAR_DICT, FILE).
        index : QModelIndex
            The index of the item in the model from which data should be deleted.

        Raises:
        -------
        InvalidModelIndexError
            If the provided index does not correspond to a valid item in the model.
        """

        item = self.customItemFromIndex(index)
        if not item:
            raise InvalidModelIndexError(index)

        def delete_kv(item):
            key, value = item.key, None
            if isinstance(item, DictionaryEntryItem):
                value = item.value
            elif isinstance(item, OrderedDictItem):
                value = self._data.get_nested_value(self.get_key_path(index))
            row = item.row()
            parent_index = index.parent()
            key_path = self.get_key_path(parent_index)

            self._data.remove(key_path, item.key)
            self.db.update_file(key_path)
            self.removeRow(row, parent_index)

            return key, value

        def clear_dict(item):
            key_path = self.get_key_path(index)
            dict_name = key_path[-1]
            deleted_data = self._data.get_nested_value(key_path)

            if not isinstance(deleted_data, CustomOrderedDict):
                raise ValueError("Expected CustomOrderedDict, got str instead.")
            to_return_data = deleted_data.copy()

            self._data.remove_all(key_path)
            self.db.update_file(key_path)
            item.removeRows(0, item.rowCount())

            return dict_name, to_return_data

        def delete_file(item: QStandardItem):
            key_path = self.get_key_path(index)
            file_path = key_path[-1]
            row = item.row()
            parent_index = index.parent()

            foam_file = self.db.get_foamfile(key_path)
            foam_content = foam_file.read()

            self.db.delete_file(file_path)
            self.removeRow(row, parent_index)

            return foam_file, foam_content

        if delete_type == ModelDeleteType.KEY_VALUE:
            return delete_kv(item)
        elif delete_type == ModelDeleteType.CLEAR_DICT:
            return clear_dict(item)
        elif delete_type == ModelDeleteType.FILE:
            return delete_file(item)


class ComboBoxModel(QStandardItemModel):
    # Define custom roles
    ROLE_ITEM_TYPE = Qt.ItemDataRole.UserRole + 1
    TYPE_PARENT = 1
    TYPE_CHILD = 2

    ROLE_BOUNDARY_CATEGORY = Qt.ItemDataRole.UserRole + 2
    CATEGORY_BASIC = "Basic"
    CATEGORY_CYCLIC = "Cyclic"
    CATEGORY_INLET = "Inlet"
    CATEGORY_OUTLET = "Outlet"
    CATEGORY_WALL = "Wall"
    CATEGORY_COUPLED = "Coupled"
    CATEGORY_GENERIC = "Generic"

    def __init__(self, combo_data: dict, parent=None):
        super().__init__(parent)
        self.combo_data = combo_data

    def load_model(self, data: dict, parent_item: QStandardItem | None = None):
        """
        Recursively loads a standard item model for the `boundaryField` custom combo box from a
        dictionary.

        Parameters:
        -----------
        data (dict): The dictionary to be converted into the model. Keys are used as item text, and values
            determine child items.
        parent_item (QStandardItem | None): The parent item for the current level of recursion. If None,
            the method assumes it is processing root-level items.
        """
        for obj in data.items():
            key, value = obj[0], obj[1]
            item = QStandardItem(key)
            if parent_item:
                item.setData(ComboBoxModel.TYPE_CHILD, ComboBoxModel.ROLE_ITEM_TYPE)
                item.setData(parent_item.text(), ComboBoxModel.ROLE_BOUNDARY_CATEGORY)
                item.setSelectable(True)
                self.appendRow(item)
            else:
                item.setData(ComboBoxModel.TYPE_PARENT, ComboBoxModel.ROLE_ITEM_TYPE)
                item.setSelectable(False)
                self.appendRow(item)
                self.load_model(value, item)
