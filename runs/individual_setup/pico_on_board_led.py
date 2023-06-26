import chembot
on_board_LED = chembot.equipment.lights.LightPico(
    name="on_board_LED",
    pin=25,
    communication="pico_serial"
)
on_board_LED.activate()
