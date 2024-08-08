import os
from os.path import expanduser
from pathlib import Path
from typing import Callable

from PyQt5.QtCore import QSettings, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QStackedWidget, QVBoxLayout

from env_var.environment import EnvironmentVariables
from model.file_writer import FileWriter
from util.exceptions import DirectoryExistsError, UnexpectedDirError
from view.components.file_browser import FileBrowserWidget
from view.pages.start.page import Page


class HomeDirPage(Page):
    home_dir_created = pyqtSignal()

    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent=None,
    ) -> None:
        super().__init__(env_var, stacked_widget, callback, parent)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.fb = FileBrowserWidget(
            "Select home directory",
            "Please create the home directory for OpenFOAM files.",
            True,
            self.handle_set_home_dir,
            None,
            self.stacked_widget,
            self,
        )
        main_layout.addWidget(self.fb)
        self.setLayout(main_layout)

    def validate_dir_path(self, home_dir: str):
        if home_dir == expanduser("~"):
            raise UnexpectedDirError(
                f"The system's home directory cannot be FoamGUI's home directory.\nPlease create a subdirectory under your system's home directory.",
                home_dir,
            )
        if os.path.exists(home_dir):
            raise DirectoryExistsError(
                f"Directory already exists.\nPlease provide an alternate directory name."
            )
        return True

    def handle_set_home_dir(self, home_dir: str):
        try:
            if self.validate_dir_path(home_dir):
                self.env_var.set_home_directory(home_dir)
                settings = QSettings("DSO", "FoamGUI")
                settings.setValue("homedir", home_dir)
                FileWriter.create_directory(Path(home_dir))
                self.callback()
        except (UnexpectedDirError, DirectoryExistsError) as e:
            QMessageBox.warning(self, "Error", e.message)
        except OSError as e:
            # Handle other possible OSError exceptions
            QMessageBox.critical(self, "Critical Error", f"An error occurred:\n{e}")
