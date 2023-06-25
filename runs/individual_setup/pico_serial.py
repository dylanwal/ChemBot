import chembot

from runs.individual_setup.equipment_names import Serial

serial = chembot.communication.PicoSerial(Serial.PICO1, "COM3")
serial.activate()
