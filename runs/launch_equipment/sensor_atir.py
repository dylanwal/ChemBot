
import chembot

from runs.launch_equipment.names import NamesSensors

atir = chembot.equipment.sensors.ATIR(NamesSensors.ATIR)
atir.activate()
