
from chembot import logger


class ChemBotError(Exception):
    ...


class CommunicationError(ChemBotError):
    def __init__(self, text: str):
        self.text = text
        logger.error(text)

    def __str__(self):
        return self.text


class PumpError(ChemBotError):
    def __init__(self, text: str):
        self.text = text
        logger.error(text)

    def __str__(self):
        return self.text
