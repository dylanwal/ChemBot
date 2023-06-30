import chembot

from runs.individual_setup.equipment_names import NamesSerial, NamesPump

serial_pump_front = chembot.communication.Serial(NamesSerial.PUMP_FRONT, "COM11")
serial_pump_front.activate()