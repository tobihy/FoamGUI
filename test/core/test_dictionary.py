import pytest

from model.core.dictionary import Dictionary
from model.core.element import Element, FieldElement
from util.exceptions import DictionaryError


@pytest.fixture
def dictionary():
    return Dictionary("test_dict")


@pytest.fixture
def element1():
    return FieldElement("name1", "value1")


@pytest.fixture
def element2():
    return FieldElement("name2", "value2")


def test_initialisation(dictionary):
    assert dictionary.name == "test_dict"
    assert dictionary.header["version"] == "2.0"
    assert dictionary.header["format"] == "ascii"
    assert dictionary.header["class"] == ""
    assert dictionary.header["object"] == ""
    assert len(dictionary.data) == 0


def test_set_class(dictionary):
    dictionary.set_class("test_class")
    assert dictionary.header["class"] == "test_class"


def test_set_object(dictionary):
    dictionary.set_object("test_object")
    assert dictionary.header["object"] == "test_object"


def test_put_and_get(dictionary, element1):
    dictionary.put("k1", element1)
    assert dictionary.get("k1") == element1


def test_update(dictionary, element1, element2):
    dictionary.put("k1", element1)
    dictionary.update("k1", element2)
    assert dictionary.get("k1") == element2


def test_remove(dictionary, element1):
    dictionary.put("key1", element1)
    removed_element = dictionary.remove("key1")
    assert removed_element == element1
    with pytest.raises(DictionaryError):
        dictionary.get("key1")


def test_put_duplicate_key(dictionary, element1, element2):
    dictionary.put("key1", element1)
    with pytest.raises(DictionaryError):
        dictionary.put("key1", element2)


def test_update_non_existing_key(dictionary, element1):
    with pytest.raises(DictionaryError):
        dictionary.update("non_existing_key", element1)


def test_get_non_existing_key(dictionary):
    with pytest.raises(DictionaryError):
        dictionary.get("non_existing_key")


def test_remove_non_existing_key(dictionary):
    with pytest.raises(DictionaryError):
        dictionary.remove("non_existing_key")
