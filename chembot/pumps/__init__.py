
import logging
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

from flow_profile import PumpFlowProfile

from pumps.subclasses.harvard_pumps import PumpHarvard

from chembot.pumps.syringes import Syringe
