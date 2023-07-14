"""
Phase sensor code:

This code runs on the Raspberry Pi Pico.
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
Max sample rate is ~300 Hz; can be less if it takes the capacitor a while to de-energize (140 Hz worst). Can be faster
if you decrease the {charge_time} but then the reference_data may be more noisy.



Wiring
    **Pico**        **Line sensor**
    3.3 V           VCC
    GND             GND
    Any GPIO Pin    OUT

    **PC**         **Pico**
    usb            usb

Parameters:
    * Pins: in main() default: [12, 13, 14, 15, 16, 17, 18, 19]

"""

from rp2 import PIO, asm_pio, StateMachine
import select
import sys
import machine
import array

__version__ = "0.0.1"


def main():
    print("startup")
    reset()
    main_loop()


def reset():
    # set all pins to low right away
    for i in range(28):
        machine.Pin(i, machine.Pin.OUT).value(0)

    # Turn LED on
    machine.Pin(25, machine.Pin.OUT).value(1)


def main_loop():
    # a list to keep record of what's going on
    pins = [12, 13, 14, 15, 16, 17, 18, 19]
    data = array.array('I', [0] * len(pins))
    state_machines = get_state_machines(pins)

    # Set up the poll object
    poll_obj = select.poll()
    poll_obj.register(sys.stdin, select.POLLIN)

    wdt = machine.WDT(timeout=10000)  # 10 sec

    while True:  # infinite loop
        poll_results = poll_obj.poll(10)
        wdt.feed()
        if poll_results:
            message = sys.stdin.readline().strip()
            try:
                do_stuff(message, state_machines, data)
            except Exception as e:
                print(str(type(e)) + " " + str(e))


def do_stuff(message: str, state_machines: list, data: array.array):
    if message[0] == "w":
        number_of_scans = int(message[1:3])
        measure(number_of_scans, state_machines, data)
    elif message[0] == "r":
        # reset()   # it commented out to avoid messing up state machines
        print("r")
    elif message == "v":
        print("v" + __version__)
    else:
        print("Invalid message:" + str(message))


# Too short of a charge_time wont charge the capacitor enough
# Too long is fine but it slows down measurement rate.
charge_time = const(100_000)
count_down = const(1_000_000)  # Don't change


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


def get_state_machines(pins: list[int]) -> list:
    state_machines = []
    for pin in pins:
        pin = machine.Pin(pin, machine.Pin.OUT)
        sm = StateMachine(reflect_measurement, freq=125_000_000, set_base=pin, in_base=pin, jmp_pin=pin)
        sm.active(1)

    return state_machines


def deactivate(state_machines: list, pins: list[int]):
    for sm in state_machines:
        sm.active(0)
    for pin in pins:
        p = machine.Pin(pin, machine.Pin.OUT)
        p.value(0)


def measure(number_of_scans: int, state_machines: list, data: array.array):
    counter = 0
    while counter < number_of_scans:
        _measure(state_machines, data)
        print("w" + ','.join(map(str, data)))


def _measure(state_machines: list, data: array.array):
    # start measurement
    for sm in state_machines:
        sm.put(charge_time)
        sm.put(count_down)

    # read reference_data out
    for i, sm in enumerate(state_machines):
        data[i] = count_down - sm.get()  # read is blocking (will wait till measurement done)


if __name__ == "__main__":
    main()
