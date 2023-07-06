import chembot

from runs.individual_setup.names import NamesSerial

serial = chembot.communication.PicoSerial(NamesSerial.PICO2, "COM4")
serial.activate()
