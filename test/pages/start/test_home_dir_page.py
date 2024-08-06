import os
from os.path import expanduser
from unittest.mock import MagicMock

import pytest
from PyQt6.QtWidgets import QApplication

from env.environment import EnvironmentVariables
from util.exceptions import DirectoryExistsError, UnexpectedDirError
from view.pages.setup_wizard import HomeDirPage


class MockEnvironmentVariables(EnvironmentVariables):
    def __init__(self):
        super().__init__()
        self.home_directory = ""
        self.case_directory = ""

    def get_home_directory(self):
        return self.home_directory

    def set_case_directory(self, path):
        self.case_directory = path


@pytest.fixture
def app():
    app = QApplication([])
    yield app
    app.exit()


@pytest.fixture
def environment_variables():
    yield MockEnvironmentVariables()


@pytest.fixture
def stacked_widget():
    yield MagicMock()


@pytest.fixture
def callback():
    yield MagicMock()


@pytest.fixture
def test_dir(tmp_path):
    yield tmp_path / "new_home_dir"


@pytest.fixture
def home_dir_page(app, environment_variables, stacked_widget, callback):
    page = HomeDirPage(environment_variables, stacked_widget, callback)
    yield page
    page.setParent(None)


def test_validate_new_homedir(
    app: QApplication,
    home_dir_page: HomeDirPage,
    test_dir: str,
):
    assert home_dir_page.validate_dir_path(test_dir)


def test_validate_system_home_homedir(
    app: QApplication,
    home_dir_page: HomeDirPage,
):
    with pytest.raises(UnexpectedDirError):
        home_dir_page.validate_dir_path(expanduser("~"))


def test_validate_existing_home_homedir(app, home_dir_page, test_dir):
    with pytest.raises(DirectoryExistsError):
        os.makedirs(test_dir)
        home_dir_page.validate_dir_path(test_dir)


def test_validate_home_dir_success(app, home_dir_page, test_dir):
    assert home_dir_page.validate_dir_path(test_dir)
