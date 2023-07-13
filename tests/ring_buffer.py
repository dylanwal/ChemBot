import pathlib
import time

from chembot.equipment.sensors.buffer_ring import BufferRing


def main():
    delay = 1/100000000  # Hz
    path = pathlib.Path(__file__).parent
    b = BufferRing(path, "int", (5000, 1), 1000)

    for i in range(50_000):
        b.add_data(i)
        if i % 1000 == 0:
            time.sleep(delay)
        #     print(i)

    b.done()


if __name__ == "__main__":
    main()
