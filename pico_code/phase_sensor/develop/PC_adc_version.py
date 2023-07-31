import time

import serial


def encode_message(text: str):
    return text.replace("\n", "__n__").replace("\r", "__r__")


def decode_message(text: str):
    return text.replace("__n__", "\n").replace("__r__", "\r")


def measure(
        s,
        message: str,
        amount: int,
        spi_id: int,
        sck_pin: int,
        mosi_pin: int,
        miso_pin: int,
        cs_pin: int,
        baudrate: int = 115_200,
        bits: int = 8,
        polarity: int = 0,
        phase: int = 0
) -> str:
    # write
    message = f"s{spi_id}{sck_pin:02}{mosi_pin:02}{miso_pin:02}{baudrate:06}{bits}{polarity}{phase}" \
              f"{cs_pin:02}b{amount:03}{message}"
    s.write((encode_message(message) + "\n").encode("UTF-8"))

    # read
    reply = s.read_until()
    reply = decode_message(reply.decode("UTF-8").strip("\n"))

    if reply[0] != "s":
        print(reply)
        reply = s.read(s.in_waiting)
        print(reply)
        raise ValueError("unexpected reply from pico")

    return reply[1:]


def adc_message(pin: int) -> str:
    if not 0 <= pin <= 7:
        raise IndexError('Outside the channels scope, please use: 0, 1 ..., 7')
    data = [0x1, pin << 4, 0x0]  # [start bit, configuration, listen space]
    data = [chr(i) for i in data]
    return "".join(data)


def digital_write(s, pin: int, value: int):
    s.write(f"d{pin:02}od{value}\n".encode())
    reply = s.read_until()
    reply = decode_message(reply.decode("UTF-8").strip("\n"))

    if reply[0] != "d":
        raise ValueError("unexpected reply from pico")


def main():
    s = serial.Serial(port="COM6")
    s.flushOutput()
    s.flushInput()

    digital_write(s, 25, 0)
    time.sleep(1)
    digital_write(s, 25, 1)

    pin = 0
    try:
        digital_write(s, 0, 1)
        data = measure(
            s,
            message=adc_message(pin),
            amount=3,
            spi_id=1,
            sck_pin=14,
            mosi_pin=15,
            miso_pin=12,
            cs_pin=13,
        )
        print(data)

    finally:
        digital_write(s, 0, 0)


if __name__ == "__main__":
    main()
