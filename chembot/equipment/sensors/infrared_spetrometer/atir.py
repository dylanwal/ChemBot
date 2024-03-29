import pathlib
import logging
import queue
import threading

import win32ui  # needed to find 'dde' package  /  from pywin32 package
import dde  # from pywin32 package
import numpy as np

from chembot.configuration import config, create_folder
from chembot.equipment.sensors.sensor import Sensor

logger = logging.getLogger(config.root_logger_name + ".atir")


class ATIRRunner:
    def __init__(self):
        self.server = dde.CreateServer()
        self.server.Create("test")
        self.conversation = dde.CreateConversation(self.server)
        self.conversation.ConnectTo("OPUS", "System")
        self.conversation.Request("REQUEST_MODE")
        logger.debug(config.log_formatter(ATIRRunner, "atirrunner", "DDE server activated"))

    def request(self, command: str) -> list:
        logger.debug(f"commands: {command}")
        result = self.conversation.Request(command).encode("utf_16_le").decode("utf_8").splitlines()
        if result[0] != "OK":
            raise Exception("\n".join(result))
        return result

    def run_background_scans(self, experiment_path: str, experiment_name: str, scans: int = None,
                             resolution: float = None):
        """
        Runs the background scans for an experiment with the given parameters.

        Parameters
        ----------
        experiment_path:
            The path to the folder which contains the experiment file.
        experiment_name:
            The class_name of the experiment file.
        scans:
            The number of background scans that should be performed. Defaults to the setting in the experiment file.
        resolution:
            The resolution of the measurement. Defaults to the setting in the experiment file.

        """
        if scans is not None and scans <= 0:
            raise Exception("Number of background scans must be positive.")

        parameters = f"EXP='{experiment_name}',XPP='{experiment_path}'"
        if scans is not None:
            parameters += f",NSR={scans}"
        if resolution is not None:
            parameters += f",RES={resolution}"
        self.request("COMMAND_LINE MeasureReference (0,{" + parameters + "});")

    def measure_sample(self, experiment_path: str, experiment_name: str, scans: int = None,
                       resolution: float = None) -> str:
        """
        Measures a sample with the given parameters.
        The experiment file specifies the default parameters for the experiment, which can be overridden by the
        other parameters.

        experiment_path:
            The path to the folder which contains the experiment file.
        experiment_name:
            The class_name of the experiment file.
        scans:
            The number of background scans that should be performed. Defaults to the setting in the experiment file.
        resolution:
            The resolution of the measurement. Defaults to the setting in the experiment file.

        Returns
        -------

        """
        measurement_display_mode = 0
        """
        measurement_display_mode:
            The display mode. 
            0 means that OPUS will not ask the user for confirmation to start measurements beforehand
            1 means OPUS will show single scans from the device until the "Start Measurements" button is manually 
            pushed, which is undesirable.
        """

        if scans is not None and scans <= 0:
            raise Exception("Number of scans must be positive.")

        parameters = f"MDM={measurement_display_mode},EXP='{experiment_name}',XPP='{experiment_path}'"
        if scans is not None:
            parameters += f",NSR={scans}"
        if resolution is not None:
            parameters += f",RES={resolution}"
        parameters += f",SNM=RAFT2_3"
        result = self.request("COMMAND_LINE MeasureSample (0,{" + parameters + "});")
        logger.debug("result: " + str(result))
        try:
            return result[3]
        except Exception as e:
            raise Exception("Unexpected data format. OPUS returned: " + "\n".join(result))

    def get_results(self, result_file: str) -> np.array:
        _ = self.request("READ_FROM_FILE %s" % result_file)  # here to make sure it reads the right file
        _ = self.request("READ_FROM_BLOCK AB")
        _ = self.request("DATA_VALUES")
        result_data = self.request("READ_DATA")
        status = result_data[0]
        if status != "OK":
            raise ValueError("Error with reading data from AT-IR.")

        data_length = int(result_data[2])
        wavenumber_upper = float(result_data[3])
        wavenumber_lower = float(result_data[4])
        scaling_factor = int(result_data[5])
        x = np.linspace(wavenumber_lower, wavenumber_upper, data_length)
        y = np.array(result_data[6:-1], dtype="float64") * scaling_factor
        return np.column_stack((x, y))


class ATIR(Sensor):
    _method_name = "ATR_DI2"
    _method_path = str(pathlib.Path(__file__).parent)

    @property
    def _data_path(self):
        path = config.data_directory / pathlib.Path("atir")
        create_folder(path)
        return path

    def __init__(self, name: str):
        super().__init__(name)
        self._runner = ATIRRunner()

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def _stop(self):
        pass

    def write_measure(self, data_name: str = None, scans: int = 16) -> np.ndarray:
        rf = self._runner.measure_sample(self._method_path, self._method_name, scans)
        logger.warning(rf)
        return self._runner.get_results(rf)[:, 1]  # TODO: figure out what to do with the wavelength shape (1754,2)

    def write_background(self, scans: int = 16):
        self._runner.run_background_scans(self._method_path, self._method_name, scans)
