from unitpy import U

import chembot

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
#
# green = chembot.lights.LightPico(
#     name="green",
#     color=530 * U.nm,
#     conversion=lambda x: (6.71 * x) * U("W/m**2"),
#     pin=2,
#     communication="pico_lights"
# )
#
# cyan = chembot.lights.LightPico(
#     name="cyan",
#     color=500 * U.nm,
#     conversion=lambda x: (9.22 * x) * U("W/m**2"),
#     pin=3,
#     communication="pico_lights"
# )
#
# blue = chembot.lights.LightPico(
#     name="blue",
#     color=475 * U.nm,
#     conversion=lambda x: (12.2 * x) * U("W/m**2"),
#     pin=4,
#     communication="pico_lights"
# )
#
# violet = chembot.lights.LightPico(
#     name="violet",
#     color=425 * U.nm,
#     conversion=lambda x: (18.3 * x) * U("W/m**2"),
#     pin=5,
#     communication="pico_lights"
# )


lights = [serial, red, mint] #, green, cyan, blue, violet]

chembot.utils.activate_multiple_equipment(lights)
