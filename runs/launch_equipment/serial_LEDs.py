import chembot

from runs.launch_equipment.names import NamesSerial

serial = chembot.communication.PicoSerial(NamesSerial.PICO1, "COM4")
serial.activate()
