from unitpy import U, Quantity


class PicoHardware:
    # all pins GPIO numbering (except adc)
    pins_GPIO = list(range(0, 22)) + [25, 26, 27, 28]
    pin_LED = 25
    pin_adc = [0, 1, 2, 4]
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

    @classmethod
    def adc_pin_to_GPIO_pin(cls, pin: int):
        if pin in cls.pin_adc:
            index = cls.pin_adc.index(pin)
            return cls.pin_adc_GPIO[index]

        raise ValueError("Invalid ADC Pin for pi pico.")

    @classmethod
    def GPIO_pin_to_adc_pin(cls, pin: int):
        if pin in cls.pin_adc_GPIO:
            index = cls.pin_adc.index(pin)
            return cls.pin_adc[index]

        raise ValueError("Invalid ADC Pin for pi pico.")

    @staticmethod
    def validate_digital_resistor(resistor: str) -> str:
        if resistor is None:
            return "n"
        else:
            if resistor in ("u", "d"):
                return resistor

        raise ValueError("Invalid resistor option for pico digital.")

    @staticmethod
    def validate_pwm_duty(duty: int):
        if not (0 <= duty <= 65_535):
            raise ValueError(f"pwm duty must be between [0, 65_535].\n given:{duty}")

    @staticmethod
    def validate_pwm_frequency(frequency: int):
        if not (7 <= frequency <= 125_000_000):
            raise ValueError(f"pwm frequency must be between [0, 125_000_000].\n given:{frequency}")

    @staticmethod
    def validate_pwm_time(time_: Quantity) -> str:
        if time_.dimensionality != U("second").dimensionality:
            raise ValueError("Units must be time.")
        if time_.to("s").value > 999:
            raise ValueError("Too large of time for PWM to be on.")
        if time_.to("us").value > 1:
            raise ValueError("Too small of time for PWM to be on.")

        time_ = time_.to("us")
        if int(time_.value) < 999:
            return f"u{int(time_.value)}"
        time_ = time_.to("ms")
        if int(time_.value) < 999:
            return f"m{int(time_.value)}"

        time_ = time_.to("s")
        return f"s{int(time_.value)}"

    @classmethod
    def validate_uart_pin(cls, uart_id: int, tx_pin: int, rx_pin: int):
        if uart_id not in cls.pin_uart:
            raise ValueError("Invalid uart_id.")
        pins = cls.pin_uart[uart_id]
        if [tx_pin, rx_pin] not in pins:
            raise ValueError("Invalid tx or rx UART pins")

    @staticmethod
    def validate_uart_parameters(baudrate: int, bits: int, parity: int, stop: int):
        if not isinstance(baudrate, int) or not (9600 <= baudrate <= 115200):
            raise ValueError("Invalid uart baudrate.")
        if not bits not in (7, 8, 9):
            raise ValueError("Invalid uart bits.")
        if not parity not in (0, 1, 2, None):
            raise ValueError("Invalid uart parity.")
        if not stop not in (1, 2):
            raise ValueError("Invalid uart stop.")

    @classmethod
    def validate_spi_pin(cls, spi_id: int, sck_pin: int, mosi_pin: int, miso_pin: int, cs_pin: int):
        if spi_id not in cls.pin_spi:
            raise ValueError("Invalid spi_id.")
        pins = cls.pin_spi[spi_id]
        if [miso_pin, mosi_pin, sck_pin] not in pins:
            raise ValueError("Invalid spi miso_pin, mosi_pin or sck_pin pins.")
        cls.validate_GPIO_pin(cs_pin)

    @staticmethod
    def validate_spi_parameters(baudrate: int, bits: int, polarity: int, phase: int):
        if not isinstance(baudrate, int) or not (9600 <= baudrate <= 115200):
            raise ValueError("Invalid spi baudrate.")
        if not bits not in (7, 8, 9):
            raise ValueError("Invalid spi bits.")
        if not polarity not in (0, 1):
            raise ValueError("Invalid spi polarity.")
        if not phase not in (0, 1):
            raise ValueError("Invalid spi phase.")

    @classmethod
    def validate_i2c_pins(cls, i2c_id: int, scl_pin: int, sda_pin: int):
        if i2c_id not in cls.pin_spi:
            raise ValueError("Invalid i2c id.")
        pins = cls.pin_i2c[i2c_id]
        if [sda_pin, scl_pin] not in pins:
            raise ValueError("Invalid i2c scl or sda pins.")

    @staticmethod
    def validate_i2c_parameters(frequency: int, address: int):
        if not isinstance(frequency, int) or not (9600 <= frequency <= 115200):
            raise ValueError("Invalid i2c frequency.")
        if not isinstance(address, int) or not (8 <= address <= 119):
            raise ValueError("Invalid i2c address.")
