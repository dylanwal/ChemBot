import sys
import os
import threading
from typing import Protocol


class Equipment(Protocol):

    def activate(self):
        ...

    def action_deactivate(self):
        ...


def activate_multiple_equipment(equipment: list[Equipment]):
    """ blocking """
    threads = [threading.Thread(target=equip.activate) for equip in equipment]

    # start all threads
    for thread in threads:
        thread.start()

    # wait for them all to finish
    try:
        for thread in threads:
            thread.join()

    finally:
        for thread, equip in zip(threads, equipment):
            if thread.is_alive():
                # if any alive; tell them to deactivate
                equip.action_deactivate()

        for thread in threads:
            thread.join()

    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
