import sys
import os
import threading
import logging
import time
from typing import Protocol

from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name)


class EquipmentInterface(Protocol):
    name = ""

    def activate(self):
        ...

    def write_deactivate(self):
        ...


EQUIPMENT_TYPE = list[EquipmentInterface, ...] | tuple[EquipmentInterface, ...] | EquipmentInterface


def equipment_to_list(equipment: EQUIPMENT_TYPE):
    if not (isinstance(equipment, list) or isinstance(equipment, tuple)):
        equipment = [equipment]
    return equipment


class EquipmentManager:
    def __init__(self, equipment: EQUIPMENT_TYPE = None):
        self.equipment = []
        self.threads = {}

        if equipment is not None:
            self.add(equipment)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate()

    def add(self, equipment: EQUIPMENT_TYPE):
        self.equipment += equipment_to_list(equipment)

    def activate(self):
        self.threads = {equip.name: threading.Thread(target=equip.activate, name=equip.name) for equip in
                        self.equipment}

        # start all threads
        for thread in self.threads.values():
            thread.start()
            time.sleep(0.2)

        logger.info("UTILS || All threads started\n" + "#" * 48 + "\n\n\n")

    def deactivate(self):
        # wait for them all to finish
        try:
            while True:
                if all(not thread.is_alive() for thread in self.threads.values()):
                    break
                time.sleep(0.2)

        except KeyboardInterrupt:
            logger.info("\n\n\tKeyboardInterrupt raised\n")

        finally:
            logger.info("UTILS || Cleaning up threads")
            for equip in self.equipment:
                if not equip._deactivation_event:
                    equip.write_deactivate()
                    logger.debug(f"UTILS || Deactivating thread: {equip.name}")
                    time.sleep(0.2)

            for _ in range(3):  # sometimes they are still alive on first pass
                for thread in self.threads.values():
                    if thread.is_alive():
                        thread.join(0.2)

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
