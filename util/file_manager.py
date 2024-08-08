from pathlib import Path
from typing import List, Union

from model.file_writer import FileWriter
from util.exceptions import (
    DirectoryExistsError,
    DirectoryNotFoundError,
    MissingDirectoryError,
    UnexpectedDirError,
)


def validate_new_case(path: str, home_dir_path: str):
    case_dir = Path(path).name
    if path == home_dir_path:
        raise UnexpectedDirError(
            f"Directory {path} is the home directory."
            + "\n"
            + "Please create a case subdirectory.",
            path,
        )
    if home_dir_path not in path:
        raise UnexpectedDirError(
            f"Case {case_dir} must be located within your home directory.", path
        )
    if Path(path).exists():
        raise DirectoryExistsError(f"Case {case_dir} already exists.")
    return True


def validate_existing_case(path: str):
    if not Path(path).exists:
        raise DirectoryNotFoundError(
            f"Directory {path} does not exist." + "\n" + "Please try again."
        )

    missing_subdirs: List[str] = []
    for subdir in ["0", "system", "constant"]:
        subdir_path = Path(path, subdir)
        if not subdir_path.exists():
            missing_subdirs.append(str(subdir_path))
    if missing_subdirs:
        raise MissingDirectoryError(
            f"Directory has missing subdirectories:"
            + "\n"
            + "\n".join(missing_subdirs),
            missing_subdirs,
        )
    return True


def create_subdirectories(case_path: str, template_path: Union[str, None] = None):
    try:
        for dir in ["0", "system", "constant"]:
            path = Path(case_path, dir)
            if template_path:
                template_subdir = Path(template_path, dir)
                FileWriter.copy_directory(template_subdir, path)
            else:
                FileWriter.create_directory(path)
    except FileExistsError:
        raise FileExistsError(f"Directory {str(path)} already exists.")
