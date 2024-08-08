import os
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox

from env_var.environment import EnvironmentVariables
from util.exceptions import MissingDirectoryError, UnexpectedDirError
from util.file_manager import validate_existing_case, validate_new_case
from view.pages.start.case_dir_page import CaseDirPage


class MockEnvironmentVariables(EnvironmentVariables):
    def __init__(self):
        super().__init__()
        self.home_directory = "/test_home_directory"
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
def test_dir(tmp_path):
    yield tmp_path / "existing"


@pytest.fixture
def case_dir_page(app, environment_variables):
    stacked_widget = MagicMock()
    callback = MagicMock()
    page = CaseDirPage(environment_variables, stacked_widget, callback)
    yield page
    page.setParent(None)


@pytest.fixture
def mock_msg():
    mock_msg_box = MagicMock()
    mock_msg_box.question.return_value = QMessageBox.StandardButton.Yes


def test_validate_home_dir_as_case_dir(
    app, case_dir_page: CaseDirPage, environment_variables: MockEnvironmentVariables
):
    with pytest.raises(UnexpectedDirError):
        path = environment_variables.get_home_directory()
        result = validate_new_case(path, environment_variables.get_home_directory())


def test_validate_parent_dir_as_case_dir(
    app, case_dir_page: CaseDirPage, environment_variables: MockEnvironmentVariables
):
    with pytest.raises(UnexpectedDirError):
        path = environment_variables.get_home_directory()
        temp = os.path.dirname(path)
        result = validate_new_case(temp, environment_variables.get_home_directory())


def test_validate_existing_case_name_as_new_case_name(
    test_dir,
    app,
    case_dir_page: CaseDirPage,
    environment_variables: MockEnvironmentVariables,
):
    with pytest.raises(Exception):
        test_dir.mkdir()
        result = validate_new_case(test_dir, environment_variables.get_home_directory())


def test_validate_existing_case_with_content(
    test_dir,
    app,
    case_dir_page: CaseDirPage,
    environment_variables: MockEnvironmentVariables,
):
    test_dir.mkdir()
    for d in ["0", "system", "constant"]:
        p = test_dir / d
        p.mkdir()
    result = validate_existing_case(test_dir)
    assert result


def test_validate_existing_case_missing_subdirs(
    test_dir,
    app,
    case_dir_page: CaseDirPage,
    environment_variables: MockEnvironmentVariables,
):
    with pytest.raises(MissingDirectoryError):
        test_dir.mkdir()
        result = validate_existing_case(test_dir)
