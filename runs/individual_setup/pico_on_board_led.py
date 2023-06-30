import chembot
on_board_LED = chembot.equipment.lights.LightPico(
    name="deep_red",
    pin=0,
    communication="pico_serial"
)
on_board_LED.activate()
