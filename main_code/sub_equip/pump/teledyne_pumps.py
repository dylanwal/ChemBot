"""
This code is for the Teledyne Isco pump syringe pump.


"""

"""

all communication starts with [CR] (carriage return)
respond time: within 200 ms
frame = destination\acknowledgement\message source\length\message\checksum\[CR]
    destination      | 1-digit unit identification number of the instrument to receive the message
    acknowledgement  | one character
            E: error, resend the message immediately - network controller only
            B: busy, resend message at next polling
            R: message recived
    message source   | unit ID of the unit that originated the message (if no message, add 'space')
    length           | length of the message in 2 digit Maximum length is 256, with 256 being represented by a 00.
    message          | area where the actual information is located. The maximum length is 256 characters long.
    checksum         | a 2 digit hexadecimal number
            all characters are converted to the ASCII equivalent and added, except for the checksum. (include space)
    [CR]             |

bit to decmial
65 = int(b'1000001',2)
decmial to ascii
'A' = chr(65)


"""
from machine import UART, Pin
from utime import ticks_ms, sleep
import ubinascii


def timeout_read(_uart, timeout_ms=20):
    now = ticks_ms()
    value = b''
    while True:
        if (ticks_ms() - now) > timeout_ms:
            break
        if _uart.any():
            value = value + _uart.read(1)
            now = ticks_ms()
    return value


def polling(_uart):
    """
    This function is to determine what controls we have acess to.
    para: _uart: uart object
    return: active: list with active pump ids
    """
    active = []
    for i in range(2):  # looping over pump
        responce = 0
        for ii in range(3):  # giving each pump 3 attempts to reply
            message = str(i + 1) + "R"  # destination + acknowledgement
            message = add_checksum(message)
            message = message + '\r'

            if i == 0:  # A [CR] must start the network.
                message = '\r' + message

            # ping pump
            message = '\r1R5D\r'
            print(message)
            _uart.write(message)

            # wait for reply
            responce = timeout_read(_uart, timeout_ms=20)
            print(responce)

            if responce:
                active.append(i + 1)
                break
            sleep(0.1)

    return active


def num_to_hex(n):
    """
    Given a number between 0-15 return sting of hexaecimal
    """
    if n < 0:
        return "error"
    elif n < 16:
        if n < 10:
            return str(n)
        if n == 10:
            return "A"
        if n == 11:
            return "B"
        if n == 12:
            return "C"
        if n == 13:
            return "D"
        if n == 14:
            return "E"
        if n == 15:
            return "F"
    else:
        return "error"


def add_checksum(message_in):
    """
    Given a message the check sum will be added to the end the
    message + checksum will be returned
    """
    dec_list = [int(ubinascii.hexlify(i), 16) for i in message_in]
    checksum_dec = 256 - sum(dec_list) % 256
    modulo = checksum_dec % 16
    divider = int((checksum_dec - modulo) / 16)
    return message_in + num_to_hex(divider) + num_to_hex(modulo)


def main():
    file = open("comm.txt", "a")

    # Setup
    uart = UART(0, 9600, bits=8, parity=None, stop=0)
    led = Pin(25, Pin.OUT)

    # polling connected pump
    pump_id = polling(uart)
    print(pump_id)
    if pump_id:
        file.write(str(pump_id))
        # print(f"These are the connected pump ids: {pump_id}")

    file.close()

    # sending a message


#     message = 'R'
#     message = add_checksum(message)
#     message = message + '\r'
#     uart.write(message)
#     reply = uart.read()
#     print(reply)

if __name__ == "__main__":
    main()

