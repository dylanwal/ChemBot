
import chembot

from runs.individual_setup.names import NamesSensors, NamesSerial

thermistor = chembot.equipment.sensors.TemperaturePICO(NamesSensors.PICO1_THERMISTOR, NamesSerial.PICO1)
thermistor.activate()
