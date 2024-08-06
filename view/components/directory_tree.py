from PyQt6.QtCore import QModelIndex, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QContextMenuEvent, QStandardItem
from PyQt6.QtWidgets import QMenu, QTreeView

from model.model import DictionaryEntryItem, OrderedDictItem, OrderedDictModel
from util.constants import DictMenuFlag, ODictType


class DirectoryTree(QTreeView):
    """
    A widget that displays a directory tree based on a given model.

    This class provides a graphical tree view of a directory structure, which is
    dynamically updated when the case directory changes. It uses a QTreeView to
    present the data from a QAbstractItemModel.

    Attributes:
        tree_view (QTreeView): The tree view widget that displays the directory structure.
        env_var (EnvironmentVariables): An instance of EnvironmentVariables to listen for
                                        case directory changes.
        model (QAbstractItemModel): The model representing the directory structure.

    Methods:
        initUI():
            Initializes the user interface and connects signals.
    """

    show_field_menu = pyqtSignal(QPoint, QModelIndex)
    show_dict_menu = pyqtSignal(QPoint, DictMenuFlag, QModelIndex)

    def __init__(
        self,
        model: OrderedDictModel | None,
        parent=None,
    ):
        super().__init__(parent)
        self.dict_model = model
        self.setModel(model)
        self.initUI()

    def initUI(self):
        """
        Initializes the user interface and connects signals.

        This method sets the model for the tree view and connects the caseDirectoryChanged
        signal to refresh the UI when the case directory is updated.
        """
        # Disable column text
        header = self.header()
        if header:
            header.hide()

        # Disable editing on double-click
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # Enable double click to expand tree items
        self.setExpandsOnDoubleClick(True)

        # Set the minimum width of the directory tree
        window = self.window()
        if window:
            self.setMinimumSize(window.width() // 4, 0)

    def expand_selection(self, index: QModelIndex):
        parent_index = index.parent()
        if parent_index.isValid():
            self.expand_selection(parent_index)
        self.expand(index)

    def sizeHint(self) -> QSize:
        window = self.window()
        if window:
            return QSize(window.size().width() // 2, window.size().height())
        return super().sizeHint()

    def get_dict_menu_flag(self, item: QStandardItem):
        parent_item = item.parent()
        if not parent_item:
            return DictMenuFlag.SUB_DIR

        grandparent_item = parent_item.parent()
        if not grandparent_item:
            return DictMenuFlag.FILE

        parent_type = parent_item.data(OrderedDictItem.ROLE_TYPE)
        grandparent_type = grandparent_item.data(OrderedDictItem.ROLE_TYPE)

        if (
            parent_type == ODictType.FILE
            and grandparent_type == ODictType.ZERO_DIR
            and item.data(OrderedDictItem.ROLE_TYPE) == ODictType.BOUNDARY_FIELD
        ):
            return DictMenuFlag.BOUNDARY_FIELD
        else:
            return DictMenuFlag.NONE

    def contextMenuEvent(self, event: QContextMenuEvent):
        self.current_index = self.indexAt(event.pos())
        if not self.current_index.isValid():
            return

        model = self.model()
        if not isinstance(model, OrderedDictModel):
            return

        item = model.itemFromIndex(self.current_index)
        if isinstance(item, DictionaryEntryItem):
            self.show_field_menu.emit(event.globalPos(), self.current_index)
        elif isinstance(item, OrderedDictItem):
            flags = self.get_dict_menu_flag(item)
            self.show_dict_menu.emit(event.globalPos(), flags, self.current_index)
