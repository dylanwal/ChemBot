from unitpy import U

import chembot

controller = chembot.MasterController()

# gui = chembot.GUI()

serial = chembot.communication.PicoSerial("pico_lights", "COM4")

# red = chembot.equipment.lights.LightPico(
#     name="deep_red",
#     color=665 * U.nm,
#     pin=0,
#     communication="pico_lights"
# )
#
# mint = chembot.equipment.lights.LightPico(
#     name="mint",
#     color=550 * U.nm,
#     pin=1,
#     communication="pico_lights"
# )
#
equip = [controller, serial] # red, mint

chembot.utils.activate_multiple_equipment(equip)
