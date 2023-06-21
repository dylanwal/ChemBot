
from unitpy import U

import chembot

red = chembot.equipment.lights.LightPico(
    name="deep_red",
    color=665 * U.nm,
    pin=0,
    communication="pico_serial"
)

mint = chembot.equipment.lights.LightPico(
    name="mint",
    color=550 * U.nm,
    pin=1,
    communication="pico_serial"
)

green = chembot.equipment.lights.LightPico(
    name="green",
    color=530 * U.nm,
    pin=2,
    communication="pico_serial"
)

cyan = chembot.equipment.lights.LightPico(
    name="cyan",
    color=500 * U.nm,
    pin=3,
    communication="pico_serial"
)

blue = chembot.equipment.lights.LightPico(
    name="blue",
    color=475 * U.nm,
    pin=4,
    communication="pico_serial"
)

violet = chembot.equipment.lights.LightPico(
    name="violet",
    color=425 * U.nm,
    pin=5,
    communication="pico_serial"
)

with chembot.utils.EquipmentManager() as manager:
    manager.add([red, mint, green, cyan, blue, violet])
    manager.activate()
