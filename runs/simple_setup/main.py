from unitpy import U

import chembot

controller = chembot.MasterController()

gui = chembot.GUI()

serial = chembot.communication.MockComm(
    "pico_lights"
)

red = chembot.lights.LightPico(
    name="deep_red",
    color=665 * U.nm,
    conversion=lambda x: (11.6 * x) * U("W/m**2"),
    pin=0,
    communication="pico_lights"
)

mint = chembot.lights.LightPico(
    name="mint",
    color=550 * U.nm,
    conversion=lambda x: (10.9 * x) * U("W/m**2"),
    pin=1,
    communication="pico_lights"
)

equip = [controller, gui, serial, red, mint]

chembot.utils.activate_multiple_equipment(equip)
