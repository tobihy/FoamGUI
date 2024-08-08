from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout

class InformationDisplay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.label = QLabel()
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_information(self, text: str):
        self.label.setText(text)

    def clear_information(self):
        self.label.clear()
