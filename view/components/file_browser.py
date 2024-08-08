import os
from os.path import expanduser
from typing import Callable, Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class FileBrowserWidget(QWidget):
    def __init__(
        self,
        title: str,
        description: str,
        isWrite: bool,
        callback: Callable,
        curr_dir: Union[str, None],
        stacked_widget: QStackedWidget,
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self.is_write = isWrite
        self.callback = callback
        self.description = description
        self.curr_dir = curr_dir
        self.stacked_widget = stacked_widget
        self.initUI()

    def open_file_browser(self):
        # open a directory dialog and get a selected directory path
        self.dialog = QFileDialog()
        options = self.dialog.options()
        options |= QFileDialog.Option.DontResolveSymlinks

        selected_dir = self.dialog.getExistingDirectory(
            self, self.title, self.curr_dir, options=options
        )

        if selected_dir:
            self.path.setText(selected_dir)

    def edit_directory_name(self):
        # creates a new directory at the current chosen path
        directory = self.path.text()

        if not directory:
            QMessageBox.warning(
                self, "No directory specified", "Please select a directory."
            )
            return

        new_folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter new folder name:"
        )

        if not (ok and new_folder_name):
            return

        self.path.setText(os.path.join(directory, new_folder_name))

    def go_next_page(self):
        self.callback(self.path.text())

    def go_prev_page(self):
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() - 1)

    def update_curr_dir(self, new_dir: str):
        self.curr_dir = new_dir
        self.path.setText(new_dir)

    def initUI(self):
        if not self.curr_dir:
            self.curr_dir = expanduser("~")

        self.main_layout = QVBoxLayout()

        # instructions section
        self.description_text = QLabel(self)
        self.description_text.setText(self.description)
        self.main_layout.addWidget(self.description_text)

        # file selection section
        self.file_selector_box = QHBoxLayout()
        self.path = QLineEdit(self)
        self.path.setText(self.curr_dir)
        self.file_selector_box.addWidget(self.path)
        if self.is_write:
            self.new_dir_btn = QPushButton(self)
            self.new_dir_btn.setText("New Folder")
            self.new_dir_btn.clicked.connect(self.edit_directory_name)
            self.file_selector_box.addWidget(self.new_dir_btn)
        self.browse_btn = QPushButton(self)
        self.browse_btn.setText("Browse")
        self.browse_btn.clicked.connect(self.open_file_browser)
        self.file_selector_box.addWidget(self.browse_btn)
        self.main_layout.addLayout(self.file_selector_box)

        # navigation section
        self.navi_box = QHBoxLayout()
        self.prev_btn = QPushButton(self)
        self.prev_btn.setText("Previous")
        self.prev_btn.clicked.connect(self.go_prev_page)
        self.navi_box.addWidget(self.prev_btn)
        self.next_btn = QPushButton(self)
        self.next_btn.setText("Next")
        self.next_btn.clicked.connect(self.go_next_page)
        self.navi_box.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.navi_box.addWidget(self.next_btn)
        self.main_layout.addLayout(self.navi_box)

        self.setLayout(self.main_layout)
