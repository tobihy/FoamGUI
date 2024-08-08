from pathlib import Path
from typing import List, Tuple

from PyQt5.QtCore import QObject, pyqtSignal

from env_var.environment import EnvironmentVariables
from model.core.foamfile import FoamFile
from model.custom_ordered_dict import CustomOrderedDict


class Database(QObject):
    """
    A class to manage the database of a case directory in the FoamGUI application.

    This class is responsible for initializing and updating a dictionary representing
    the contents of a case directory. It listens for changes to the case directory and
    updates the database accordingly. The database is structured as a custom ordered
    dictionary.

    Attributes:
        database_updated (pyqtSignal): Signal emitted when the database is updated.

    Methods:
        initialise_from_case(case_dir: Path):
            Initializes the database from the given case directory.
        fill_dict_from_subdir(odict: CustomOrderedDict, path: Path):
            Recursively fills the case directory dictionary with files and subdirectories.
        get_dict() -> CustomOrderedDict:
            Returns the current state of the database.
    """

    database_updated = pyqtSignal()

    def __init__(self, env_var: EnvironmentVariables) -> None:
        super().__init__()
        self.env_var = env_var
        self.odict = CustomOrderedDict()
        self.foamfile_store = dict()

    def initialise_from_case(self, case_dir: str):
        """
        Initializes the database from the given case directory.

        This method fills the custom ordered dictionary with the contents of the case
        directory, including files and subdirectories from '0', 'system', and 'constant'
        subdirectories. Emits the database_updated signal after initialization.

        Parameters:
        -----------
            case_dir (Path): The path to the case directory.
        """
        if not Path(case_dir).exists():
            return

        for dir in map(
            lambda subdir: Path(case_dir) / subdir,
            ["0", "system", "constant"],
        ):
            self.fill_dict_from_subdir(self.odict, dir)
        self.database_updated.emit()

    def fill_dict_from_subdir(self, odict: CustomOrderedDict, path: Path):
        """
        Recursively fills the case directory dictionary with files and subdirectories.

        This method reads FoamFile instances from the given directory path and adds them
        to the custom ordered dictionary. If a subdirectory is encountered, the method
        calls itself recursively to process the subdirectory's contents.

        Parameters:
        -----------
            odict (CustomOrderedDict): The dictionary to be filled with directory contents.
            path (Path): The path to the current directory.
        """
        if not Path(path).exists():
            return

        subdir_dict = CustomOrderedDict()
        odict[str(path)] = subdir_dict
        for p in path.iterdir():
            if p.is_file():
                foamfile = FoamFile(p)
                self.foamfile_store[str(p)] = foamfile

                foamdict = foamfile.read()
                subdir_dict[str(p)] = foamdict
            elif p.is_dir():
                self.fill_dict_from_subdir(subdir_dict, p)

    def get_dict(self):
        return self.odict

    def get_foamfile(self, key_path: List[str]) -> FoamFile:
        file_path, file_key_seq = self.get_file_path(key_path)
        return self.foamfile_store[str(file_path)]

    def get_file_path(self, key_path: List[str]) -> Tuple[str, List[str]]:
        """
        Given a key path, traverses through the key path until we reach the first non-file key.

        Returns:
        --------
        1. The first return value will be the path of the foamfile odict we require.
        2. The second return value represents the sequence of keys leading to the file's odict.
        """
        res, seq = "", []
        for k in key_path:
            if not Path(k).exists():
                break
            res = k
            seq.append(k)
        return res, seq

    def update_file(self, key_path: List[str]):
        path, edited_file_seq = self.get_file_path(key_path)
        foamfile: FoamFile = self.foamfile_store[str(path)]
        content_to_write = self.odict.get_nested_value(edited_file_seq)
        foamfile.write(content_to_write)

    def delete_file(self, path_str: str):
        """
        Deletes a file at the specified path.

        This method deletes a file located at the given path. If the file does not exist, it raises
        a `FileNotFoundError`.

        Parameters:
        path_str (str): The path to the file to be deleted. It should be a string representing the file path.

        Raises:
        FileNotFoundError: If the file does not exist at the specified path.
        """
        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(f"The file at {path_str} does not exist.")

        path.unlink()

    def create_file(
        self,
        parent_path_str: str,
        path_str: str,
        foam_class: str,
        content: CustomOrderedDict = CustomOrderedDict(),
    ):
        """
        Creates a new file in the current case directory.

        The new file will reside in the parent path directory provided.

        Parameters:
        -----------
            parent_path_str (str): The path string to contain the new file created.
            path_str (str): The path string to the new file created.
            foam_class (str): The class of the OpenFOAM input file created.

        Raises:
        -------
            FileExistsError: If the provided file name already exists in the parent directory.
        """
        path = Path(path_str)
        if path.exists():
            raise FileExistsError(f"The file '{path.name}' already exists.")

        with FoamFile(path_str, mode="w", foam_class=foam_class) as foamfile:
            foamfile.write(content)
            self.fill_dict_from_subdir(self.odict, Path(parent_path_str))
