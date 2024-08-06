from PyQt6.QtWidgets import QPushButton
from typing import Callable


class CustomButton(QPushButton):
    def __init__(self, text: str, callback: Callable):
        super().__init__()
        self.setText(text)
        self.clicked.connect(callback)
