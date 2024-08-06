from env.environment import EnvironmentVariables
from model.model import OrderedDictModel
from view.pages.homepage import MainWindow


class MainController:
    def __init__(
        self, model: OrderedDictModel, view: MainWindow, env_var: EnvironmentVariables
    ):
        self.model = model
        self.view = view
        self.env_var = env_var

    def init_connections(self):
        """Initialise all connections."""
        self.view.new_case_action.triggered.connect(self.on_new_case)

    def on_new_case(self):
        pass
