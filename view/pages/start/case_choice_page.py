from typing import Callable

from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from env.environment import EnvironmentVariables
from util.constants import CaseDirMode
from view.components.button import CustomButton
from view.pages.start.page import Page


class CaseChoicePage(Page):
    case_mode_selected = pyqtSignal(CaseDirMode)

    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent=None,
    ):
        super().__init__(env_var, stacked_widget, callback, parent)
        self.stacked_widget = stacked_widget
        self.callback = callback
        self.initUI()

    @pyqtSlot()
    def open_existing_case(self):
        self.env_var.set_case_dir_mode(CaseDirMode.EXISTING)
        self.callback()

    @pyqtSlot()
    def create_new_case(self):
        self.env_var.set_case_dir_mode(CaseDirMode.NEW)
        self.callback()

    def initUI(self):
        self.main_layout = QVBoxLayout()

        # choice frame
        self.case_choice_frame = QFrame()
        self.case_choice_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.description = QLabel(self)
        self.description.setText("I want to...")
        self.existing_btn = CustomButton(
            "Open an existing case", self.open_existing_case
        )
        self.new_btn = CustomButton("Create a new case", self.create_new_case)
        self.button_layout.addWidget(self.existing_btn)
        self.button_layout.addWidget(self.new_btn)
        self.case_choice_layout.addWidget(self.description)
        self.case_choice_layout.addLayout(self.button_layout)
        self.case_choice_frame.setLayout(self.case_choice_layout)

        # initialise layout
        self.main_layout.addWidget(self.case_choice_frame)

        # change to initial layout
        self.setLayout(self.main_layout)
