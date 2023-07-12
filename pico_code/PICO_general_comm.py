"""
General Communication Code:

This code is used on multipurpose Picos.
It takes commands over USB and based on the message it receives it can run various different functions.


Wiring:
    **PC**                  **Pico**
    usb                     usb

Notes:
* Every sent from PC should termate with '\n'.

"""
import time

import select
import sys
import machine

__version__ = "0.0.2"

# a list to keep record of what's going on
pins = [["", None]] * 28


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
                do_stuff(message)
            except Exception as e:
                print(str(type(e)) + " " + str(e))


def digital(message: str):
    """
    Turn pin on or off

    Parameters
    ----------
    message:
        format: "d##__#"
        'd' is to specify digital
        '##' GPIO pin (for single digit pins add leading zero. eg: 01)
        '_' input or output = [i, o]
        '_' add pull up or pull down resistor [n, u, d] n: None u: pull up; d: pull down; default is None
        '#' value [0, 1] (output only)

    Returns
    -------
    reply: "d" or "d#"


    Examples
    --------
    >>> "d02on1"
        digitial pin:2 output resistor:n value:1

    """
    # process message
    pin = int(message[1:3])  # GPIO pins: 0 - 28
    mode = message[3]  # i or o only
    if message[4] == "d":
        resistor = machine.Pin.PULL_DOWN
    elif message[4] == "u":
        resistor = machine.Pin.PULL_UP
    else:
        resistor = None
    value = int(message[5])  # 0 or 1 only

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[pin]
    if prior_pin[0] == message[:4]:
        p = prior_pin[1]
    else:
        if mode == "i":
            p = machine.Pin(pin, mode=machine.Pin.IN, pull=resistor)
        else:
            p = machine.Pin(pin, mode=machine.Pin.OUT, pull=resistor)
        pins[pin] = [message, p]  # save pin

    # do something
    if mode == "i":
        print("d" + str(p.value()))
    else:
        p.value(value)
        print("d")


def analog(message: str):
    """
    Get analog reading
    GPIO pins: 26, 27, 28 or ADC - 0, 1, 2, 3(internal Vsys), 4(internal temp.)

    Parameters
    ----------
    message:
        format: "a##"
        'a' is to specify analog
        '##' GPIO pin (for single digit pins add leading zero. eg: 01)

    Returns
    -------
    reply: "a65535"
        '65535' range: 0-65535


    Examples
    --------
    >>> "a02"
        analog pin:2

    """
    # process message
    pin = int(message[1:3])  # GPIO pins: 0 - 28

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[pin]
    if prior_pin[0] == message[:3]:
        p = prior_pin[1]
    else:
        p = machine.ADC(pin)
        pins[pin] = [message, p]  # save pin

    # do something
    print("a" + str(p.read_u16()))


def pwm(message: str):
    """
    PWM (pulse width modulation)
    GPIO pins: 0 - 15 (over GPIO 15 are alternative GPIO pins for the same channels)

    Parameters
    ----------
    message:
        format: "p##65535125000000"
        'p' is to specify pwm
        '##' GPIO pin (for single digit pins add leading zero. eg: 01)
        '65535' duty cycle, range 0-65535
        '125000000' frequency, range 7Hz to 125Mhz

    Returns
    -------
    reply: "p"

    Examples
    --------
    >>> "p0232767000000300"
        pwm pin:2 33767/65535 (50% duty) 300 Hz

    """
    # process message
    pin = int(message[1:3])
    duty = int(message[3:8])
    freq = int(message[8:])

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[pin]
    if prior_pin[0] == message[:3]:
        p = prior_pin[1]
    else:
        p = machine.PWM(machine.Pin(pin))
        pins[pin] = [message, p]  # save pin

    # do something
    if freq == 0 or duty == 0:
        p.deinit()
        machine.Pin(pin, machine.Pin.OUT).value(0)  # turn off pwm
    else:
        p.freq(freq)
        p.duty_u16(duty)
    print("p")


def pwm_pulse(message: str):
    """
    PWM (pulse width modulation) pulse
    GPIO pins: 0 - 15 (over GPIO 15 are alternative GPIO pins for the same channels)

    Parameters
    ----------
    message:
        format: "q##65535125000000_###"
        'q' is to specify pwm pulse
        '##' GPIO pin (for single digit pins add leading zero. eg: 01)
        '65535' duty cycle, range 0-65535
        '125000000' frequency, range 7Hz to 125Mhz
        "_" time range ["s", "m", "u"] "s" seconds, "m" milliseconds, "u" microseconds (limit to 10 sec; watchdog limit)
        "###" time value

    Returns
    -------
    reply: "q"

    Examples
    --------
    >>> "q0232767000000300s001"
        pwm_pulse pin:2 33767/65535 (50% duty) 300 Hz pulse for 1 sec

    """
    # process message
    pin = int(message[1:3])
    duty = int(message[3:8])
    freq = int(message[8:17])
    scale = message[17]
    time_ = int(message[18:])

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[pin]
    if prior_pin[0] == message[:3]:
        p = prior_pin[1]
    else:
        p = machine.PWM(machine.Pin(pin))
        pins[pin] = [message, p]  # save pin

    # do something
    p.freq(freq)
    p.duty_u16(duty)
    if scale == "s":
        time.sleep(time_)
    elif scale == "m":
        time.sleep_ms(time_)
    elif scale == "u":
        time.sleep_us(time_)
    p.deinit()
    machine.Pin(pin, machine.Pin.OUT).value(0)  # turn off pwm
    print("q")


def serial(message: str):
    """
    UART (serial bus)
    UART0 can be mapped to GPIO 0/1, 12/13 and 16/17, and UART1 to GPIO 4/5 and 8/9

    Parameters
    ----------
    message:
        format: "t#txrx115200###a_"
        '#' UART id
        'tx' GPIO pin (for single digit pins add leading zero. eg: 01)
        'rx' GPIO pin (for single digit pins add leading zero. eg: 01)
        '115200' baud rate common values [9600, 19200, 57600, 115200]
        '#' bits number of bits per character, 7, 8 or 9 (typically 8)
        '#' parity 0 (even) or 1 (odd) or 2 (None)
        '#' number of stop bits, 1 or 2
        'a' action 'r' (readline), 's' (read), 'w' (write), 'b' (write + readline)
        '_' if 'a'='s' number of bits to read // if 'w' or 'b' the message.

    Returns
    -------
    reply: "t" + "message"

    Examples
    --------
    >>> "t00001009600821wreply__r__"
        serial id:0 tx:00 rx:01 baudrate:9600 bits:8 parity:None write message: reply\r

    """
    # process message
    uart_id = int(message[1])
    tx_pin = int(message[2:4])
    rx_pin = int(message[4:6])
    baudrate = int(message[6:12])
    bits = int(message[12])
    parity = int(message[13])
    if parity == 2:
        parity = None
    stop = int(message[14])

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[tx_pin]
    if prior_pin[0] == message[:14]:
        p = prior_pin[1]
    else:
        p = machine.UART(uart_id, baudrate=baudrate, tx=machine.Pin(tx_pin), rx=machine.Pin(rx_pin), bits=bits,
                         parity=parity, stop=stop, timeout=1000)
        pins[tx_pin] = [message[:14], p]  # save pin
        pins[rx_pin] = [message[:14], p]  # save pin

    # do something
    action = message[15]
    if action == "r":
        print("t" + encode_message(p.readline()))
    elif action == "s":
        amount = int(message[15:])
        print("t" + encode_message(p.read(amount)))
    elif action == "w":
        p.write(decode_message(message[15:]))
        print("t")
    else:
        p.write(decode_message(message[15:]))
        print("t" + encode_message(p.readline()))


def encode_message(text: str):
    return text.replace("\n", "__n__").replace("\r", "__r__")


def decode_message(text: str):
    return text.replace("__n__", "\n").replace("__r__", "\r")


def spi(message: str):
    """
    SPI – a Serial Peripheral Interface bus protocol

    Parameters
    ----------
    message:
        format: "s#######115200###csa_"
        '#' spi id
        '##' sck_pin GPIO pin (for single digit pins add leading zero. eg: 01)
        '##' mosi_pin GPIO pin (for single digit pins add leading zero. eg: 01)
        '##' miso_pin GPIO pin (for single digit pins add leading zero. eg: 01)
        '115200' baud rate common values [9600, 19200, 57600, 115200]
        '#' bits number of bits per character, 7, 8 or 9 (typically 8)
        '#' polarity  0 or 1, and is the level the idle clock line sits at.
        '#' phase 0 or 1 to sample data on the first or second clock edge respectively
        'cs' cs_pin GPIO pin (for single digit pins add leading zero. eg: 01)
        'a' action 'r' (read), 'w' (write), 'b' (write + read)
        '_' if 'a'='r' number of bits to read // if 'w' or 'b' the message. (first 3 are number of bits read)

    Returns
    -------
    reply: "s" + "message"

    Examples
    --------
    >>> "s006070400960080000wreply__r__"
        serial id:0 sck_pin:06 mosi_pin:07 miso_pin:04 baudrate:9600 bits:8 polarity:0 phase:0 cs_pin:0
        write message: reply\r

    """
    # process message
    spi_id = int(message[1])
    sck_pin = int(message[2:4])
    mosi_pin = int(message[4:6])
    miso_pin = int(message[6:8])
    baudrate = int(message[8:14])
    bits = int(message[14])
    polarity = int(message[15])
    phase = int(message[16])

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[sck_pin]
    if prior_pin[0] == message[:16]:
        p = prior_pin[1]
    else:
        p = machine.SPI(spi_id, baudrate=baudrate, sck=machine.Pin(sck_pin), mosi=machine.Pin(mosi_pin),
                        miso=machine.Pin(miso_pin), bits=bits, polarity=polarity, phase=phase, timeout=1000)
        pins[sck_pin] = [message[:16], p]  # save pin
        pins[mosi_pin] = [message[:16], p]  # save pin
        pins[miso_pin] = [message[:16], p]  # save pin

    cs_pin = int(message[17:19])
    prior_pin = pins[cs_pin]
    if prior_pin[0] == cs_pin:
        cs_p = prior_pin[1]
    else:
        cs_p = machine.Pin(cs_pin, mode=machine.Pin.OUT)
        pins[sck_pin] = [cs_pin, cs_p]  # save pin

    # do something
    action = message[20]
    cs_p.value(1)
    if action == "r":
        amount = int(message[21:])
        print("s" + encode_message(p.read(amount)))
    elif action == "w":
        p.write(decode_message(message[21:]))
        print("s")
    else:
        amount = int(message[21:24])
        reply = p.read(amount, decode_message(message[15:]))
        print("s" + encode_message(reply))

    cs_p.value(0)


def i2c(message: str):
    """
    I2C – a two-wire serial protocol

    Parameters
    ----------
    message:
        format: "i#####400000a_"
        '#' i2c id
        '##' scl GPIO pin (for single digit pins add leading zero. eg: 01)
        '##' sda GPIO pin (for single digit pins add leading zero. eg: 01)
        '400000' frequency
        'a' action 'r' (readline), 's' (read), 'w' (write), 'b' (write + readline)
        '_' if 'a'='s' number of bits to read // if 'w' or 'b' the message.

    Returns
    -------
    reply: "i" + "message"

    Examples
    --------
    >>> "i00001009600821wreply__r__"
        serial id:0 tx:00 rx:01 baudrate:9600 bits:8 parity:None write message: reply\r

    """
    # process message
    i2c_id = int(message[1])
    scl_pin = int(message[2:4])
    sda_pin = int(message[4:6])
    freq = int(message[6:12])

    # check for existing hardware or initialize it
    global pins
    prior_pin = pins[scl_pin]
    if prior_pin[0] == message[:12]:
        p = prior_pin[1]
    else:
        p = machine.I2C(i2c_id, scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin), freq=freq, timeout=1000)
        pins[scl_pin] = [message[:12], p]  # save pin
        pins[sda_pin] = [message[:12], p]  # save pin

    # do something
    action = message[13]
    address = int(message[14:16])
    if action == "r":
        amount = int(message[16:])
        print("i" + encode_message(p.readfrom(address, amount)))
    elif action == "s":
        print("i" + encode_message(p.scan()))
    elif action == "w":
        p.writeto(address, decode_message(message[16:]))
        print("i")
    else:
        amount = int(message[16:19])
        p.writeto(decode_message(message[19:]))
        print("i" + encode_message(p.readfrom(amount)))


def do_stuff(message: str):
    if message[0] == "d":
        digital(message)
    elif message[0] == "a":
        analog(message)
    elif message[0] == "p":
        pwm(message)
    elif message[0] == "q":
        pwm_pulse(message)
    elif message[0] == "s":
        spi(message)
    elif message[0] == "i":
        i2c(message)
    elif message[0] == "t":
        serial(message)
    elif message[0] == "r":
        reset()
        print("r")
    elif message == "v":
        print("v" + __version__)
    else:
        print("Invalid message:" + str(message))


if __name__ == "__main__":
    main()
