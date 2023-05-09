
import chembot

pico = chembot.communication.PicoSerial("test_name", "COM3")

pico.write_digital(10, 1)
