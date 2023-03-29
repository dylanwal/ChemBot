import logging

logger = logging.getLogger("ChemBot")
logger.setLevel(logging.WARNING)

from chembot.configuration import config

import chembot.pumps as pumps

