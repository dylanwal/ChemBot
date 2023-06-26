
import logging

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.equipment.pumps.syringes import Syringe
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.communication.serial_pico import PicoSerial


logger = logging.getLogger(config.root_logger_name + ".pump")

class HarvardPumpStatus:
    STANDBY = ":"
    INFUSE = ">"
    WITHDRAW = "<"
    STALLED = "*"
    TARGET_REACHED = "T"


class CommandError:
    """
    Command errors are displayed when the command is unrecognized, entered in the wrong mode,
    or the state of the pump keeps the command from executing
    """


class ArgumentError:
    """
    Argument errors are displayed when a command argument is unrecognized or out of range.
    The argument in question will be displayed except in the case of missing arguments.
    """


def remove_crud(string: str) -> str:
    """Return string without useless information.
     Return string with trailing zeros after a decimal place, trailing
     decimal points, and leading and trailing spaces removed.
     """
    if "." in string:
        string = string.rstrip('0')

    string = string.lstrip('0 ')
    string = string.rstrip(' .')

    return string


def _format_diameter(pump: SyringePump, diameter: float) -> str:
    # SyringePump only considers 2 d.p. - anymore are ignored
    diameter_str = str(round(diameter, 2))

    if diameter != float(diameter_str):
        logger.warning(f'{pump.name} diameter truncated to {diameter_str} mm')

    return diameter_str


def _format_flow_rate(pump: SyringePump, flow_rate: int | float) -> str:
    flow_rate = str(flow_rate)

    if len(flow_rate) > 5:
        flow_rate = flow_rate[0:5]
        logger.warning(f'{pump.name} flow rate truncated to {flow_rate} uL/min')

    return remove_crud(flow_rate)


def remove_string_formatting_char(string: str) -> str:
    return ''.join(s for s in string if 31 < ord(s) < 126)


class SyringePumpHarvard:
    """ for USB """

    def __init__(self):


    def write_echo(self):
        prompt = "echo [on]"