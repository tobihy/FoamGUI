from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStackedWidget, QWidget

from env_var.environment import EnvironmentVariables


class Page(QWidget):
    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.env_var = env_var
        self.stacked_widget = stacked_widget
        self.callback = callback
