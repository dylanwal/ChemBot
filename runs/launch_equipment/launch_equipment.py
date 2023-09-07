# import collections
# import subprocess
# import sys
# import time
# import pathlib
#
# path = pathlib.Path(__file__).parent
#
# equipments = collections.OrderedDict()
# equipments["master_controller"] = path / "master_controller.py"
# equipments["serial_valves"] = path / "serial_valves.py"
# equipments["valves"] = path / "valves.py"
# equipments["pumps"] = path / "pumps.py"
# equipments["sensor_phase_sensor"] = path / "sensor_phase_sensor.py"
#
# # subprocess.run("cd .")
# for equipment, file in equipments.items():
#     a = subprocess.Popen([sys.executable, file], creationflags=subprocess.CREATE_NEW_CONSOLE)
#     time.sleep(0.3)
#     print(equipment)
#
print("done")
