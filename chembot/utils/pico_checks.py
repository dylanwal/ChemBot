"""
Methods related to Pico

"""

pico_pins = list(range(0, 24)) + [25, 26, 27]


def check_GPIO_pins(pin: int):
    """
    Checks if pins in PICO GPIO pins
    """
    if not isinstance(pin, int):
        raise TypeError("GPIO pins must be of type 'int'.")

    if pin in pico_pins:
        return

    raise ValueError("Invalid Pico pin. acceptable values: 0")
