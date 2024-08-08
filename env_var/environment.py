from PyQt5.QtCore import QObject, QSettings, pyqtSignal

from util.constants import CaseDirMode


class EnvironmentVariables(QObject):
    """
    A class to manage environment variables for the FoamGUI application.

    This class handles the storage and retrieval of the home and case directories,
    as well as emitting signals when these directories are changed. It uses QSettings
    to persist the home directory across sessions.

    Attributes:
        homeDirectoryChanged (pyqtSignal): Signal emitted when the home directory is changed.
        caseDirectoryChanged (pyqtSignal): Signal emitted when the case directory is changed.
        case_mode_selected (pyqtSignal): Signal emitted when the case directory mode is selected.

    Methods:
        get_home_directory() -> str:
            Returns the current home directory.
        get_case_directory() -> str:
            Returns the current case directory.
        set_home_directory(dir_path: str):
            Sets a new home directory and emits the homeDirectoryChanged signal.
        set_case_directory(dir_path: str):
            Sets a new case directory and emits the caseDirectoryChanged signal.
        set_case_dir_mode(case_dir_mode: CaseDirMode):
            Sets the case directory mode and emits the case_mode_selected signal.
    """

    homeDirectoryChanged = pyqtSignal(str)
    caseDirectoryChanged = pyqtSignal(str)
    case_mode_selected = pyqtSignal(CaseDirMode)

    def __init__(self, parent=None) -> None:
        """
        Initializes the EnvironmentVariables instance.

        Args:
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self.settings = QSettings("DSO", "FoamGUI")
        self._home_directory = self.settings.value("homedir", "", str)
        self._case_directory = ""
        self._case_dir_mode = None

    def get_home_directory(self):
        """
        Returns the current home directory.

        Returns:
            str: The path to the home directory.
        """
        return self._home_directory

    def get_case_directory(self):
        """
        Returns the current case directory.

        Returns:
            str: The path to the cases directory.
        """
        return self._case_directory

    def get_case_dir_mode(self):
        return self._case_dir_mode

    def set_home_directory(self, dir_path: str):
        """
        Sets a new home directory and emits the homeDirectoryChanged signal if the directory is changed.

        Args:
            dir_path (str): The new home directory path.
        """
        if self._home_directory != dir_path:
            self._home_directory = dir_path
            self.settings.setValue("homedir", dir_path)
            self.homeDirectoryChanged.emit(dir_path)

    def set_case_directory(self, dir_path: str):
        """
        Sets a new case directory and emits the caseDirectoryChanged signal if the directory is changed.

        Args:
            dir_path (str): The new case directory path.
        """
        if self._case_directory != dir_path:
            self._case_directory = dir_path
            self.caseDirectoryChanged.emit(dir_path)

    def set_case_dir_mode(self, case_dir_mode: CaseDirMode):
        """
        Sets the case directory mode and emits the case_mode_selected signal.

        Args:
            case_dir_mode (CaseDirMode): The mode of the case directory, either 'new' or 'existing'.
        """
        self._case_dir_mode = case_dir_mode
        self.case_mode_selected.emit(case_dir_mode)
