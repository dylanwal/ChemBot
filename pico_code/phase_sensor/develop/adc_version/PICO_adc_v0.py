"""
ads1115

"""

from utime import sleep
from machine import I2C, Pin
from micropython import const
import struct

_ADS1X15_POINTER_CONVERSION = const(0x00)
_ADS1X15_POINTER_CONFIG = const(0x01)
_ADS1X15_CONFIG_OS_SINGLE = const(0x8000)
_ADS1X15_CONFIG_MUX_OFFSET = const(12)
_ADS1X15_CONFIG_COMP_QUE_DISABLE = const(0x0003)

# Gains
GAINS = {
    2/3: 0x0000, # 6.144 V
    1: 0x0200,   # 4.096 V
    2: 0x0400,   # 2.048 V
    4: 0x0600,   # 1.024 V
    8: 0x0800,   # 0.512 V
    16: 0x0A00,  # 0.256 V
}

# OPERATING MODES
CONTINUOUS = const(0x0000)
SINGLE = const(0x0100)

# Data sample rates (samples per second)
SAMPLE_RATE = {
    8: 0x0000,
    16: 0x0020,
    32: 0x0040,
    64: 0x0060,
    128: 0x0080,
    250: 0x00A0,
    475: 0x00C0,
    860: 0x00E0,
}

class ADS1115:
    def __init__(self, i2c, gain=1, data_rate=128, mode=SINGLE, address=0x48):
        self._last_pin_read = None
        self.buf = bytearray(3)
        self._data_rate = self._gain = self._mode = None
        self.gain = gain
        self.data_rate = data_rate
        self.mode = mode
        self.i2c_device = i2c
        self.address = address

    @property
    def gain(self):
        """The ADC gain."""
        return self._gain

    @gain.setter
    def gain(self, gain):
        possible_gains = list(GAINS.keys())
        if gain not in possible_gains:
            raise ValueError("Gain must be one of: {}".format(possible_gains))
        self._gain = gain


    def read(self, pin, differential=False):
        """I2C Interface for ADCs reads.
        params:
            :param pin: individual or differential pin.
            :param bool differential: single-ended or differential read.
        """
        pin = pin if differential else pin + 0x04
        return self._read(pin)


    def _conversion_value(self, raw_adc):
        """Subclasses should override this function that takes the 16 raw ADC
        values of a conversion result and returns a signed integer value.
        """
        raw_adc = raw_adc.to_bytes(2, "big")
        value = struct.unpack(">h", raw_adc)[0]
        return value

    def _read(self, pin):
        """Perform an ADC read. Returns the signed integer result of the read."""
        # Immediately return conversion register result if in CONTINUOUS mode
        # and pin has not changed
        if self.mode == CONTINUOUS and self._last_pin_read == pin:
            return self._conversion_value(self.get_last_result(True))

        # Assign last pin read if in SINGLE mode or first sample in CONTINUOUS mode on this pin
        self._last_pin_read = pin

        # Configure ADC every time before a conversion in SINGLE mode
        # or changing channels in CONTINUOUS mode
        if self.mode == SINGLE:
            config = _ADS1X15_CONFIG_OS_SINGLE
        else:
            config = 0
        config |= (pin & 0x07) << _ADS1X15_CONFIG_MUX_OFFSET
        config |= GAINS[self.gain]
        config |= self.mode
        config |= SAMPLE_RATE[self.data_rate]
        config |= _ADS1X15_CONFIG_COMP_QUE_DISABLE
        # print(config)
        self._write_register(_ADS1X15_POINTER_CONFIG, config)

        # Wait for conversion to complete
        # ADS1x1x devices settle within a single conversion cycle
        if self.mode == SINGLE:
            # Continuously poll conversion complete status bit
            while not self._conversion_complete():
                pass
        else:
            # Can't poll registers in CONTINUOUS mode
            # Wait expected time for two conversions to complete
            time.sleep(2 / self.data_rate)

        return self._conversion_value(self.get_last_result(False))

    def _conversion_complete(self):
        """Return status of ADC conversion."""
        # OS is bit 15
        # OS = 0: Device is currently performing a conversion
        # OS = 1: Device is not currently performing a conversion
        return self._read_register(_ADS1X15_POINTER_CONFIG) & 0x8000

    def get_last_result(self, fast=False):
        """Read the last conversion result when in continuous conversion mode.
        Will return a signed integer value. If fast is True, the register
        pointer is not updated as part of the read. This reduces I2C traffic
        and increases possible read rate.
        """
        return self._read_register(_ADS1X15_POINTER_CONVERSION, fast)

    def _write_register(self, reg, value):
        """Write 16 bit value to register."""
        self.buf[0] = reg
        self.buf[1] = (value >> 8) & 0xFF
        self.buf[2] = value & 0xFF
        # print("write: " +  str(self.buf))
        self.i2c_device.writeto(self.address, self.buf)

    def _read_register(self, reg, fast=False):
        """Read 16 bit register value. If fast is True, the pointer register
        is not updated.
        """
        # print("r/w :" + str(reg))
        if fast:
            self.i2c_device.readinto(self.buf, end=2)
        else:
            self.i2c_device.writeto(self.address, bytearray([reg]))
            self.i2c_device.readfrom_into(self.address, self.buf)
        # print("read: " + str(self.buf))
        return self.buf[0] << 8 | self.buf[1]

#The MCP4725 has support from 2 addresses
BUS_ADDRESS = [0x62,0x63]

#The device supports a few power down modes on startup and during operation
POWER_DOWN_MODE = {'Off':0, '1k':1, '100k':2, '500k':3}

class MCP4725:
    def __init__(self,i2c, address=BUS_ADDRESS[0], supply_voltage: float = 5) :
        self.i2c=i2c
        self.address=address
        self._writeBuffer=bytearray(2)
        self.supply_voltage = supply_voltage

    def write(self,voltage: float):
        if voltage > self.supply_voltage:
            value=self.supply_voltage
        if voltage < 0:
            voltage=0

        value = int(voltage / self.supply_voltage * 0xFFF)
        value=value & 0xFFF
        self._writeBuffer[0]=(value>>8) & 0xFF
        self._writeBuffer[1]=value & 0xFF
        return self.i2c.writeto(self.address,self._writeBuffer)==2

    def read(self):
        buf=bytearray(5)
        if self.i2c.readfrom_into(self.address,buf) ==5:
            eeprom_write_busy=(buf[0] & 0x80)==0
            power_down=self._powerDownKey((buf[0] >> 1) & 0x03)
            value=((buf[1]<<8) | (buf[2])) >> 4
            eeprom_power_down=self._powerDownKey((buf[3]>>5) & 0x03)
            eeprom_value=((buf[3] & 0x0f)<<8) | buf[4]
            return (eeprom_write_busy,power_down,value,eeprom_power_down,eeprom_value)
        return None

    def config(self,power_down='Off',value=0,eeprom=False):
        buf=bytearray()
        conf=0x40 | (POWER_DOWN_MODE[power_down] << 1)
        if eeprom:
            #store the powerdown and output value in eeprom
            conf=conf | 0x60
        buf.append(conf)
        #check value range
        if value<0:
            value=0
        value=value & 0xFFF
        buf.append(value >> 4)
        buf.append((value & 0x0F)<<4)
        return self.i2c.writeto(self.address,buf)==3

    def _powerDownKey(self,value):
        for key,item in POWER_DOWN_MODE.items():
            if item == value:
                return key

def main():
    i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
    ADC = ADS1115(i2c)
    DAC = MCP4725(i2c)

    leds = Pin(0, Pin.OUT, pull=Pin.PULL_UP)
    leds.value(0)
    sleep(0.1)
    try:
#         n=100
#         first= 0
#         for i in range(100):
#             first += ADC.read(0, differential=False)
#         first = first/n
#         print(first)
#         print(first/32767*5)
        # DAC.write(first/32767*5)
        DAC.write(2.6)

        ADC.gain = 16
        for i in range(1000):
            print(ADC.read(0, differential=True), ADC.read(1, differential=True))
            sleep(0.0001)

    finally:
        leds.value(1)

def single():
    i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
    ADC = ADS1115(i2c)
    DAC = MCP4725(i2c)

    leds = Pin(0, Pin.OUT, pull=Pin.PULL_UP)
    leds.value(0)
    sleep(0.1)
    try:
        ADC.gain = 1
        print(ADC.read(0, differential=False))

    finally:
        leds.value(1)


if __name__ == "__main__":
    main()

"""
2.34V empty
2.6V water
"""
