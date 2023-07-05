
import chembot
from runs.individual_setup.equipment_names import NamesSerial

on_board_LED = chembot.equipment.lights.LightPico(
    name="on_board_LED",
    pin=0,
    communication=NamesSerial.PICO1
)
on_board_LED.activate()
