import os
from enum import Enum, auto
from os.path import expanduser
from typing import Callable

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QLabel, QMainWindow, QMessageBox, QStackedWidget, QWidget

from env.environment import EnvironmentVariables
from util.exceptions import DirectoryNotFoundError, UnexpectedDirError
from view.pages.start.case_choice_page import CaseChoicePage
from view.pages.start.case_dir_page import CaseDirPage
from view.pages.start.home_dir_page import HomeDirPage
from view.pages.start.page import Page
from view.pages.start.template_choice_page import TemplateChoicePage
from view.pages.start.template_dir_page import TemplateDirPage
from view.pages.start.welcome_page import WelcomePage


class SetupMode(Enum):
    NEW_USER = auto()
    EXISTING_USER = auto()
    CASE = auto()


class SetupWizard(QMainWindow):
    def __init__(
        self, callback: Callable, env_var: EnvironmentVariables, parent=None
    ) -> None:
        super().__init__(parent)
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)
        self.env_var = env_var
        self.callback = callback
        self.initUI()

    def validate_home_dir(self, home_dir: str):
        if home_dir == expanduser("~"):
            raise UnexpectedDirError(
                f"The system's home directory cannot be FoamGUI's home directory.\nPlease create a subdirectory under your system's home directory.",
                home_dir,
            )
        if not os.path.exists(home_dir):
            raise DirectoryNotFoundError(
                f"The current specified home directory cannot be found.\nPlease provide a new home directory.",
            )
        return True

    def initUI(self):
        self.setWindowTitle("Welcome to FoamGUI")
        self.settings = QSettings("DSO", "FoamGUI")
        home_dir = self.settings.value("homedir", "", type=str)
        self.env_var.set_home_directory(home_dir)
        self.case_dir = ""

        # flow of pages
        self.welcome_page = lambda stacked_widget: WelcomePage(
            self.env_var, stacked_widget, self.go_next_page, self
        )
        self.home_dir_page = lambda stacked_widget: HomeDirPage(
            self.env_var, stacked_widget, self.go_next_page
        )
        self.case_choice_page = lambda stacked_widget: CaseChoicePage(
            self.env_var, stacked_widget, self.go_next_page, self
        )
        self.case_dir_page = lambda stacked_widget: CaseDirPage(
            self.env_var, stacked_widget, self.exit_hero_flow, self
        )
        self.template_choice_page = lambda stacked_widget: TemplateChoicePage(
            self.env_var, stacked_widget, self.exit_hero_flow, self
        )
        self.template_dir_page = lambda stacked_widget: TemplateDirPage(
            self.env_var, stacked_widget, self.exit_hero_flow, self
        )

        # set up page sequences
        self.page_sequences = {
            SetupMode.NEW_USER: [
                self.welcome_page,
                self.home_dir_page,
                self.case_choice_page,
                self.case_dir_page,
                self.template_choice_page,
                self.template_dir_page,
            ],
            SetupMode.EXISTING_USER: [
                self.case_choice_page,
                self.case_dir_page,
                self.template_choice_page,
                self.template_dir_page,
            ],
            SetupMode.CASE: [
                self.case_dir_page,
                self.template_choice_page,
                self.template_dir_page,
            ],
        }

        # get home dir
        home_dir = self.env_var.get_home_directory()
        if not home_dir:
            self.set_sequence(SetupMode.NEW_USER)
            return

        try:
            if self.validate_home_dir(home_dir):  # home directory is valid
                self.set_sequence(SetupMode.EXISTING_USER)
                return
        except (UnexpectedDirError, DirectoryNotFoundError) as e:
            reply = QMessageBox.critical(
                self, "Error", e.message, QMessageBox.StandardButton.Ok
            )
            if reply == QMessageBox.StandardButton.Ok:
                self.settings.setValue("homedir", "")
                self.env_var.set_home_directory("")
                self.set_sequence(SetupMode.NEW_USER)

    def go_prev_page(self):
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() - 1)

    def go_next_page(self):
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() + 1)

    def set_sequence(self, mode: SetupMode):
        sequence = self.page_sequences[mode]
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        for page_constructor in sequence:
            page_instance = page_constructor(self.stacked_widget)
            self.stacked_widget.addWidget(page_instance)

        self.stacked_widget.setCurrentIndex(0)

    def exit_hero_flow(self):
        self.hide()
        self.callback()
