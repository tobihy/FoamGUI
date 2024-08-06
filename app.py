import sys

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from env.environment import EnvironmentVariables
from view.pages.homepage import MainWindow

# Create an instance of the application
app = QApplication([])


# Create global variables
env_var = EnvironmentVariables()

# Get settings
settings = QSettings("DSO", "FoamGUI")

# Pages
main_window = MainWindow(env_var)

# Open hero page
main_window.show()

# Run your application's event loop
sys.exit(app.exec())
