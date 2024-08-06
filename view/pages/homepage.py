from PyQt6.QtCore import QPoint, QSettings, QSize, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFrame,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from controller.commands.command_handler import CommandHandler
from controller.crud_manager import CRUDManager
from controller.directory_tree_controller import DirectoryTreeController
from controller.form_controller import FieldEditorController
from env_var.environment import EnvironmentVariables
from model.database import Database
from model.model import OrderedDictModel
from util.constants import CaseDirMode
from view.components.directory_tree import DirectoryTree
from view.components.form import FieldEditor
from view.pages.setup_wizard import SetupMode, SetupWizard


class MainWindow(QMainWindow):
    """The main window which contains the interactive elements of FoamGUI."""

    def __init__(self, env_var: EnvironmentVariables) -> None:
        super().__init__()
        self.env_var = env_var

        # initialize window settings
        self.setWindowTitle("FoamGUI")
        self.read_settings()

        self.setup_wizard = SetupWizard(self.handle_setup_complete, self.env_var, self)
        self.setup_wizard.show()

        # initialize tool bar
        self.menu_bar = self.menuBar()

        self.file_menu = QMenu("File", self)
        self.new_case_action = QAction("New case...", self)
        self.new_case_action.triggered.connect(self.on_new_case)
        self.open_case_action = QAction("Open case...")
        self.open_case_action.triggered.connect(self.on_open_case)
        self.file_menu.addAction(self.new_case_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.open_case_action)

        self.edit_menu = QMenu("Edit", self)
        self.undo_action = QAction("Undo", self)
        self.undo_action.triggered.connect(self.on_undo)
        self.redo_action = QAction("Redo", self)
        self.redo_action.triggered.connect(self.on_redo)
        self.edit_menu.addActions([self.undo_action, self.redo_action])

        self.view_menu = QMenu("View", self)
        self.fullscreen_action = QAction("Fullscreen")
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.toggled.connect(self.toggle_fullscreen)
        self.view_menu.addAction(self.fullscreen_action)

        self.help_menu = QMenu("Help", self)
        self.documentation_action = QAction("Go to documentation...", self)
        self.help_menu.addAction(self.documentation_action)

        # add action menus
        if self.menu_bar:
            self.menu_bar.addMenu(self.file_menu)
            self.menu_bar.addMenu(self.edit_menu)
            self.menu_bar.addMenu(self.view_menu)
            self.menu_bar.addMenu(self.help_menu)

        # status bar for the homepage
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)

        # upon change in case directory, refresh main window
        self.env_var.caseDirectoryChanged.connect(lambda: self.initUI)

    def initUI(self):
        self.central_widget = QWidget(self)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # initialise database
        self.database = Database(self.env_var)
        self.database.initialise_from_case(self.env_var.get_case_directory())

        # initialise item model
        self.model = OrderedDictModel(self.database, self)

        # initialise manager for operations
        self.crud_manager = CRUDManager(self)

        # initialise command handler
        self.command_handler = CommandHandler()

        # load database into model
        self.model.load_model(self.database.get_dict(), self.model.invisibleRootItem())
        self.database.database_updated.connect(self.model.update_model)

        # Create case files browser widget
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Adjust the ratios to place the splitter in the middle
        self.splitter.setSizes([self.width() // 2, self.width() // 2])

        # Directory tree view on the left
        self.directory_tree = DirectoryTree(
            self.model,
            self,
        )
        self.directory_tree_controller = DirectoryTreeController(
            self.directory_tree,
            self.model,
            self.env_var,
            self.crud_manager,
            self.command_handler,
            self,
        )
        self.directory_tree.setFrameStyle(
            QFrame.Shape.StyledPanel | QFrame.Shadow.Plain
        )
        self.directory_tree.setStyleSheet("QTreeView { border: 1px solid gray; }")
        self.splitter.addWidget(self.directory_tree)

        # Create form view of current selection
        self.form = FieldEditor(self.model, self)
        self.form.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.form.setStyleSheet(
            "QScrollArea, FieldEditor, InformationDisplay { border: 1px solid gray; }"
        )
        self.form_controller = FieldEditorController(
            self.model, self.form, self.crud_manager, self.command_handler
        )
        self.splitter.addWidget(self.form)

        # Add slots to signals
        self.directory_tree_controller.tree_selection_changed.connect(
            self.form_controller.handle_selection_change
        )
        self.directory_tree_controller.operation_completed.connect(
            self.show_status_message
        )
        self.form_controller.operation_completed.connect(self.show_status_message)
        self.form_controller.jump_to_item.connect(
            self.directory_tree_controller.jump_to_item
        )

        # Set widgets to be non-collapsible
        for index in range(self.splitter.count()):
            self.splitter.setCollapsible(index, False)

        # actions
        self.add_file_btn = QAction("Add File", self)
        self.add_file_btn.setStatusTip("Add a file in the current folder.")
        self.add_field_btn = QAction("Add Field", self)
        self.add_field_btn.setStatusTip("Add field at the specified location.")
        self.remove_file_btn = QAction("Remove File", self)
        self.remove_file_btn.setStatusTip(
            "Removes the selected file from the current folder."
        )
        self.remove_field_btn = QAction("Remove Field", self)
        self.remove_field_btn.setStatusTip("Remove field at the specified location.")

        self.main_layout.addWidget(self.splitter)
        self.setCentralWidget(self.central_widget)

    def closeEvent(self, event):
        close = QMessageBox(self)
        close.setWindowTitle("Quit FoamGUI")
        close.setText("Are you sure you want to exit?")
        close.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        close = close.exec()

        if close == QMessageBox.StandardButton.Yes:
            self.write_settings()
            event.accept()
        else:
            event.ignore()

    def toggle_fullscreen(self, checked: bool):
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()

    def show_status_message(self, message: str):
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage(message)
        else:
            print("Status bar is not initialized.")

    def write_settings(self):
        settings = QSettings("DSO", "FoamGUI")
        settings.beginGroup("MainWindow")
        settings.setValue("size", self.size())
        settings.setValue("position", self.pos())
        settings.setValue("homedir", self.env_var.get_home_directory())
        settings.endGroup()

    def read_settings(self):
        settings = QSettings("DSO", "FoamGUI")
        settings.beginGroup("MainWindow")
        self.resize(settings.value("size", QSize(400, 400)))
        self.move(settings.value("position", QPoint(200, 200)))
        settings.endGroup()

    def on_new_case(self):
        self.env_var.set_case_dir_mode(CaseDirMode.NEW)
        self.setup_wizard.set_sequence(SetupMode.CASE)
        self.setup_wizard.show()

    def on_open_case(self):
        self.env_var.set_case_dir_mode(CaseDirMode.EXISTING)
        self.setup_wizard.set_sequence(SetupMode.CASE)
        self.setup_wizard.show()

    def on_undo(self):
        success_message = self.command_handler.undo_latest()
        if success_message:
            self.show_status_message(success_message)

    def on_redo(self):
        success_message = self.command_handler.redo_latest()
        if success_message:
            self.show_status_message(success_message)

    def handle_setup_complete(self):
        self.setup_wizard.hide()
        self.initUI()
        self.show()
