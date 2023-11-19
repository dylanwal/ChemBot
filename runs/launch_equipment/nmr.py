
import chembot

from runs.launch_equipment.names import NamesSensors

nmr = chembot.equipment.sensors.NMR(NamesSensors.NMR, "192.168.0.100", 13000)
nmr.activate()

