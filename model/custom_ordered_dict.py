from typing import Any


class CustomOrderedDict(dict):

    def __init__(self, data=None) -> None:
        super().__init__(data or {})

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CustomOrderedDict):
            return False
        return list(self.items()) == list(other.items())

    def rename_key(self, key_path: list[str], old_key: str, new_key: str):
        """
        Renames a key in a nested CustomOrderedDict.

        This method navigates to a nested CustomOrderedDict using the provided key path
        and renames a specified key within that dictionary. The nested dictionary is
        updated in place.

        Parameters:
        -----------
        key_path : list[str]
            A list of strings representing the path to the nested dictionary where the key
            renaming should take place. Each string in the list corresponds to a key in the
            hierarchy of nested dictionaries.
        old_key : str
            The key in the nested dictionary that needs to be renamed.
        new_key : str
            The new key name that will replace the old key.

        Returns:
        --------
        CustomOrderedDict
            The updated nested dictionary with the key renamed.

        Raises:
        -------
        ValueError
            If the value at the end of the key path is not a CustomOrderedDict.
        KeyError
            If the old_key is not found in the CustomOrderedDict.

        Example:
        --------
        >>> d = CustomOrderedDict({
        ...     "level1": CustomOrderedDict({
        ...         "level2": CustomOrderedDict({
        ...             "old_key": "value"
        ...         })
        ...     })
        ... })
        >>> d.rename_key(["level1", "level2"], "old_key", "new_key")
        CustomOrderedDict([('level1', CustomOrderedDict([('level2', CustomOrderedDict([('new_key', 'value')]))]))])
        """

        # Get the nested dictionary using the key_path provided
        curr = self.get_nested_value(key_path)
        if type(curr) is not CustomOrderedDict:
            raise ValueError(f"Value at key {old_key} is not a OrderedDict")
        if old_key not in curr.keys():
            raise KeyError(f"Key '{old_key}' not found in OrderedDict.")
        if old_key == new_key:
            return self  # No change needed if old_key is the same as new_key

        # Get updated dictionary with new key
        updated_dict = CustomOrderedDict(
            {new_key if k == old_key else k: v for k, v in curr.items()}
        )

        # Update existing dictionary with renamed key dictionary
        curr.clear()
        curr.update(updated_dict)
        return curr

    # O(n) insertions for new fields
    def insert(
        self,
        key_path: list[str],
        key: Any,
        value: Any,
        insert_key: str | None = None,
        after: bool = False,
    ) -> None:
        target_dict = self.get_nested_value(key_path)
        if not isinstance(target_dict, CustomOrderedDict):
            raise ValueError("Expected dictionary, got string instead.")

        keys = list(target_dict.keys())
        if not insert_key:
            insert_pos = len(
                keys
            )  # default behaviour: insert at the back of the dictionary
        else:
            insert_pos = keys.index(insert_key)
            if insert_pos < 0 or insert_pos >= len(target_dict):
                raise KeyError("Invalid index for dictionary.")

        if after:
            keys.insert(insert_pos + 1, key)
        else:
            keys.insert(insert_pos, key)

        new_dict = dict()
        for k in keys:
            new_dict[k] = target_dict.get(k, None)

        target_dict.clear()
        target_dict.update(new_dict)
        target_dict[key] = value

    def update_nested_value(
        self, key_path: list[str], key: str, new_value: "str | CustomOrderedDict"
    ):
        target_dict = self.get_nested_value(key_path)
        if not isinstance(target_dict, CustomOrderedDict):
            raise ValueError("Expected dictionary, got string instead.")
        if key not in target_dict.keys():
            raise KeyError(f"Key {key} not found in the dictionary.")
        target_dict[key] = new_value
        print(f"Dictionary updated with key:value pair {key}:{new_value}.")

    def remove(self, key_path: list[str], key: str):
        target_dict = self.get_nested_value(key_path)
        if not isinstance(target_dict, CustomOrderedDict):
            raise ValueError("Expected dictionary, got string instead.")

        target_dict.pop(key)
        print(f"Dictionary entry with key {key} deleted.")

    def remove_all(self, key_path: list[str]):
        target_dict = self.get_nested_value(key_path)
        if not isinstance(target_dict, CustomOrderedDict):
            raise ValueError("Expected dictionary, got string instead.")

        target_dict.clear()
        print(f"Dictionary entries cleared.")

    def get_nested_value(self, key_path: list[str]) -> "CustomOrderedDict | str":
        if not key_path:
            return self
        current_level, next_level = self, self
        for key in key_path:
            if key not in next_level:
                raise KeyError(f"Key {key} not found in the dictionary.")
            current_level = next_level
            next_level = current_level[key]
        return current_level[key_path[-1]]

    def map_keys_to_target_dict(self, target_dict: "CustomOrderedDict"):
        """
        Create a new dictionary with keys from the current dictionary
        and values from the target dictionary if the key exists in the target,
        or None if it does not exist in the target.

        Parameters:
        - example_dict: Dictionary containing the keys to map.
        - target_dict: Dictionary containing the values to map to.

        Returns:
        A new dictionary with the same keys as the example dictionary,
        and values from the target dictionary or None.
        """
        if not len(self):
            return CustomOrderedDict()

        return CustomOrderedDict(
            {key: target_dict.get(key, self.get(key)) for key in self.keys()}
        )
