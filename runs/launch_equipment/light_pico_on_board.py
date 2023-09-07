
import chembot
from runs.launch_equipment.equipment_names import NamesSerial

on_board_LED = chembot.equipment.lights.LightPico(
    name="on_board_LED",
    pin=0,
    communication=NamesSerial.PICO1
)
on_board_LED.activate()
