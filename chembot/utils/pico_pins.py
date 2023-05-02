from unitpy import U


class PicoHardware:
    # all pins GPIO numbering (except adc)
    pins_GPIO = list(range(0, 22)) + [25, 26, 27, 28]
    pin_LED = 25
    pin_adc = [0, 1, 2]
    pin_adc_GPIO = [26, 27, 28]
    pin_internal_temp = 4  # ADC4
    pin_vsys = 3  # ADC3
    pin_i2c = {
        0: [
            [0, 1],  # sda, scl
            [4, 5],
            [8, 9],
            [12, 13],
            [16, 17],
            [20, 21]
        ],
        1: [
            [2, 3],
            [6, 7],
            [10, 11],
            [14, 15],
            [18, 19],
            [26, 27]
        ]
    }
    pin_spi = {
        0: [
            [0, 3, 2],  # rx(miso), tx(mosi), clk
            [4, 7, 6],
            [16, 19, 18]
        ],
        1: [
            [8, 11, 10],
            [12, 15, 14]
        ]
    }
    pin_uart = {
        0: [
            [0, 1],  # tx rx
            [12, 13],
            [16, 17],
        ],
        1: [
            [4, 5],
            [8, 9]
        ]
    }
    v_sys = 3.3 * U("volt")

    @classmethod
    def validate_GPIO_pin(cls, pin: int):
        if not cls.is_GPIO_pin(pin):
            raise ValueError("Invalid GPIO Pin for pi pico")

    @classmethod
    def is_GPIO_pin(cls, pin: int) -> bool:
        if pin in cls.pins_GPIO:
            return True
        return False

    @classmethod
    def validate_adc_pin(cls, pin: int):
        if not cls.is_adc_pin(pin):
            raise ValueError("Invalid ADC Pin for pi pico.")

    @classmethod
    def is_adc_pin(cls, pin: int) -> bool:
        if pin in cls.pin_adc:
            return True
        if pin in cls.pin_adc_GPIO:
            return True
        return False
