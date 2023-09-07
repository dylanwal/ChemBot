import chembot

from runs.launch_equipment.names import NamesSerial

serial = chembot.communication.PicoSerial(NamesSerial.PICO2, "COM12")
serial.activate()
