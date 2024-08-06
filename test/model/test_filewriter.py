import os
from pathlib import Path

import pytest

from model.file_writer import FileWriter


def test_create_directory_valid(tmpdir):
    subdir = tmpdir / "subdir"
    FileWriter.create_directory(subdir)
    assert subdir.exists()


def test_create_directory_existing_dir(tmpdir):
    existing_dir = tmpdir / "existing_dir"
    os.makedirs(existing_dir)
    with pytest.raises(FileExistsError):
        FileWriter.create_directory(existing_dir)


def test_copy_directory_valid(tmpdir):
    src_dir = tmpdir / "src_dir"
    os.makedirs(src_dir)
    existing_file = src_dir / "existing_file"
    Path(existing_file).touch()

    dest_dir = tmpdir / "dest_dir"
    FileWriter.copy_directory(src_dir, dest_dir)
    assert dest_dir.exists()
    target_file = dest_dir / "existing_file"
    assert target_file.isfile()
