from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PyQt6.QtTest import QSignalSpy

from model.custom_ordered_dict import CustomOrderedDict
from model.model import (
    DictionaryEntryItem,
    ODictType,
    OrderedDictItem,
    OrderedDictModel,
    QModelIndex,
)
from util.constants import ModelCreateType, ModelDeleteType, ModelUpdateType
from util.exceptions import DuplicateKeyError


@pytest.fixture
def database():
    # Mock the Database class
    class MockDatabase:
        def get_dict(self):
            return CustomOrderedDict(
                {
                    "/root": CustomOrderedDict(
                        {
                            "/root/subdir1": CustomOrderedDict(
                                {
                                    "file1": "content1",
                                    "file2": "content2",
                                    "file3": CustomOrderedDict({"content3": "test3"}),
                                }
                            ),
                            "/root/subdir2": CustomOrderedDict(
                                {
                                    "file3": CustomOrderedDict({"key3": "value3"}),
                                }
                            ),
                            "file4": "content4",
                        }
                    ),
                    "/standardise": CustomOrderedDict(
                        {
                            "/standardise/subdir1": CustomOrderedDict(
                                {
                                    "key1": "value1",
                                    "boundaryField": CustomOrderedDict(
                                        {"inlet": "test"}
                                    ),
                                }
                            ),
                            "/standardise/subdir2": CustomOrderedDict(
                                {
                                    "key1": "value1",
                                    "boundaryField": CustomOrderedDict(
                                        {"inlet": "example"}
                                    ),
                                }
                            ),
                            "/standardise/subdir3": CustomOrderedDict(
                                {"boundaryField": CustomOrderedDict({"haha": "lol"})}
                            ),
                        }
                    ),
                }
            )

        def handle_data_changed(self, key_path, data):
            pass

        def update_file(self, key_path):
            pass

    yield MockDatabase()


@pytest.fixture
def model(database):
    yield OrderedDictModel(database)


def test_get_key_path_valid(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    subdir1_item = root_item.child(0)
    subdir1_index = subdir1_item.index()
    assert model.get_key_path(subdir1_index) == ["/root", "/root/subdir1"]


def test_get_key_path_invalid(model):
    model.update_model()
    invalid_index = QModelIndex()
    assert model.get_key_path(invalid_index) == []


def test_index_from_key_path_valid(model):
    model.update_model()
    valid_key_path = ["/root", "/root/subdir1"]
    res_index = model.index_from_key_path(valid_key_path)
    assert model.get_key_path(res_index) == valid_key_path


def test_index_from_key_path_invalid(model):
    model.update_model()
    invalid_key_path = ["/root", "/root/invalid_subdir/test"]
    res_index = model.index_from_key_path(invalid_key_path)
    assert model.get_key_path(res_index) != invalid_key_path


def test_ordered_dict_item(tmpdir):
    subdir = tmpdir / "root/subdir1"
    subdir_path = Path(subdir)
    subdir_path.mkdir(parents=True)
    item = OrderedDictItem(str(subdir))
    assert subdir_path.exists()
    assert item.text() == "subdir1"
    assert item.key == str(subdir)

    item_non_file = OrderedDictItem("non_file_item")
    assert item_non_file.text() == "non_file_item"
    assert item_non_file.key == "non_file_item"


def test_load_model(model):
    model.update_model()
    root_item = model.invisibleRootItem()
    assert root_item.hasChildren()

    subdir1 = root_item.child(0)
    assert subdir1.text() == "/root"
    assert subdir1.child(0).text() == "/root/subdir1"
    assert subdir1.child(1).text() == "/root/subdir2"
    assert subdir1.child(2).text() == "file4: content4"


def test_update_model_directory_name(model):
    model.update_model()
    index_to_edit = model.index(0, 0)

    model.update_data(ModelUpdateType.KEY, index_to_edit, "/new_root")

    assert model.customItemFromIndex(index_to_edit).key == "/new_root"


def test_update_model_duplicate_key_name(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    subdir1 = root_item.child(0)
    subdir2 = root_item.child(1)
    assert subdir1.key == "/root/subdir1"
    assert subdir2.key == "/root/subdir2"

    with pytest.raises(DuplicateKeyError):
        model.update_data(ModelUpdateType.KEY, subdir2.index(), "/root/subdir1")


def test_update_model_value(model):
    model.update_model()
    model.current_selection = "file4"  # To be set during actual item selection
    root_index = model.index(0, 0)
    file4_index = model.index(2, 0, root_index)

    # Using QSignalSpy to spy on signals sent
    spy = QSignalSpy(model.dataChanged)

    model.itemFromIndex(file4_index).setData("file4_new")
    assert len(spy) == 1
    assert model.itemFromIndex(file4_index).data() == "file4_new"


def test_insert_model_new_kv(model):
    new_key, new_value = "test", "example"
    model.update_model()
    root_item = model.invisibleRootItem()
    assert root_item.hasChildren()

    # Using QSignalSpy to spy on signals sent
    spy = QSignalSpy(model.dataChanged)

    root = root_item.child(0)  # /root
    subdir1 = root.child(0)  # /root/subdir1
    model.insert_new_data(
        ModelCreateType.AFTER, model.indexFromItem(subdir1), new_key, new_value
    )

    assert len(spy) == 1
    assert model.customItemFromIndex(root.child(1).index()).key == new_key
    assert model.customItemFromIndex(root.child(1).index()).value == new_value
    assert model.customItemFromIndex(root.child(2).index()).key == "/root/subdir2"


def test_insert_model_new_odict(model):
    new_key = "best_friends"
    new_value = CustomOrderedDict({"1": "albert", "2": "bernard", "3": "charlie"})

    model.update_model()
    root_item = model.invisibleRootItem()
    assert root_item.hasChildren()

    # Using QSignalSpy to spy on signals sent
    spy = QSignalSpy(model.dataChanged)

    root = root_item.child(0)  # /root
    subdir1 = root.child(0)  # /root/subdir1
    model.insert_new_data(
        ModelCreateType.BEFORE, model.indexFromItem(subdir1), new_key, new_value
    )

    assert len(spy) == 1
    new_item = model.customItemFromIndex(root.child(0).index())
    assert new_item.key == "best_friends"
    assert new_item.hasChildren()
    assert new_item.rowCount() == 3
    assert new_item.child(0).value == "albert"
    assert new_item.child(1).value == "bernard"
    assert new_item.child(2).value == "charlie"


def test_insert_model_duplicate_kv(model):
    new_key = "file4"
    new_value = "file4_newvalue"

    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    file4_item = root_item.child(2)

    with pytest.raises(DuplicateKeyError):
        model.insert_new_data(
            ModelCreateType.AFTER, file4_item.index(), new_key, new_value
        )


def test_delete_model_kv(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    subdir1 = root_item.child(0)
    subdir1_index = subdir1.index()

    model.delete_data(ModelDeleteType.KEY_VALUE, subdir1_index)

    assert root_item.child(0).key != "/root/subdir1"
    assert root_item.child(0).key == "/root/subdir2"


def test_delete_model_clear_dict(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    subdir1 = root_item.child(0)
    subdir1_index = subdir1.index()

    model.delete_data(ModelDeleteType.CLEAR_DICT, subdir1_index)

    assert root_item.child(0).key == "/root/subdir1"
    assert not root_item.child(0).hasChildren()


def test_standardise_to_item(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    subdir1 = root_item.child(0)
    subdir1_index = subdir1.index()
    subdir2 = root_item.child(1)
    subdir2_index = subdir2.index()

    model.standardise_to_item(subdir2_index, subdir1_index)

    assert subdir1.rowCount() == subdir2.rowCount()
    assert subdir1.child(0).key == subdir2.child(0).key
    assert subdir2.child(0).value == subdir1.child(0).value
    assert subdir1.child(1).key == subdir2.child(1).key
    assert subdir2.child(1).value == subdir1.child(1).value


def test_standardise_all_items_missing_field_value(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    root_item = invisible_item.child(0)
    subdir2 = root_item.child(1)
    template_item = subdir2.child(0)
    template_item_index = template_item.index()

    with pytest.raises(ValueError):
        model.standardise_all_items(template_item_index)


def test_standardise_all_items_valid(model):
    model.update_model()
    invisible_item = model.invisibleRootItem()
    standardise_item = invisible_item.child(1)
    subdir1 = standardise_item.child(0)
    subdir2 = standardise_item.child(1)
    subdir3 = standardise_item.child(2)
    template_item = subdir1.child(1)
    target_item_subdir2 = subdir2.child(1)
    target_item_subdir3 = subdir3.child(0)

    model.standardise_all_items(template_item.index())

    assert (
        template_item.rowCount()
        == target_item_subdir2.rowCount()
        == target_item_subdir3.rowCount()
    )

    template_entry = template_item.child(0)
    target_item_subdir2_entry = target_item_subdir2.child(0)
    target_item_subdir3_entry = target_item_subdir3.child(0)

    assert (
        template_entry.key
        == target_item_subdir2_entry.key
        == target_item_subdir3_entry.key
    )
    assert target_item_subdir2_entry.value != template_entry.value
    assert target_item_subdir3_entry.value == template_entry.value
