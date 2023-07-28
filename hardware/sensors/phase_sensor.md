

## IR detectors
SparkFun Line Sensor Breakout - QRE1113 (Analog)
https://www.sparkfun.com/products/9453

Output is the middle point in a voltage divider:

VCC --[10K resistor]-->OUT--[photosensor]-->GND

OUT voltage lowers when less light is reflected back.

## ADC

data sheet: https://cdn-shop.adafruit.com/datasheets/MCP3008.pdf

10 bit, 1024

https://github.com/luxedo/RPi_mcp3008/blob/master/mcp3008.py
```python
    def _read_single(self, mode):
        '''
        Returns the value of a single mode reading
        '''
        if not 0 <= mode <= 15:
            raise IndexError('Outside the channels scope, please use: 0, 1 ..., 7')
        request = [0x1, mode << 4, 0x0] # [start bit, configuration, listen space]
        _, byte1, byte2 = self.xfer2(request)
        value = (byte1%4 << 8) + byte2
        return value


```


| Diff | D2  | D1  | D0  | Input        | channel |
|------|-----|-----|-----|--------------|---------|
| 1    | 0   | 0   | 0   | single-ended | CH0     |
| 1    | 0   | 0   | 1   | single-ended | CH1     |
| 1    | 0   | 1   | 0   | single-ended | CH2     |
| 1    | 0   | 1   | 1   | single-ended | CH3     |
| 1    | 1   | 0   | 0   | single-ended | CH4     |
| 1    | 1   | 0   | 1   | single-ended | CH5     |
| 1    | 1   | 1   | 0   | single-ended | CH6     |
| 1    | 1   | 1   | 1   | single-ended | CH7     |

Initiating communication with either device is done by bringing the CS line low


FT232H USB
https://github.com/eblot/pyftdi

