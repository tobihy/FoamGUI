import os
from enum import Enum, auto
from typing import Callable, List, Literal

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from controller.error_handler import ErrorHandler
from env.environment import EnvironmentVariables
from util.constants import CaseDirMode
from util.exceptions import DirectoryNotFoundError, MissingDirectoryError
from util.file_manager import validate_existing_case, validate_new_case
from view.components.file_browser import FileBrowserWidget
from view.pages.start.page import Page


class CaseDirPage(Page):
    case_dir_selected = pyqtSignal()

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
        # pages in the control flow
        self.new_case_widget = FileBrowserWidget(
            "Create case directory",
            "Please create the case directory for your new case.",
            True,
            self.handle_new_case,
            self.env_var.get_home_directory(),
            self.stacked_widget,
            self,
        )

        self.existing_case_widget = FileBrowserWidget(
            "Select case directory",
            "Please choose an existing case directory to open.",
            False,
            self.handle_existing_case,
            self.env_var.get_home_directory(),
            self.stacked_widget,
            self,
        )

        # error handler
        self.error_handler = ErrorHandler()

        # case dir frame
        self.case_dir_layout = QVBoxLayout()
        self.case_dir_layout.addWidget(self.new_case_widget)
        self.case_dir_layout.addWidget(self.existing_case_widget)

        self.setLayout(self.case_dir_layout)

        # set visibilities based on current case dir mode
        self.set_initial_visibility()

        # page should change depending on whether it is a new case or existing case
        self.env_var.case_mode_selected.connect(self.change_state)

    def set_initial_visibility(self):
        curr_mode = self.env_var.get_case_dir_mode()
        if curr_mode == CaseDirMode.EXISTING:
            self.new_case_widget.hide()
            self.existing_case_widget.show()
        elif curr_mode == CaseDirMode.NEW:
            self.new_case_widget.show()
            self.existing_case_widget.hide()

    def enter_home_page(self):
        self.callback()

    def change_state(self, dir_mode: CaseDirMode):
        if dir_mode == CaseDirMode.EXISTING:
            self.new_case_widget.hide()
            self.existing_case_widget.show()
        if dir_mode == CaseDirMode.NEW:
            self.existing_case_widget.hide()
            self.new_case_widget.show()

    def handle_new_case(self, path: str):
        try:
            if validate_new_case(path, self.env_var.get_home_directory()):
                self.stacked_widget.setCurrentIndex(
                    self.stacked_widget.currentIndex() + 1
                )
                self.env_var.set_case_directory(path)
        except Exception as e:
            self.error_handler.handle_error(e)

    def handle_existing_case(self, case_dir: str):
        try:
            if validate_existing_case(case_dir):
                self.env_var.set_case_directory(case_dir)
                self.enter_home_page()
        except DirectoryNotFoundError as dne:
            # QMessageBox.warning(self, "Error", dne.message)
            self.error_handler.handle_error(dne)
        except MissingDirectoryError as me:
            reply = QMessageBox.question(
                self,
                "Error",
                me.message + "\nDo you want to recreate the missing directories?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.handle_missing_subdirectories(case_dir, me.missing_dirs)
                self.enter_home_page()

    def handle_missing_subdirectories(self, case_dir: str, missing_dirs: List[str]):
        try:
            for subdir in missing_dirs:
                path = os.path.join(case_dir, subdir)
                os.mkdir(path)
        except FileExistsError:
            QMessageBox.warning(self, "Error", f"Directory {path} already exists.")
        except OSError as e:
            # Handle other possible OSError exceptions
            self.error_handler.handle_error(e)
