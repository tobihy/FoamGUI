import sys

from PyQt6.QtCore import QModelIndex, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QStyle,
    QStyledItemDelegate,
    QWidget,
)

from model.model import ComboBoxModel
from util.constants import TAB

ROLE_ITEM_TYPE = Qt.ItemDataRole.UserRole + 1
TYPE_PARENT = 1
TYPE_CHILD = 2


class ComboBoxItemDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def paint(self, painter: QPainter, option, index: QModelIndex):
        # Initialize the style option
        self.initStyleOption(option, index)

        # Check the item type using the custom role
        item_type = index.data(ROLE_ITEM_TYPE)

        # Get the original text from the model
        text = option.text

        # Add four white spaces to the beginning of the text for child items
        if (item_type == TYPE_CHILD) and text:
            option.text = TAB + text

        # Prepare the style option for drawing text
        option.font.setBold(item_type == TYPE_PARENT)

        # Draw the custom text
        style = QApplication.style()
        if style:
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)


class CustomComboBox(QComboBox):
    focus_out_event = pyqtSignal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.delegate = ComboBoxItemDelegate(self)
        self.setItemDelegate(self.delegate)

        # Set the background color to transparent; solves bug
        # See issue at https://bugreports.qt.io/browse/QTBUG-123722?gerritIssueType=IssueOnly
        self.setStyleSheet(
            "QComboBox QAbstractItemView {background-color: transparent}"
        )

    def set_data(self, model: ComboBoxModel):
        self.setModel(model)

    def set_current_choice(self, current_choice: str):
        self.setCurrentText(current_choice)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_out_event.emit()
