from typing import List

from PyQt5.QtCore import QModelIndex


class DictionaryError(Exception):
    """Raised when an error related to dictionary CRUD occurs"""

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


class DirectoryExistsError(FileExistsError):
    """Raised when an existing directory is provided as an empty directory"""

    def __init__(self, message, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


class DirectoryNotFoundError(FileNotFoundError):
    """Raised when a directory cannot be found"""

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


class MissingDirectoryError(FileNotFoundError):
    """Raised when any directory or directories are missing"""

    def __init__(self, message: str, missing_dirs: List[str], *args: object) -> None:
        self.message = message
        self.missing_dirs = missing_dirs
        super().__init__(message, *args)


class UnexpectedDirError(ValueError):
    """Raised when the path specified is invalid"""

    def __init__(self, message: str, path: str, *args: object) -> None:
        self.message = message
        self.path = path
        super().__init__(message, *args)


class InvalidModelIndexError(Exception):
    """Exception raised when an invalid model index is encountered."""

    def __init__(self, index: QModelIndex):
        self.message = f"Item not found for invalid index {index}"
        super().__init__(self.message)


class InvalidModelOperationError(Exception):
    """
    Exception raised for invalid operations performed on a model.
    """

    def __init__(self, item, message="Invalid operation done on item") -> None:
        self.message = f"{message}: {item}"
        super().__init__(self.message)


class DuplicateKeyError(KeyError):
    """
    Exception raised when attempting to insert a duplicate key into a dictionary.

    Attributes:
        message (str): Optional error message to describe the exception.
    """

    def __init__(self, key: str, message: str = "Duplicate key found in dictionary."):
        self.key = key
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} Key: {self.key}"
