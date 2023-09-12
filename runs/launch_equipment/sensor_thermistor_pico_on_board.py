
import chembot

from runs.launch_equipment.names import NamesSensors, NamesSerial

thermistor = chembot.equipment.sensors.TemperaturePICO(NamesSensors.PICO1_THERMISTOR, NamesSerial.PICO1)
thermistor.activate()
