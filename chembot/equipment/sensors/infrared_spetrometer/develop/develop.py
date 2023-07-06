import win32ui
import dde
import numpy as np


class ExperimentRunner:
    def __init__(self):
        self.server = dde.CreateServer()
        self.server.Create("test")
        self.conversation = dde.CreateConversation(self.server)
        serverName = "OPUS"
        self.conversation.ConnectTo(serverName, "System")
        self.conversation.Request("REQUEST_MODE")

    def request(self, command: str) -> list:
        result = self.conversation.Request(command).encode("utf_16_le").decode("utf_8").splitlines()
        if result[0] != "OK":
            raise Exception("\n".join(result))
        return result

    def run_background_scans(self, experiment_path: str, experiment_name: str, background_scans: int = None,
                             resolution: float = None):
        """
        Runs the background scans for an experiment with the given parameters.

        :param experiment_path: The path to the folder which contains the experiment file.
        :param experiment_name: The name of the experiment file.
        :background_scans: The number of background scans that should be performed. Defaults to the setting in the experiment file.
        :resolution: The resolution of the measurement. Defaults to the setting in the experiment file.
        """
        if background_scans is not None and background_scans <= 0:
            raise Exception("Number of background scans must be positive.")
        parameters = "EXP='%s',XPP='%s'" % (experiment_name, experiment_path)
        if background_scans is not None:
            parameters += ",NSR=%d" % background_scans
        if resolution is not None:
            parameters += ",RES=%f" % resolution
        self.request("COMMAND_LINE MeasureReference (0,{%s});" % (parameters))

    def measure_sample(self, experiment_path: str, experiment_name: str, scans: int = None, resolution: float = None,
                       measurement_display_mode: int = 0) -> str:
        """
        Measures a sample with the given parameters.
        The experiment file specifies the default parameters for the experiment, which can be overridden by the other parameters.

        :param experiment_path: The path to the folder which contains the experiment file.
        :param experiment_name: The name of the experiment file.
        :scans: The number of scans that should be performed. Defaults to the setting in the experiment file.
        :resolution: The resolution of the measurement. Defaults to the setting in the experiment file. Note that resolution of measurements must match with the resolution of background scans.
        :measurement_display_mode: The display mode. 0 means that OPUS will not ask the user for confirmation to start measurements beforehand,
        so 0 is the default value in this case. If the value is set to 1, OPUS will show single scans from the device until the "Start Measurements"
        button is manually pushed, which is undesirable.
        """
        if scans is not None and scans <= 0:
            raise Exception("Number of scans must be positive.")
        parameters = "MDM=%d,EXP='%s',XPP='%s'" % (measurement_display_mode, experiment_name, experiment_path)
        if scans is not None:
            parameters += ",NSS=%d" % scans
        if resolution is not None:
            parameters += ",RES=%f" % resolution
        result = self.request("COMMAND_LINE MeasureSample (0,{%s});" % (parameters))
        try:
            return result[3]
        except:
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


er = ExperimentRunner()
path = "C:\\Users\\Robot2\\Desktop\\test"
name = "ATR_DI"
er.run_background_scans(path, name, 1)
input("Press enter to run measurements.")
rf = er.measure_sample(path, name, 1)
print(rf)
res = er.get_results(rf)
print(res)
with open("signal.txt", "w") as f:
    for i in range(len(res)):
        f.write("%f %f\n" % (res[i, 0], res[i, 1]))
plt.plot(res[:, 0], res[:, 1])
plt.show()
