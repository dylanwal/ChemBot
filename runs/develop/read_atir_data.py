from datetime import datetime

import win32ui  # needed to find 'dde' package  /  from pywin32 package
import dde  # from pywin32 package
import numpy as np


class ATIRRunner:
    def __init__(self):
        self.server = dde.CreateServer()
        self.server.Create("test")
        self.conversation = dde.CreateConversation(self.server)
        self.conversation.ConnectTo("OPUS", "System")
        self.conversation.Request("REQUEST_MODE")

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
        result = self.request("COMMAND_LINE MeasureSample (0,{" + parameters + "});")
        try:
            return result[3]
        except Exception as e:
            raise Exception("Unexpected data format. OPUS returned: " + "\n".join(result))

    def get_results(self, result_file: str) -> np.array:
        a = self.request("READ_FROM_FILE %s" % result_file)  # here to make sure it reads the right file
        b = self.request("READ_FROM_BLOCK AB")
        c = self.request("DATA_VALUES")
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

    def get_date(self, result_file: str):
        a = self.request("READ_FROM_FILE %s" % result_file)  # here to make sure it reads the right file
        b = self.request("FILE_PARAMETERS")
        date_ = self.request("READ_PARAMETER DAT")[2]
        date_ = date_.split(r"/")
        time_ = self.request("READ_PARAMETER TIM")[2]
        out = datetime(
            day=int(date_[0]),
            month=int(date_[1]),
            year=int(date_[2]),
            hour=int(time_.split(":")[0]),
            minute=int(time_.split(":")[1]),
            second=int(time_.split(":")[2].split(".")[0]),
        )
        return out.timestamp()


def main():
    runner = ATIRRunner()
    n = 432  # 433
    data = np.zeros((n+1, 1755))
    for i in range(1, n+1):
        rf = fr'"C:\Users\Robot2\Documents\Bruker\OPUS_8.7.10\DATA\MEAS\Sample description.{i}" 1'
        d = runner.get_results(rf)
        time_ = runner.get_date(rf)
        if i == 1:
            data[0, 1:] = d[:, 0]
        data[i, 0] = time_
        data[i, 1:] = d[:, 1]

    np.savetxt("DW2-1-ATIR.csv", data, delimiter=",")
    print("hi")


if __name__ == "__main__":
    main()