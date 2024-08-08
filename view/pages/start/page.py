from typing import Callable, Union

from PyQt5.QtWidgets import QStackedWidget, QWidget

from env_var.environment import EnvironmentVariables


class Page(QWidget):
    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent: Union[QWidget, None] = None,
    ):
        super().__init__(parent)
        self.env_var = env_var
        self.stacked_widget = stacked_widget
        self.callback = callback
