
import chembot

from runs.individual_setup.names import NamesSensors

atir = chembot.equipment.sensors.ATIR(NamesSensors.ATIR)
atir.activate()
