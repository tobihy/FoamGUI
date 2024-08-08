from typing import Callable

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QStackedWidget, QVBoxLayout

from env_var.environment import EnvironmentVariables
from view.pages.start.page import Page


class WelcomePage(Page):
    welcome_completed = pyqtSignal()

    def __init__(
        self,
        env_var: EnvironmentVariables,
        stacked_widget: QStackedWidget,
        callback: Callable,
        parent=None,
    ):
        super().__init__(env_var, stacked_widget, callback, parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.welcome = QLabel(self)
        self.welcome.setText(
            "Welcome to FoamGUI, your handy GUI for the creation of OpenFOAM input files.\nTo start, set the home directory for FoamGUI."
        )
        self.welcome_btn = QPushButton(self)
        self.welcome_btn.setText("Begin")
        self.welcome_btn.pressed.connect(self.next_page)
        layout.addWidget(self.welcome)
        layout.addWidget(self.welcome_btn)
        self.setLayout(layout)

    def next_page(self):
        self.setVisible(False)
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() + 1)
