import datetime
import os
import pathlib
import sys


def create_folder(folder: str | pathlib.Path):
    if not os.path.exists(folder):
        os.makedirs(folder)


def check_if_folder_exists(path: str) -> bool:
    return os.path.isdir(path)


class Configurations:
    def __init__(self):
        self.encoding = "UTF-8"

        # logging
        self.logging = True
        self.logging_to_file = True
        self._logging_directory = None

    @property
    def logging_directory(self):
        if self._logging_directory is None:
            # grab file location where main was run
            main_file = pathlib.Path(sys.argv[0]).parent
            # create new folder 'logs'
            path = main_file / pathlib.Path("logs")
            create_folder(path)
            # create new folder with data
            self._logging_directory = path / pathlib.Path(datetime.datetime.now().strftime("log_%Y_%m_%d-%H_%M"))

        return self._logging_directory

    @logging_directory.setter
    def logging_directory(self, logging_directory: str):
        if not check_if_folder_exists(logging_directory):
            raise ValueError("'logging_directory' not found.")

        self._logging_directory = logging_directory


config = Configurations()
