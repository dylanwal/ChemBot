
from unitpy import U

import chembot

from runs.individual_setup.equipment_names import NamesLEDColors, NamesSerial


red = chembot.equipment.lights.LightPico(
    name=NamesLEDColors.DEEP_RED,
    color=665 * U.nm,
    pin=0,
    communication=NamesSerial.PICO1
)

mint = chembot.equipment.lights.LightPico(
    name=NamesLEDColors.MINT,
    color=550 * U.nm,
    pin=1,
    communication=NamesSerial.PICO1
)

green = chembot.equipment.lights.LightPico(
    name=NamesLEDColors.GREEN,
    color=530 * U.nm,
    pin=2,
    communication=NamesSerial.PICO1
)

cyan = chembot.equipment.lights.LightPico(
    name=NamesLEDColors.CYAN,
    color=500 * U.nm,
    pin=3,
    communication=NamesSerial.PICO1
)

blue = chembot.equipment.lights.LightPico(
    name=NamesLEDColors.BLUE,
    color=475 * U.nm,
    pin=4,
    communication=NamesSerial.PICO1
)

violet = chembot.equipment.lights.LightPico(
    name=NamesLEDColors.VIOLET,
    color=425 * U.nm,
    pin=5,
    communication=NamesSerial.PICO1
)

with chembot.utils.EquipmentManager() as manager:
    manager.add([red, mint, green, cyan, blue, violet])
    manager.activate()
