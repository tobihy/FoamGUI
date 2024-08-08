from typing import Callable, Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from env_var.environment import EnvironmentVariables
from util.file_manager import create_subdirectories
from view.pages.start.page import Page


class TemplateChoicePage(Page):

    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent: Union[QWidget, None] = None,
    ) -> None:
        super().__init__(env_var, stacked_widget, callback, parent)

        template_choice_layout = QVBoxLayout()
        self.setLayout(template_choice_layout)

        description = QLabel("I want to...", self)
        brand_new_btn = QRadioButton("Create a new case from scratch")
        brand_new_btn.setChecked(True)
        template_btn = QRadioButton("Start from an existing template")

        prev_btn = QPushButton("Previous", self)
        prev_btn.pressed.connect(self.go_prev_page)
        next_btn = QPushButton("Next", self)
        next_btn.pressed.connect(lambda: self.go_next_page(template_btn.isChecked()))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(prev_btn)
        btn_layout.addWidget(next_btn)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        template_choice_layout.addWidget(description)
        template_choice_layout.addWidget(brand_new_btn)
        template_choice_layout.addWidget(template_btn)
        template_choice_layout.addLayout(btn_layout)

    def go_prev_page(self):
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() - 1)

    def go_next_page(self, is_template: bool):
        if is_template:
            self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() + 1)
        else:
            case_dir = self.env_var.get_case_directory()
            create_subdirectories(case_dir)
            self.callback()
