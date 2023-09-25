
import chembot
from runs.launch_equipment.names import NamesSerial

on_board_LED = chembot.equipment.lights.LightPico(
    name=NamesSerial.PICO1,
    pin=0,
    communication=NamesSerial.PICO1
)
on_board_LED.activate()
