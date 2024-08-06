from collections import OrderedDict

from model.core.element import Element
from util.exceptions import DictionaryError


class Dictionary(Element):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.header = {"version": "2.0", "format": "ascii", "class": "", "object": ""}
        self.data = {}

    # Set/update metadata
    def set_class(self, cls: str) -> None:
        self.header["class"] = cls

    def set_object(self, obj: str) -> None:
        self.header["object"] = obj

    # Create
    def put(self, key: str, val: Element) -> None:
        if self.data.get(key):  # entry already exists
            raise DictionaryError(f"Dictionary key {key} already exists.")
        self.data[key] = val

    # Update
    def update(self, key: str, val: Element) -> None:
        if not self.data.get(key):  # key not found
            raise DictionaryError(f"Dictionary key {key} does not exist.")
        self.data[key] = val

    # Read
    def get(self, key: str) -> Element:
        if not self.data.get(key):  # key not found
            raise DictionaryError(f"Dictionary key {key} does not exist.")
        return self.data[key]

    # Delete
    def remove(self, key: str) -> Element:
        if not self.data.get(key):  # key not found
            raise DictionaryError(f"Dictionary key {key} does not exist.")
        return self.data.pop(key)
