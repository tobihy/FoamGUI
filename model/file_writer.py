import os
import shutil
from pathlib import Path


class FileWriter:
    @staticmethod
    def create_directory(path: Path):
        os.makedirs(path)

    @staticmethod
    def copy_directory(src: Path, dest: Path):
        shutil.copytree(src, dest)
