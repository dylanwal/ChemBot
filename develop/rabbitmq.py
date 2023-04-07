import os
import sys
import threading
import time

from chembot.rabbitmq._development import Pump, Controller


def main():
    pump_1 = Pump("1")
    pump_2 = Pump("2")
    t = threading.Thread(target=pump_1.activate)
    t2 = threading.Thread(target=pump_2.activate)
    t.start()
    t2.start()

    controller = Controller("1")
    controller.activate()

    messages = ["print", "print", "long", "sish", "close"]
    i = 0
    try:
        while True:
            print(i)
            controller.send(messages[i % len(messages)])
            i += 1
            time.sleep(0.3)

    except KeyboardInterrupt:
        print('Interrupted')

    finally:
        pump_1.deactivate()
        pump_2.deactivate()
        print('deactivate')

        t.join()
        t2.join()
        print("join")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':
    main()
