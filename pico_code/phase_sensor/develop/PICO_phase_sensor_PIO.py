"""
Phase sensor code:

This code runs on the Rasberry Pi Pico.
The phase sensor consists of one or more SparkFun Line Sensor Breakout - QRE1113 (Digital)
[https://www.sparkfun.com/products/9454] in a line with clear PTFE or PFA tubing running a few millimeters in front of the
sensor.
The QRE1113 is an IR-LED (12 mW, 940 nm) and IR sensitive phototransistor, when powered the LED emits light which will
reflect of the tubing and liquid or gas in the tubing. Depending on the phase, the amount of light reflected will change
which will change the resistance of the phototransistor.

Operation:
The sensor works by charging the capacitor (10nF) to 3.3V through the OUT connection, then measuring the time it takes the
capacitor to drain as electricity from the capacitor leaves through the phototransistor.

PIO states machines were used to get accurate timing of capacitor draining, as it is quite quick. Additionally, state machines
provides the ability to simultaneous measure 8 sensors at once, given that the pico has 8 state machines.
The state machines run at 125 MHz (8 ns per cycle) and the time loop is two cycles so (16 ns accuracy is expected).


High level steps of code:
1) define PIO states machines
2) define UART connection to master computer
3) define interrupt (master computer can stop measurement)
3) wait for "run" message from master computer
4) when "run" message received: run state machines and start sending data over UART
4*) if interrupt received from master computer, stop measurements and go into "standby" state. (wait for "run" to be sent again)

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
    DTR/RTS         Any GPIO (GPIO_2)    RTS: Request to send (1:no request, 0: request - not sure)
    CTS             (not used currently)  CTS: Clear to send (1: ready, 0: not ready - not sure)

Parameters:
    * Pins for sensors: provide the set of pins in main() to the
    * UART object ID
    * Pin for interrupt

"""

from time import time, sleep
from rp2 import PIO, asm_pio
from machine import Pin, UART

# Too short of a charge_time wont charge the capacitor enough
# Too long is fine but it slows down measurement rate.
charge_time = int(125_000_000 * 0.001)
count_down = 1_000_000 # Don't change


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
        self.num_sensor = len(pin_list)
        self.sensors = []
        for i, pin in enumerate(self.pins):
            self.sensors.append(reflect_ir(i, pin))

    def measure(self):
        data = [0] * self.num_sensor

        # start measurement
        for sensor in self.sensors:
            sensor._put()

        # read data out
        for i, sensor in enumerate(self.sensors):
            data[i] = sensor._read() # read is blocking (will wait till measurement done)

        return data

    def deactivate(self):
        for sensor in self.sensors:
            sensor.deactivate()


def stop_interrupt(pin):
    global state

    if state != "standby":
        state = "standby"


def main():
    # Initialize state machines
    pins = [16, 17, 18, 19]
    sen_array = reflect_ir_array(pins)

    # Initialize UART
    uart = UART(0, baudrate=19200, bits=8, parity=0, stop=1)
    global state
    state = "standby"
    print("standby")

    # Initialize interrupt
    pin_interrupt = Pin(2, machine.Pin.IN)
    pin_interrupt.irq(trigger=machine.Pin.IRQ_RISING, handler=stop_interrupt)

    while True:

        # wait for command "run"
        while state == "standby":
            print("standby")
            message = uart.read(1)
            print(message)
            if message != None:
                if message == b"r":
                    state = "run"
                    print("running")
                    uart.write("r" + "\n")
                    break
                else:
                    uart.write("Invald message sent" + str(message) + "\n")

            sleep(1)

        # start taking data
        while state == "run":
            data = sen_array.measure()
            uart.write(str(time()) + "+" + str(data) + "\n")
            mes = uart.read(1)
            if mes == "e":
                break

        # When interrupt received
        print("standby")
        sen_array.deactivate()


def main_no_comm():
    """
    No UART communication
    """
    pins = [16, 17, 18, 19]
    sen_array = reflect_ir_array(pins)

    while True:
        data = sen_array.measure()
        print(data)


if __name__ == '__main__':
    main()



