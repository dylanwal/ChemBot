import chembot

from runs.individual_setup.equipment_names import NamesSerial

serial = chembot.communication.PicoSerial(NamesSerial.PICO1, "COM4")
serial.activate()
