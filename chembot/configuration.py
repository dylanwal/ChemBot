import datetime
import os
import pathlib
import sys
import logging


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
        self._logging_directory = None
        self.root_file = pathlib.Path(sys.argv[0])
        self.root_logger_name = self.root_file.stem
        self._setup_logger()

        # rabbitmq
        # MUST BE CHANGED BEFORE INITIALIZING DEVISES
        self.rabbit_host = 'localhost'
        self.rabbit_port = 5672
        self.rabbit_username = 'guest'
        self.rabbit_password = 'guest'
        self.rabbit_exchange = 'chembot'

    @property
    def logging_directory(self) -> str:
        if self._logging_directory is None:
            # create new folder 'logs'
            path = self.root_file.parent / pathlib.Path("logs")
            create_folder(path)
            # create new folder with reference_data
            self._logging_directory = str(path / pathlib.Path(datetime.datetime.now().strftime("log_%Y_%m_%d-%H_%M")))
            create_folder(self._logging_directory)

        return self._logging_directory

    @logging_directory.setter
    def logging_directory(self, logging_directory: str):
        if not check_if_folder_exists(logging_directory):
            raise ValueError("'logging_directory' not found.")

        self._logging_directory = logging_directory

    def _setup_logger(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=self.logging_directory + r"\\" + self.root_file.stem + '.log',
                            filemode='w',
                            encoding="UTF-8"
                            )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logging.getLogger().addHandler(console)


config = Configurations()
