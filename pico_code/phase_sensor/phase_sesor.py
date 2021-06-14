from machine import Pin
from utime import sleep, ticks_us, ticks_diff, time_ns


class reflect_ir:
    def __init__(self, pin, gas=0, liq=0, dis=0):
        self.pin = pin
        self.gas = gas
        self.liq = liq
        self.dis = dis
        self.sensor = Pin(self.pin, Pin.OUT)
        self.sensor.value(0)

    def measure(self):
        data = 0.000  # place holder
        self.sensor = Pin(self.pin, Pin.OUT)
        self.sensor.value(1)
        sleep(.005)
        self.sensor = Pin(self.pin, Pin.IN)
        start = ticks_us()
        for _ in range(1000):
            if self.sensor.value() == 0:
                data = ticks_diff(ticks_us(), start)
                break
        return data


class reflect_ir_array:
    def __init__(self, pin_list, gas, liq):
        self.pins = pin_list
        self.sensors = []
        for pin, g, l in zip(self.pins, gas, liq):
            self.sensors.append(reflect_ir(pin, g, l))

    def measure(self):
        data = [0, 0, 0, 0]
        for i, sensor in enumerate(self.sensors):
            data[i] = sensor.measure()

        return data

    def measure_norm(self):
        data = [0, 0, 0, 0]
        for i, sensor in enumerate(self.sensors):
            data[i] = (sensor.measure() - sensor.liq) / (sensor.gas - sensor.liq)

        return data

    def measure_phase(self):
        phase = [0, 0, 0, 0]
        for i, sensor in enumerate(self.sensors):
            phase[i] = self.determine_phase(sensor.measure(), sensor.gas, sensor.liq)

        return phase

    @staticmethod
    def determine_phase(value, gas, liq):
        gas_diff = abs(value - gas)
        liq_diff = abs(value - liq)
        if gas_diff < liq_diff:
            return "gas"

        return "liquid"


pins = [16, 17, 18, 19]
gas = [1247, 1280, 2688, 1311]
liq = [1511, 1573, 2734, 1576]
sen_array = reflect_ir_array(pins, gas, liq)
n = 500
data = [[0, 0, 0, 0]] * n
start = time_ns()
for i in range(n):
    data[i] = sen_array.measure()

end = time_ns()

for i in range(n):
    print(data[i])

print((end - start) / 1000 / 1000 / 1000)

print("done")

