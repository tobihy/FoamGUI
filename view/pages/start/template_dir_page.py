from typing import Callable

from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from controller.error_handler import ErrorHandler
from env.environment import EnvironmentVariables
from util.file_manager import create_subdirectories, validate_existing_case
from view.components.file_browser import FileBrowserWidget
from view.pages.start.page import Page


class TemplateDirPage(Page):
    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(env_var, stacked_widget, callback, parent)
        self.env_var.caseDirectoryChanged.connect(self.update_target_path)
        self.initUI()

    def initUI(self):
        self.error_handler = ErrorHandler()
        self.template_widget = FileBrowserWidget(
            "Choose template",
            "Please select the template directory you wish to use.",
            False,
            self.handle_create_from_template,
            self.env_var.get_home_directory(),
            self.stacked_widget,
            self,
        )

        self.template_dir_layout = QVBoxLayout()
        self.template_dir_layout.addWidget(self.template_widget)
        self.setLayout(self.template_dir_layout)

    def handle_create_from_template(self, template_path: str):
        try:
            if validate_existing_case(template_path):
                create_subdirectories(self.target_path, template_path)
                self.callback()

        except Exception as e:
            self.error_handler.handle_error(e)

    def update_target_path(self, updated_path: str):
        self.target_path = updated_path
