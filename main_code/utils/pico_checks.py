"""
Methods related to Pico

"""

def check_GPIO_pins(pin: int) -> bool:
    """
    Checks if pins in range of PICO GPIO pins
    :return:
    """
    if 0 < pin < 28 and pin != 24:
        return True
    else:
        return False
