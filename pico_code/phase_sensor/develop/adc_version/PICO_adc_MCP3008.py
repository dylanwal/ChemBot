from machine import Pin, SPI, PWM
from time import sleep, sleep_ms


class MCP3008:

    def __init__(self, spi, cs, ref_voltage=5):
        """
        Create MCP3008 instance

        Args:
            spi: configured SPI bus
            cs:  pin to use for chip select
            ref_voltage: r
        """
        self.cs = cs
        self.cs.value(1)  # ncs on
        self._spi = spi
        self._out_buf = bytearray(3)
        self._out_buf[0] = 0x01
        self._in_buf = bytearray(3)
        self._ref_voltage = ref_voltage

    def reference_voltage(self) -> float:
        """Returns the MCP3xxx's reference voltage as a float."""
        return self._ref_voltage

    def read(self, pin, is_differential=False):
        """
        read a voltage or voltage difference using the MCP3008.

        Args:
            pin: the pin to use
            is_differential: if true, return the potential difference between two pins,


        Returns:
            voltage in range [0, 1023] where 1023 = VREF (3V3)

        """

        self.cs.value(0)  # select
        self._out_buf[1] = ((not is_differential) << 7) | (pin << 4)
        self._spi.write_readinto(self._out_buf, self._in_buf)
        self.cs.value(1)  # turn off
        return ((self._in_buf[1] & 0x03) << 8) | self._in_buf[2]

    def read_set(self, pin_set, is_differential=False):
        """
        read a voltage or voltage difference using the MCP3008.

        Args:
            pin: the pin to use
            is_differential: if true, return the potential difference between two pins,


        Returns:
            voltage in range [0, 1023] where 1023 = VREF (3V3)

        """
        data = [0] * len(pin_set)
        for i, pin in enumerate(pin_set):
            data[i] = self.read(pin, is_differential)

        return data

    def read_many(self, pin_set, is_differential=False, n: int = 3):
        """
        read a voltage or voltage difference using the MCP3008.

        Args:
            pin: the pin to use
            is_differential: if true, return the potential difference between two pins,


        Returns:
            voltage in range [0, 1023] where 1023 = VREF (3V3)

        """
        value = 0
        for _ in range(n):
            value += self.read(pin, is_differential)
            sleep(0.01)

        return int(value / n)

    def read_set_many(self, pin_set, is_differential=False, n: int = 3):
        """
        read a voltage or voltage difference using the MCP3008.

        Args:
            pin: the pin to use
            is_differential: if true, return the potential difference between two pins,


        Returns:
            voltage in range [0, 1023] where 1023 = VREF (3V3)

        """
        data = [0] * len(pin_set)
        for _ in range(n):
            for i, pin in enumerate(pin_set):
                data[i] = self.read(pin, is_differential)

        for i in range(len(data)):
            data[i] = int(data[i] / n)

        return data


def main():
    spi = SPI(1, sck=Pin(14), mosi=Pin(15), miso=Pin(12), baudrate=115_200)
    cs = Pin(13, Pin.OUT)
    cs.value(1)  # disable chip at start

    leds = Pin(0, Pin.OUT)
    leds.value(1)
    #     leds = PWM(leds)
    #     leds.freq(100_000)
    #     duty = int(0.8 * 65535)
    #     leds.duty_u16(duty)

    chip = MCP3008(spi, cs)

    try:
        reads = [0, 1, 2, 3]
        for _ in range(5000):
            print(chip.read(0, True))
            sleep(0.05)

    finally:
        leds = Pin(0, Pin.OUT, pull=Pin.PULL_DOWN)
        leds.value(0)


if __name__ == "__main__":
    main()
