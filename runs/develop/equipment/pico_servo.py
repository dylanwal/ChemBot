import enum
import logging
import time

from unitpy import Quantity, Unit

from serial import Serial


logger = logging.getLogger("pico")


class PicoHardware:
    # all pins GPIO numbering (except adc)
    ADC_resolution = 65535
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
    v_sys = 3.3 * Unit("volt")

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
            if resistor in ("u", "d", "n"):
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
        if time_.dimensionality != Unit("second").dimensionality:
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


def encode_message(text: str):
    return text.replace("\n", "__n__").replace("\r", "__r__")


def decode_message(text: str):
    return text.replace("__n__", "\n").replace("__r__", "\r")


def analog_to_voltage(analog: int) -> Quantity:
    return analog * PicoHardware.v_sys / 65535  # 65535 = 2**16 or 16 bit resolution of the ADC


def analog_to_temperature(analog: int) -> Quantity:
    voltage = analog_to_voltage(analog)
    return (27 - (voltage.v - 0.706) / 0.001721) * Unit.degC  # equation from RP2040 data sheet (section 4.9.5)


class PinStatus(enum.Enum):
    STANDBY = -1
    DIGITAL_OFF = 0  # output pull down
    DIGITAL_ON = 1
    DIGITAL_INPUT = 2
    ANALOG = 3
    PWM = 4
    SERIAL = 5
    SPI = 6
    I2C = 7


class PicoSerial:
    def __init__(self, comport: str, encoding: str = "UTF-8"):
        self.serial = Serial(comport, timeout=1)
        self.encoding = encoding

        self.pins = {pin: PinStatus.STANDBY for pin in PicoHardware.pins_GPIO}
        self.pico_version = None

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write_reset()
        self.serial.close()

    def activate(self):
        reply = self.write_plus_read_until("v")
        if reply[0] != "v":
            raise ValueError(f"Unexpected reply from Pico during activation.\n reply:{reply}")
        self.pico_version = reply[1:]

    def deactivate(self):
        self.write_reset()

    def _write(self, message: str):
        message = encode_message(message) + "\n"
        logger.debug("write: " + message)
        self.serial.write(message.encode(self.encoding))

    def _read(self, read_bytes: int) -> str:
        message = self.serial.read(read_bytes)
        return decode_message(message.decode(self.encoding).strip("\n"))

    def _read_until(self, symbol: str = "\n") -> str:
        message = self.serial.read_until(symbol)
        return decode_message(message.decode(self.encoding).strip("\n"))

    def _read_all(self, decode: bool = True) -> str:
        message = self.serial.read(self.serial.in_waiting)
        if decode:
            return decode_message(message.decode(self.encoding).strip("\n"))
        else:
            return message.decode(self.encoding)

    def write_plus_read_until(self, message: str, symbol: str = "\n") -> str:
        self._write(message)
        return self._read_until(symbol)

    def _stop(self):
        self.write_plus_read_until("r")

    def read_pico_version(self) -> str:
        """
        version of pico communication code
        """
        return self.pico_version

    def write_reset(self):
        """
        reset all pins to off
        """
        reply = self.write_plus_read_until("r")
        if reply[0] != "r":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

    def write_digital(self, pin: int, value: int, resistor: str = None):
        """
        Turn GPIO pin on, off

        Parameters
        ----------
        pin:
            GPIO pin
            range: [0:1:28]
        value:
            0: off; 1 on
            range: [0, 1]
        resistor:
            'n': No resistor, 'u': pull up, 'd': pull down
            range: ['n', 'u', 'd']

        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        resistor = PicoHardware.validate_digital_resistor(resistor)
        if value not in (0, 1):
            raise ValueError(f"Digital value can only be [0, 1]. \ngiven: {value}")

        # action
        reply = self.write_plus_read_until(f"d{pin:02}o{resistor}{value}")
        if reply != "d":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        # update pin status
        if value == 1:
            self.pins[pin] = PinStatus.DIGITAL_ON
        else:
            self.pins[pin] = PinStatus.DIGITAL_OFF

    def write_led(self, value: int):
        """
        Turn built in LED on, off

        Parameters
        ----------
        value: int
            0: off; 1 on
            range: [0, 1]
        """
        self.write_digital(PicoHardware.pin_LED, value, 'n')

    def read_digital(self, pin: int, resistor: str = None) -> int:
        """
        read_digital

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0:28]
        resistor:
            'n': No resistor, 'u': pull up, 'd': pull down
            range: ['n', 'u', 'd']

        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        resistor = PicoHardware.validate_digital_resistor(resistor)

        # action
        reply = self.write_plus_read_until(f"d{pin:02}i{resistor}")
        if reply[0] != "d":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        # update pin status
        self.pins[pin] = PinStatus.DIGITAL_INPUT

        return int(reply[1])

    def read_analog(self, pin: int) -> int:
        """
        read_analog

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0:4]

        Returns
        -------
        value: int
            range: [0:65535]
        """
        # validation
        PicoHardware.validate_adc_pin(pin)

        # action
        reply = self.write_plus_read_until(f"a{pin:02}")
        if reply[0] != "a":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        # update pin status
        self.pins[pin] = PinStatus.ANALOG

        return int(reply[1:])

    def read_internal_temperature(self) -> Quantity:
        """
        read the pico's internal temperature sensor
        board temperature sensor is very sensitive to errors in the reference voltage

        Returns
        -------
        temperature:
            degrees Celsius

        """
        analog = self.read_analog(PicoHardware.pin_internal_temp)
        return round(analog_to_temperature(analog), 3)

    def write_pwm(self, pin: int, duty: int, frequency: int):
        """
        write_pwm

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0:28]
        duty: int
            how much the pulse is 'on'
            range: [0:65_535]
            duty = 0 turns off pwm
        frequency:
            PWM pulse frequency
            range: [7:125_000_000]
        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        PicoHardware.validate_pwm_duty(duty)
        PicoHardware.validate_pwm_frequency(frequency)

        # action
        reply = self.write_plus_read_until(f"p{pin:02}{duty:05}{frequency:09}")
        if reply != "p":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[pin] = PinStatus.PWM

    def write_pwm_pulse(self, pin: int, duty: int, frequency: int, time_: Quantity):
        """
        write_pwm_pulse

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0:28]
        duty: int
            how much the pulse is 'on'
            range: [0:65_535]
        frequency:
            PWM pulse frequency
            range: [7:125_000_000]
        time_:
            time the PWM will remain on
            _range: [999 * U("s"):1 * U("us")]

        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        PicoHardware.validate_pwm_duty(duty)
        PicoHardware.validate_pwm_frequency(frequency)
        time_ = PicoHardware.validate_pwm_time(time_)

        # action
        reply = self.write_plus_read_until(f"q{pin:02}{duty:05}{frequency:09}{time_}")
        if reply != "q":
            self._unexpected_reply_from_pico(reply)

    def write_serial(self,
                     message: str,
                     uart_id: int,
                     tx_pin: int,
                     rx_pin: int,
                     baudrate: int = 9600,
                     bits: int = 8,
                     parity: int = None,
                     stop: int = 1
                     ):
        """
        write_serial

        Parameters
        ----------
        message: str
            message to send
        uart_id:
            range: [0, 1]
        tx_pin:
            GPIO pin
            range: [0:28]
        rx_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2, None]
        stop:
            range: [1, 2]

        """
        # validation
        PicoHardware.validate_uart_pin(uart_id, tx_pin, rx_pin)
        PicoHardware.validate_uart_parameters(baudrate, bits, parity, stop)
        if parity is None:
            parity = 2

        # action
        message_ = f"t{uart_id}{tx_pin:02}{rx_pin:02}{baudrate:06}{bits}{parity}{stop}w{message}"
        reply = self.write_plus_read_until(message_)
        if reply != "t":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[tx_pin] = PinStatus.SERIAL
        self.pins[rx_pin] = PinStatus.SERIAL

    def read_serial(self,
                    amount: int,
                    uart_id: int,
                    tx_pin: int,
                    rx_pin: int,
                    baudrate: int = 9600,
                    bits: int = 8,
                    parity: int = None,
                    stop: int = 1
                    ) -> str:
        """
        read_serial

        Parameters
        ----------
        amount: int
            number of bytes to read
        uart_id:
            range: [0, 1]
        tx_pin:
            GPIO pin
            range: [0:28]
        rx_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2, None]
        stop:
            range: [1, 2]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_uart_pin(uart_id, tx_pin, rx_pin)
        PicoHardware.validate_uart_parameters(baudrate, bits, parity, stop)
        if parity is None:
            parity = 2

        # action
        message_ = f"t{uart_id}{tx_pin:02}{rx_pin:02}{baudrate:06}{bits}{parity}{stop}s{amount}"
        reply = self.write_plus_read_until(message_)
        if reply[0] != "t":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[tx_pin] = PinStatus.SERIAL
        self.pins[rx_pin] = PinStatus.SERIAL

        return reply[1:]

    def read_until_serial(self,
                          uart_id: int,
                          tx_pin: int,
                          rx_pin: int,
                          baudrate: int = 9600,
                          bits: int = 8,
                          parity: int = None,
                          stop: int = 1
                          ) -> str:
        """
        read_until_serial

        Parameters
        ----------
        uart_id:
            range: [0, 1]
        tx_pin:
            GPIO pin
            range: [0:28]
        rx_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2, None]
        stop:
            range: [1, 2]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_uart_pin(uart_id, tx_pin, rx_pin)
        PicoHardware.validate_uart_parameters(baudrate, bits, parity, stop)
        if parity is None:
            parity = 2

        # action
        message_ = f"t{uart_id}{tx_pin:02}{rx_pin:02}{baudrate:06}{bits}{parity}{stop}r"
        reply = self.write_plus_read_until(message_)
        if reply[0] != "t":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[tx_pin] = PinStatus.SERIAL
        self.pins[rx_pin] = PinStatus.SERIAL

        return reply[1:]

    def write_plus_read_until_serial(self,
                                     message: str,
                                     uart_id: int,
                                     tx_pin: int,
                                     rx_pin: int,
                                     baudrate: int = 9600,
                                     bits: int = 8,
                                     parity: int = None,
                                     stop: int = 1
                                     ) -> str:
        """
        write_serial

        Parameters
        ----------
        message: str
            message to send
        uart_id:
            range: [0, 1]
        tx_pin:
            GPIO pin
            range: [0:28]
        rx_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2, None]
        stop:
            range: [1, 2]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_uart_pin(uart_id, tx_pin, rx_pin)
        PicoHardware.validate_uart_parameters(baudrate, bits, parity, stop)
        if parity is None:
            parity = 2

        # action
        message_ = f"t{uart_id}{tx_pin:02}{rx_pin:02}{baudrate:06}{bits}{parity}{stop}b{message}"
        reply = self.write_plus_read_until(message_)
        if reply[0] != "t":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[tx_pin] = PinStatus.SERIAL
        self.pins[rx_pin] = PinStatus.SERIAL

        return reply[1:]

    def write_spi(self,
                  message: str,
                  spi_id: int,
                  sck_pin: int,
                  mosi_pin: int,
                  miso_pin: int,
                  cs_pin: int,
                  baudrate: int = 115_200,
                  bits: int = 8,
                  polarity: int = 0,
                  phase: int = 0
                  ):
        """
        write_spi

        Parameters
        ----------
        message: str
            message to send
        spi_id:
            range: [0, 1]
        sck_pin:
            GPIO pin
            range: [0:28]
        mosi_pin:
            GPIO pin
            range: [0:28]
        miso_pin:
            GPIO pin
            range: [0:28]
        cs_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600:115_200]
            # could increase to 1000000
        bits:
            range: [7, 8, 9]
        polarity:
            range: [0, 1]
        phase:
            range: [0, 1]

        """
        # validation
        PicoHardware.validate_spi_pin(spi_id, sck_pin, mosi_pin, miso_pin, cs_pin)
        PicoHardware.validate_spi_parameters(baudrate, bits, polarity, phase)

        # action
        message_ = f"s{spi_id}{sck_pin:02}{mosi_pin:02}{miso_pin:02}{baudrate:06}{bits}{polarity}{phase}" \
                   f"{cs_pin:02}w{message}"
        reply = self.write_plus_read_until(message_)
        if reply != "s":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[sck_pin] = PinStatus.SPI
        self.pins[mosi_pin] = PinStatus.SPI
        self.pins[miso_pin] = PinStatus.SPI
        self.pins[cs_pin] = PinStatus.SPI

    def read_spi(self,
                 amount: int,
                 spi_id: int,
                 sck_pin: int,
                 mosi_pin: int,
                 miso_pin: int,
                 cs_pin: int,
                 baudrate: int = 115_200,
                 bits: int = 8,
                 polarity: int = 0,
                 phase: int = 0
                 ) -> str:
        """
        write_spi

        Parameters
        ----------
        amount: int
            number of bytes to read
        spi_id:
            range: [0, 1]
        sck_pin:
            GPIO pin
            range: [0:28]
        mosi_pin:
            GPIO pin
            range: [0:28]
        miso_pin:
            GPIO pin
            range: [0:28]
        cs_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600:115_200]
            # could increase to 1000000
        bits:
            range: [7, 8, 9]
        polarity:
            range: [0, 1]
        phase:
            range: [0, 1]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_spi_pin(spi_id, sck_pin, mosi_pin, miso_pin, cs_pin)
        PicoHardware.validate_spi_parameters(baudrate, bits, polarity, phase)

        # action
        message_ = f"s{spi_id}{sck_pin:02}{mosi_pin:02}{miso_pin:02}{baudrate:06}{bits}{polarity}{phase}" \
                   f"{cs_pin:02}r{amount}"
        reply = self.write_plus_read_until(message_)
        if reply[0] != "s":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[sck_pin] = PinStatus.SPI
        self.pins[mosi_pin] = PinStatus.SPI
        self.pins[miso_pin] = PinStatus.SPI
        self.pins[cs_pin] = PinStatus.SPI

        return reply[1:]

    def write_plus_read_spi(self,
                            message: str,
                            amount: int,
                            spi_id: int,
                            sck_pin: int,
                            mosi_pin: int,
                            miso_pin: int,
                            cs_pin: int,
                            baudrate: int = 115_200,
                            bits: int = 8,
                            polarity: int = 0,
                            phase: int = 0
                            ) -> str:
        """
        write_spi

        Parameters
        ----------
        message: str
            message to send
        amount: int
            number of bytes to read
        spi_id:
            range: [0, 1]
        sck_pin:
            GPIO pin
            range: [0:28]
        mosi_pin:
            GPIO pin
            range: [0:28]
        miso_pin:
            GPIO pin
            range: [0:28]
        cs_pin:
            GPIO pin
            range: [0:28]
        baudrate: int
            range: [9600:115_200]
            # could increase to 1000000
        bits:
            range: [7, 8, 9]
        polarity:
            range: [0, 1]
        phase:
            range: [0, 1]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_spi_pin(spi_id, sck_pin, mosi_pin, miso_pin, cs_pin)
        PicoHardware.validate_spi_parameters(baudrate, bits, polarity, phase)

        # action
        message_ = f"s{spi_id}{sck_pin:02}{mosi_pin:02}{miso_pin:02}{baudrate:06}{bits}{polarity}{phase}" \
                   f"{cs_pin:02}b{amount:03}{message}"
        reply = self.write_plus_read_until(message_)
        if reply[0] != "s":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[sck_pin] = PinStatus.SPI
        self.pins[mosi_pin] = PinStatus.SPI
        self.pins[miso_pin] = PinStatus.SPI
        self.pins[cs_pin] = PinStatus.SPI

        return reply[1:]

    def write_i2c(self,
                  message: str,
                  address: int,
                  i2c_id: int,
                  scl_pin: int,
                  sda_pin: int,
                  frequency: int = 115_200,
                  ):
        """
        write_i2c

        Parameters
        ----------
        message: str
            message to send
        address: int
            address
        i2c_id:
            range: [0, 1]
        scl_pin:
            GPIO pin
            range: [0:28]
        sda_pin:
            GPIO pin
            range: [0:28]
        frequency: int
            range: [400_000]

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)
        PicoHardware.validate_i2c_parameters(frequency, address)

        # action
        reply = self.write_plus_read_until(f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}w{message}")
        if reply[0] != "i":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[scl_pin] = PinStatus.I2C
        self.pins[sda_pin] = PinStatus.I2C

    def read_i2c(self,
                 amount: int,
                 address: int,
                 i2c_id: int,
                 scl_pin: int,
                 sda_pin: int,
                 frequency: int = 115_200,
                 ) -> str:
        """
        read_i2c

        Parameters
        ----------
        amount: int
            number of bytes to read
        address: int
            address
        i2c_id:
            range: [0, 1]
        scl_pin:
            GPIO pin
            range: [0:28]
        sda_pin:
            GPIO pin
            range: [0:28]
        frequency: int
            range: [400_000]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)
        PicoHardware.validate_i2c_parameters(frequency, address)

        # action
        reply = self.write_plus_read_until(f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}r{amount}")
        if reply[0] != "i":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[scl_pin] = PinStatus.I2C
        self.pins[sda_pin] = PinStatus.I2C

        return reply[1:]

    def read_scan_i2c(self,
                      i2c_id: int,
                      scl_pin: int,
                      sda_pin: int,
                      frequency: int = 115_200,
                      ) -> str:
        """
        Scan all I2C addresses between 0x08 and 0x77 inclusive and return a list of those that respond.

        Parameters
        ----------
        i2c_id:
            range: [0, 1]
        scl_pin:
            GPIO pin
            range: [0:28]
        sda_pin:
            GPIO pin
            range: [0:28]
        frequency: int
            range: [400_000]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)

        # action
        reply = self.write_plus_read_until(f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}s")
        if reply[0] != "i":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[scl_pin] = PinStatus.I2C
        self.pins[sda_pin] = PinStatus.I2C

        return reply[1:]

    def write_plus_read_i2c(self,
                            message: str,
                            amount: int,
                            address: int,
                            i2c_id: int,
                            scl_pin: int,
                            sda_pin: int,
                            frequency: int = 115_200,
                            ):
        """
        write_plus_read_i2c

        Parameters
        ----------
        message: str
            message to send
        amount: int
            number of bytes to read
        address: int
            address
        i2c_id:
            range: [0, 1]
        scl_pin:
            GPIO pin
            range: [0:28]
        sda_pin:
            GPIO pin
            range: [0:28]
        frequency: int
            range: [400_000]

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)
        PicoHardware.validate_i2c_parameters(frequency, address)

        # action
        message_ = f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}b{amount:03}{message}"
        reply = self.write_plus_read_until(message_)
        if reply[0] != "i":
            self._unexpected_reply_from_pico(reply)

        # update pin status
        self.pins[scl_pin] = PinStatus.I2C
        self.pins[sda_pin] = PinStatus.I2C

        return reply[1:]

    def _unexpected_reply_from_pico(self, reply: str):
        time.sleep(1)
        reply += self._read_all(decode=False)  # get everything from buffer
        raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")


def main():
    with PicoSerial("COM12") as pico:
        print(pico.read_internal_temperature())
        print(pico.read_analog(2))


if __name__ == "__main__":
    main()
