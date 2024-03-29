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

        # data
        self._data_directory = None
        self.root_file = pathlib.Path(sys.argv[0])

        # logging
        self.logging = True
        self._logging_directory = None
        self.root_file = pathlib.Path(sys.argv[0])
        self.root_logger_name = self.root_file.stem
        self.logger = logging.getLogger(self.root_logger_name)
        self._setup_logger()

        # rabbitmq
        # MUST BE CHANGED BEFORE INITIALIZING DEVISES
        self.rabbit_host = '127.0.0.1'
        self.rabbit_port = 5672
        self.rabbit_port_http = 15672
        self.rabbit_username = 'guest'
        self.rabbit_password = 'guest'
        self.rabbit_exchange = 'chembot'
        self.rabbit_queue_timeout = 1  # sec
        self.rabbit_auth = (self.rabbit_username, self.rabbit_password)
        self.pickle_protocol = 5

    @property
    def data_directory(self) -> pathlib.Path:
        if self._data_directory is None:
            # create new folder 'data'
            path = self.root_file.parent / pathlib.Path("data")
            create_folder(path)
            # create new folder 'data.date'
            self._data_directory = path / pathlib.Path(datetime.datetime.now().strftime("data_%Y_%m_%d"))
            create_folder(self._data_directory)

        return self._data_directory

    @data_directory.setter
    def data_directory(self, data_directory: str):
        if not check_if_folder_exists(data_directory):
            raise ValueError("'data_directory' not found.")

        self._data_directory = data_directory

    @property
    def logging_directory(self) -> pathlib.Path:
        if self._logging_directory is None:
            # create new folder 'logs'
            path = self.root_file.parent / pathlib.Path("logs")
            create_folder(path)
            # create new folder 'logs.date'
            self._logging_directory = path / pathlib.Path(datetime.datetime.now().strftime("log_%Y_%m_%d"))
            create_folder(self._logging_directory)

        return self._logging_directory

    @logging_directory.setter
    def logging_directory(self, logging_directory: str):
        if not check_if_folder_exists(logging_directory):
            raise ValueError("'logging_directory' not found.")

        self._logging_directory = logging_directory

    def _setup_logger(self):
        self.logger.setLevel(logging.DEBUG)

        # file handler
        file_handler = logging.FileHandler(self.logging_directory / pathlib.Path(self.root_file.stem + '.log'),
                                           encoding="UTF-8", mode='a')
        # file_handler.setLevel(logging.DEBUG)

        # console logger
        console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.DEBUG)

        # formatter
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d %(levelname)-8s || %(name)-25s %(message)s\n', datefmt='%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.critical("\n"
                             "\n#######################################################################################"
                             "\n#######################################################################################"
                             "\n")
        self.logger.addHandler(console_handler)

    @staticmethod
    def log_formatter(class_, name: str, message: str) -> str:
        message = message.replace('\t', '\t\t')
        return f"{type(class_).__name__}: {name}\n\t{message}"

    def error(self):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = '\\'.join(os.path.split(exc_tb.tb_frame.f_code.co_filename))
        return f"{exc_type}:{exc_obj.args[0]} \nfile: {fname}, line: {exc_tb.tb_lineno}"


config = Configurations()
