import sys
import os
import threading
import logging
import time
from typing import Protocol

from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name)


class Equipment(Protocol):
    name = ""

    def activate(self):
        ...

    def action_deactivate(self):
        ...


def activate_multiple_equipment(equipment: list[Equipment]):
    """ blocking """
    threads = [threading.Thread(target=equip.activate, name=equip.name) for equip in equipment]

    # start all threads
    for thread in threads:
        thread.start()

    logger.info(config.log_formatter("UTILS", "", "All threads started"))
    # wait for them all to finish
    try:
        while True:
            for thread in threads:
                thread.join(timeout=1)

    except KeyboardInterrupt:
        logger.info("\n\n\tKeyboardInterrupt raised\n")

    finally:
        logger.info(config.log_formatter("UTILS", "", "Cleaning up threads"))
        for equip in equipment:
            # if any alive; tell them to deactivate
            equip.action_deactivate()
            logger.debug(config.log_formatter("UTILS", "", f"Deactivating thread after: {equip.name}"))
            time.sleep(0.2)

        for _ in range(3):  # sometimes they are still alive on first pass
            for thread in threads:
                if thread.is_alive():
                    thread.join(0.2)

    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
