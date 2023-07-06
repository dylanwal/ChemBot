import chembot

from runs.individual_setup.names import NamesSerial

serial = chembot.communication.PicoSerial(NamesSerial.PICO1, "COM4")
serial.activate()
