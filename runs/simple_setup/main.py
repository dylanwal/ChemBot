from unitpy import U

import chembot

controller = chembot.MasterController()

serial = chembot.communication.PicoSerial("pico_lights", "COM4")

red = chembot.equipment.lights.LightPico(
    name="deep_red",
    color=665 * U.nm,
    pin=0,
    communication="pico_lights"
)

mint = chembot.equipment.lights.LightPico(
    name="mint",
    color=550 * U.nm,
    pin=1,
    communication="pico_lights"
)


with chembot.utils.EquipmentManager() as manager:
    manager.add([controller, serial, red, mint])
    manager.activate()



