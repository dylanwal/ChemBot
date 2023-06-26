
from unitpy import U

import chembot

from runs.individual_setup.equipment_names import LEDColors, Serial


red = chembot.equipment.lights.LightPico(
    name=LEDColors.DEEP_RED,
    color=665 * U.nm,
    pin=0,
    communication=Serial.PICO1
)

mint = chembot.equipment.lights.LightPico(
    name=LEDColors.MINT,
    color=550 * U.nm,
    pin=1,
    communication=Serial.PICO1
)

green = chembot.equipment.lights.LightPico(
    name=LEDColors.GREEN,
    color=530 * U.nm,
    pin=2,
    communication=Serial.PICO1
)

cyan = chembot.equipment.lights.LightPico(
    name=LEDColors.CYAN,
    color=500 * U.nm,
    pin=3,
    communication=Serial.PICO1
)

blue = chembot.equipment.lights.LightPico(
    name=LEDColors.BLUE,
    color=475 * U.nm,
    pin=4,
    communication=Serial.PICO1
)

violet = chembot.equipment.lights.LightPico(
    name=LEDColors.VIOLET,
    color=425 * U.nm,
    pin=5,
    communication=Serial.PICO1
)

with chembot.utils.EquipmentManager() as manager:
    manager.add([red, mint, green, cyan, blue, violet])
    manager.activate()
