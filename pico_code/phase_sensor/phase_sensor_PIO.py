from time import time_ns
from rp2 import PIO, asm_pio
from machine import Pin

charge_time = int(125_000_000 * 0.001)
count_down = 1_000_000


@asm_pio(set_init=rp2.PIO.OUT_LOW)
def reflect_measurement():
    # Pull in "charge capacitor time", and "countdown timer"
    pull()
    mov(x, osr)  # store "charge capacitor time" in x
    pull()
    mov(y, osr)  # store "countdown timer" in y

    # Charge the capacitor
    set(pindirs, 1)  # set pins as output
    set(pins, 1)  # set pins on
    label("onloop")  # loop keeps pin "ON" till x = 0
    jmp(x_dec, "onloop")
    # set(pins, 0)    # set pins off

    # This times how many cycles it takes to get back to zero
    set(pindirs, 0)  # set pins to input
    set(x, 1)  # the loop breaks when x is set to zero, which happends when jump pin = 0
    label("timeloop")  # loop counts down till pins = 0 again
    jmp(pin, "filp")  # jumps over set x=0 when pin = 1 and allows x to be set to zero when pin = 0
    set(x, 0)
    label("filp")
    jmp(not_x, "dataout")  # breaks out of loop to export count
    jmp(y_dec, "timeloop")  # counter

    # Output countdown
    label("dataout")
    mov(isr, y)
    push()


class reflect_ir:
    def __init__(self, state_machine, pin, gas=0, liq=0, dis=0):
        self.pin = Pin(pin, Pin.OUT)
        self.gas = gas
        self.liq = liq
        self.dis = dis
        self.sm = rp2.StateMachine(state_machine, reflect_measurement, freq=125_000_000, set_base=self.pin,
                                   in_base=self.pin, jmp_pin=self.pin)

        self.sm.active(1)

    def _put(self):
        self.sm.put(charge_time)
        self.sm.put(count_down)

    def _read(self):
        return count_down - self.sm.get()

    def deactivate(self):
        self.sm.active(0)
        self.pin.value(0)


class reflect_ir_array:
    def __init__(self, pin_list):
        if len(pin_list) > 8:
            exit("only 8 state machines on the pico.")
        self.pins = pin_list
        self.sensors = []
        for i, pin in enumerate(self.pins):
            self.sensors.append(reflect_ir(i, pin))

    def measure(self):
        data = [0, 0, 0, 0]
        for sensor in self.sensors:
            sensor._put()
        for i, sensor in enumerate(self.sensors):
            data[i] = sensor._read()

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
sen_array = reflect_ir_array(pins)
n = 100
data = [[0, 0, 0, 0]] * n
start = time_ns()
for i in range(n):
    data[i] = sen_array.measure()

end = time_ns()
print(data[1:10])

print((end - start) / 1000 / 1000 / 1000)
print("done")
# sm.active(1)
# sm.put(charge_time)
# sm.put(count_down)
# #print(sm.rx_fifo())
# print(sm.get())
# sm.active(0)
# sm.exec("set(pins,0)")


