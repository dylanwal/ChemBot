import enum
import logging

import serial
from serial.tools.list_ports import comports

from unitpy import Quantity

from chembot.configuration import config
from chembot.communication.communication import Communication
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply
from chembot.utils.pico_pins import PicoHardware

logger = logging.getLogger(config.root_logger_name + ".communication")


def encode_message(text: str):
    return text.replace("\n", "__n__").replace("\r", "__r__")


def decode_message(text: str):
    return text.replace("__n__", "\n").replace("__r__", "\r")


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


class PicoSerial(Communication):
    """
    Pico serial

    """
    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 port: str,
                 ):
        super().__init__(name)

        if port not in self.available_ports:
            raise ValueError(f"Port '{port}' is not connected to computer.")
        self.serial = serial.Serial(port=port, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=10)

        self.pins = {pin: PinStatus.STANDBY for pin in PicoHardware.pins_GPIO}

    def __repr__(self):
        return self.name + f" || port: {self.port}"

    def _read_port_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_port()))

    def read_port(self) -> str:
        """ read_port """
        return self.port

    def _activate(self):
        self._write_flush_buffer()

    def _deactivate(self):
        self.serial.close()

    def _write_write(self, message: str):
        message = encode_message(message) + "\n"
        self.serial.write(message.encode(config.encoding))

    def _read_read(self, read_bytes: int) -> str:
        message = self.serial.read(read_bytes).decode(config.encoding)
        return decode_message(message.strip("\n"))

    def write_write_plus_read_until(self, message: str, symbol: str = "\n") -> str:
        self.write_write(message)
        return self.read_read_until(symbol)

    def _read_read_until(self, symbol: str = "\n") -> str:
        return self.serial.read_until(symbol.encode(config.encoding)).decode(config.encoding)

    def _write_flush_buffer(self):
        self.serial.flushInput()
        self.serial.flushOutput()

    def write_reset(self):
        """
        write_reset
        sets all pins to off
        """
        reply = self.write_write_plus_read_until(f"r")
        if reply != "r":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

    def write_digital(self, pin: int, value: int, resistor: str = None):
        """
        write digital
        Turn GPIO pin on or off

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0, ..., 28]
        value: int
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
        reply = self.write_write_plus_read_until(f"d{pin:02}o{resistor}{value}")
        if reply != "d":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        # update pin status
        if value == 1:
            self.pins[pin] = PinStatus.DIGITAL_ON
        else:
            self.pins[pin] = PinStatus.DIGITAL_OFF

    def read_digital(self, pin: int, resistor: str = None) -> int:
        """
        read_digital

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0, ..., 28]
        resistor:
            'n': No resistor, 'u': pull up, 'd': pull down
            range: ['n', 'u', 'd']

        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        resistor = PicoHardware.validate_digital_resistor(resistor)

        # action
        reply = self.write_write_plus_read_until(f"d{pin:02}i{resistor}")
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
            range: [0, 1, 2, 3, 4]

        Returns
        -------
        value: int
            range: [0, ..., 65535]
        """
        # validation
        PicoHardware.validate_adc_pin(pin)

        # action
        reply = self.write_write_plus_read_until(f"a{pin:02}")
        if reply[0] != "a":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        # update pin status
        self.pins[pin] = PinStatus.ANALOG

        return int(reply[1:])

    def write_pwm(self, pin: int, duty: int, frequency: int):
        """
        write_pwm

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0, ..., 28]
        duty: int
            how much the pulse is 'on'
            range: [0, ..., 65_535]
        frequency:
            PWM pulse frequency
            range: [7, ..., 125_000_000]
        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        PicoHardware.validate_pwm_duty(duty)
        PicoHardware.validate_pwm_frequency(frequency)

        # action
        reply = self.write_write_plus_read_until(f"p{pin:02}{duty:05}{frequency:09}")
        if reply != "p":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

        # update pin status
        self.pins[pin] = PinStatus.PWM

    def write_pwm_pulse(self, pin: int, duty: int, frequency: int, time_: Quantity):
        """
        write_pwm_pulse

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0, ..., 28]
        duty: int
            how much the pulse is 'on'
            range: [0, ..., 65_535]
        frequency:
            PWM pulse frequency
            range: [7, ..., 125_000_000]
        time_:
            time the PWM will remain on
            range: [999 * U("s"), ..., 1 * U("us")]

        """
        # validation
        PicoHardware.validate_GPIO_pin(pin)
        PicoHardware.validate_pwm_duty(duty)
        PicoHardware.validate_pwm_frequency(frequency)
        time_ = PicoHardware.validate_pwm_time(time_)

        # action
        reply = self.write_write_plus_read_until(f"q{pin:02}{duty:05}{frequency:09}{time_}")
        if reply != "q":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        rx_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2 or None]
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
        reply = self.write_write_plus_read_until(message_)
        if reply != "t":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        rx_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2 or None]
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
        reply = self.write_write_plus_read_until(message_)
        if reply[0] != "t":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        rx_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2 or None]
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
        reply = self.write_write_plus_read_until(message_)
        if reply[0] != "t":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        rx_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, 19200, 57600, 115200]
        bits:
            range: [7, 8, 9]
        parity:
            range: [0, 1, 2 or None]
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
        reply = self.write_write_plus_read_until(message_)
        if reply[0] != "t":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        mosi_pin:
            GPIO pin
            range: [0, ..., 28]
        miso_pin:
            GPIO pin
            range: [0, ..., 28]
        cs_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, ..., 115_200]
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
        reply = self.write_write_plus_read_until(message_)
        if reply != "s":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        mosi_pin:
            GPIO pin
            range: [0, ..., 28]
        miso_pin:
            GPIO pin
            range: [0, ..., 28]
        cs_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, ..., 115_200]
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
        reply = self.write_write_plus_read_until(message_)
        if reply[0] != "s":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        mosi_pin:
            GPIO pin
            range: [0, ..., 28]
        miso_pin:
            GPIO pin
            range: [0, ..., 28]
        cs_pin:
            GPIO pin
            range: [0, ..., 28]
        baudrate: int
            range: [9600, ..., 115_200]
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
        reply = self.write_write_plus_read_until(message_)
        if reply[0] != "s":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        sda_pin:
            GPIO pin
            range: [0, ..., 28]
        frequency: int
            range: [400_000]

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)
        PicoHardware.validate_i2c_parameters(frequency, address)

        # action
        reply = self.write_write_plus_read_until(f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}w{message}")
        if reply[0] != "i":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        sda_pin:
            GPIO pin
            range: [0, ..., 28]
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
        reply = self.write_write_plus_read_until(f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}r{amount}")
        if reply[0] != "i":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
        scan_i2c
        Scan all I2C addresses between 0x08 and 0x77 inclusive and return a list of those that respond.

        Parameters
        ----------
        i2c_id:
            range: [0, 1]
        scl_pin:
            GPIO pin
            range: [0, ..., 28]
        sda_pin:
            GPIO pin
            range: [0, ..., 28]
        frequency: int
            range: [400_000]

        Returns
        -------
        message:

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)

        # action
        reply = self.write_write_plus_read_until(f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}s")
        if reply[0] != "i":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

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
            range: [0, ..., 28]
        sda_pin:
            GPIO pin
            range: [0, ..., 28]
        frequency: int
            range: [400_000]

        """
        # validation
        PicoHardware.validate_i2c_pins(i2c_id, scl_pin, sda_pin)
        PicoHardware.validate_i2c_parameters(frequency, address)

        # action
        message_ = f"i{i2c_id}{scl_pin:02}{sda_pin:02}{frequency:06}b{amount:03}{message}"
        reply = self.write_write_plus_read_until(message_)
        if reply[0] != "i":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")

        # update pin status
        self.pins[scl_pin] = PinStatus.I2C
        self.pins[sda_pin] = PinStatus.I2C

        return reply[1:]