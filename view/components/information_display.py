from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class InformationDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel()
        self.label.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_information(self, text: str):
        self.label.setText(text)

    def clear_information(self):
        self.label.clear()
