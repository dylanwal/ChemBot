import pathlib
import logging
from datetime import datetime

import win32ui  # from pywin32 package and must be imported first to expose dde
import dde  # from pywin32 package
import numpy as np

from chembot.configuration import config
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

        parameters = f"EXP={experiment_name},XPP={experiment_path}"
        if scans is not None:
            parameters += f",NSR={scans}"
        if resolution is not None:
            parameters += f",RES={resolution}"
        self.request(f"COMMAND_LINE MeasureReference (0,{parameters});")

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

        parameters = f"MDM={measurement_display_mode},EXP={experiment_name},XPP={experiment_path}"
        if scans is not None:
            parameters += f",NSR={scans}"
        if resolution is not None:
            parameters += f",RES={resolution}"
        result = self.request(f"COMMAND_LINE MeasureSample (0,{parameters});")

        try:
            return result[3]
        except Exception as e:
            raise Exception("Unexpected data format. OPUS returned: " + "\n".join(result))

    def get_results(self, result_file: str) -> np.array:
        result_read = self.request("READ_FROM_FILE %s" % result_file)
        result_block = self.request("READ_FROM_BLOCK AB")
        result_data_points = self.request("DATA_VALUES")
        result_data = self.request("READ_DATA")
        try:
            data_length = int(result_data[2])
            wavenumber_upper = float(result_data[3])
            wavenumber_lower = float(result_data[4])
            scaling_factor = int(result_data[5])
            data = np.array([
                [
                    wavenumber_lower + i * (wavenumber_upper - wavenumber_lower) / (data_length - 1),
                    float(result_data[6 + i]),
                ] for i in range(data_length)
            ])
            return data
        except:
            raise Exception("Unexpected data format. OPUS returned: " + "\n".join(result))


class ATIR(Sensor):
    _method_name = "ATR_DI"
    _method_path = str(pathlib.Path(__file__).parent)
    _data_path = config.data_directory / pathlib.Path("atir")

    def __init__(self,
                 name: str,
                 ):
        super().__init__(name)

        self._runner = ATIRRunner()

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def _stop(self):
        pass

    def write_measure(self, data_name: str = None, scans: int = 8):
        rf = self._runner.measure_sample(self._method_path, self._method_name, scans)
        res = self._runner.get_results(rf)

        if data_name is None:
            data_name = "atir_data_" + datetime.now().strftime("data_%Y_%m_%d")

        np.savetxt(self._data_path / data_name, res, delimiter=",")

    def write_background(self, scans: int = 8):
        self._runner.run_background_scans(self._method_path, self._method_name, scans)
