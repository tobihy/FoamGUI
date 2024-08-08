from PyQt5.QtWidgets import QMessageBox


class ErrorHandler:
    def __init__(self) -> None:
        pass

    def handle_error(self, error: Exception):
        QMessageBox.critical(
            None,
            "Error",
            str(error),
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
        )
