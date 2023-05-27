"""
Phase sensor code:

This code runs on the Rasberry Pi Pico.
The phase sensor consists of one or more SparkFun Line Sensor Breakout - QRE1113 (Digital)
[https://www.sparkfun.com/products/9454] in a line with clear PTFE or PFA tubing running a few millimeters in front of the
sensor.
The QRE1113 is an IR-LED (12 mW, 940 nm) and IR sensitive phototransistor, when powered the LED emits lights which will
reflect of the tubing and liquid or gas in the tubing. Depending on the phase, the amount of lights reflected will change
which will change the resistance of the phototransistor.

Sensor Operation:
The sensor works by charging the capacitor (10nF) to 3.3V through the OUT connection, then measuring the time it takes the
capacitor to drain as electricity from the capacitor leaves through the phototransistor.

PIO states machines were used to get accurate timing of capacitor draining, as it is quite quick. Additionally, state machines
provides the ability to simultaneous measure 8 sensors at once, given that the pico has 8 state machines.
The state machines run at 125 MHz (8 ns per cycle) and the time loop is two cycles so (16 ns timing accuracy is expected).
Max sample rate is ~300 Hz

High level steps of code:
1) define PIO states machines
2) define UART connection to master computer
3) start infinite loop:
    3-1) Read from UART
    3-2-1) if None: do nothing
    3-2-2) if "r": take measurement, and send reference_data back over UART
    3-2-3) if "s": send "s" back over UART - just used to check the PICO/communication is running correctly


Wiring
    **Pico**        **Line sensor**
    3.3 V           VCC
    GND             GND
    Any GPIO Pin    OUT

    **FT232R**      **Pico**
    RX              TX (GPIO_0, UART0)
    TX              RX (GPIO_1, UART0)
    GND             GND
    VCC             (don't connect, can kill Pico if 5 V)
    DTR/RTS         (not used currently)  RTS: Request to send (1:no request, 0: request - not sure)
    CTS             (not used currently)  CTS: Clear to send (1: ready, 0: not ready - not sure)

Parameters:
    * Pins for sensors: provide the set of pins in main() to the
    * UART object ID

"""

from time import time, sleep, ticks_ms, ticks_us
from rp2 import PIO, asm_pio, StateMachine
from machine import Pin, UART

# Too short of a charge_time wont charge the capacitor enough
# Too long is fine but it slows down measurement rate.
charge_time = const(100_000)
count_down = const(1_000_000) # Don't change


@asm_pio(set_init=PIO.OUT_LOW)
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

    # This section times how many cycles it takes to get back to zero
    set(pindirs, 0)  # set pins to input
    set(x, 1)  # the loop breaks when x is set to zero, which happens when jump pin = 0
    label("timeloop")  # loop counts down till pins = 0 again
    jmp(pin, "filp")  # jumps over set x=0 when pin = 1 and allows x to be set to zero when pin = 0
    set(x, 0)
    label("filp")
    jmp(not_x, "dataout")  # breaks out of loop to export count
    jmp(y_dec, "timeloop")  # counter

    # Output countdown timer
    label("dataout")
    mov(isr, y)
    push()


class reflect_ir:
    def __init__(self, state_machine, pin):
        self.pin = Pin(pin, Pin.OUT)
        self.sm = StateMachine(state_machine, reflect_measurement, freq=125_000_000, set_base=self.pin,
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
        self.num_sensor = len(pin_list)
        self.sensors = []
        for i, pin in enumerate(self.pins):
            self.sensors.append(reflect_ir(i, pin))

    def measure(self):
        data = [0] * self.num_sensor

        # start measurement
        for sensor in self.sensors:
            sensor._put()

        # read reference_data out
        for i, sensor in enumerate(self.sensors):
            data[i] = sensor._read() # read is blocking (will wait till measurement done)

        return data

    def deactivate(self):
        for sensor in self.sensors:
            sensor.deactivate()

@micropython.native
def main():
    # Initialize state machines
    pins = [16, 17, 18, 19]
    sen_array = reflect_ir_array(pins)

    # Initialize UART
    uart = UART(0, baudrate=57600, bits=8, parity=0, stop=1)
    print("Running")

    # Get mean
    n = 50
    num =len(pins)
    mean = [0] * num
    for _ in range(n):
        data = sen_array.measure()
        for i in range(num):
            mean[i] = mean[i] + data[i]

    for i in range(num):
        mean[i] = int(mean[i]/n)

    # main loop (infinite loop)
    while True:
        # communication
        message = uart.read(1)

        if message is not None:
            if message == b"r":
                # taking reference_data
                data = sen_array.measure()
                for i in range(num):
                    data[i] = int(data[i]/mean[i]*1000)

                # send reference_data
                # print(reference_data)
                uart.write("d" + str(ticks_us()) + "+" + str(data) + "\n")
                continue

            # Not nessacary but, provides a way to check the phase sensor is working correctly
            if message == b"s":
                uart.write("s" + "\n")
                continue

        sleep(0.005)

@micropython.native
def main_no_comm():
    """
    No UART communication
    """
    pins = [16, 17, 18, 19]
    sen_array = reflect_ir_array(pins)

    n = 100
    start = ticks_us()
    for _ in range(n):
        sen_array.measure()

    end = ticks_us()
    print(n/(end-start)*1_000_000)

    num =len(pins)
    mean = [0] * num
    for _ in range(n):
        data = sen_array.measure()
        for i in range(num):
            mean[i] = mean[i] + data[i]

    for i in range(num):
        mean[i] = mean[i]/n

    n = 100
    start = ticks_us()
    for _ in range(n):
        data = sen_array.measure()
        for i in range(num):
            data[i] = int(data[i]/mean[i]*1000)

    end = ticks_us()
    print(n/(end-start)*1_000_000)

    sleep(1)
    std = [0]*num
    for _ in range(1_000):
        data = sen_array.measure()
        for i in range(num):
            data[i] = int(data[i]/mean[i]*1000)
        print(data)
        #sleep(0.05)



if __name__ == '__main__':
    main()
    # main_no_comm()



