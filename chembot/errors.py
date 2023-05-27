from typing import Protocol

from chembot import logger


class EquipmentObject(Protocol):
    id_: int


class ChemBotError(Exception):
    ...


class EquipmentError(ChemBotError):
    def __init__(self, obj: EquipmentObject, text: str):
        self.text = f"{type(obj).__name__} (id: {obj.id_}): " + text
        logger.error(self.text)

    def __str__(self):
        return self.text


# class CommunicationError(ChemBotError):
#     def __init__(self, text: str):
#         self.text = text
#         logger.error(text)
#
#     def __str__(self):
#         return self.text
#
#
# class PumpError(ChemBotError):
#     def __init__(self, obj: ErrorObject, text: str):
#         text:
#         self.text = text
#         logger.error(text)
#
#     def __str__(self):
#         return self.text
#
#

class PumpFlowRateError(ChemBotError):
    def __init__(self, text: str):
        self.text = text
        logger.error(text)

    def __str__(self):
        return self.text
