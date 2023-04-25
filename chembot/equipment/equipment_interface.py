
import enum

import docstring_parser

class EquipmentState(enum.Enum):
    OFFLINE = 0  # used for equipment that was online at some point but gone
    PREACTIVATION = 1  # Used to announce it coming online
    STANDBY = 2
    SCHEDULED_FOR_USE = 3
    RUNNING = 4
    RUNNING_BUSY = 5  # will not accept writes in this state
    SHUTTING_DOWN = 6
    CLEANING = 7
    ERROR = 8


class ActionType(enum.Enum):
    READ = 0
    WRITE = 1


class ActionParameters:
    def __init__(self,
                 name: str,
                 type_,
                 descriptions: str = "",
                 min_: float | int = None,
                 max_: float | int = None,
                 options: list | tuple = None
                 ):
        self.name = name
        self.descriptions = descriptions
        self.type_ = type_
        self.min_ = min_
        self.max_ = max_
        self.options = options


class Action:
    def __init__(self,
                 name: str,
                 descriptions: str = "",
                 inputs: list[ActionParameters] = None,
                 outputs: list[ActionParameters] = None
                 ):
        self.name = name
        self.descr = descriptions
        if name.startswith("read"):
            self._type = ActionType.READ
        else:
            self._type = ActionType.WRITE
        self.inputs = inputs
        self.outputs = outputs


class EquipmentInterface:
    def __init__(self, name: str, actions: list[Action], state: EquipmentState):
        self.name = name
        self.state = state
        self.actions = actions


def get_equipment_interface(class_) -> EquipmentInterface:
    """ Given an Equipment create and equipment interface. """
    actions = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and (func.startswith("read_") or func.startswith("write_")):
            docstring = docstring_parser.parse(getattr(class_, func).__doc__, docstring_parser.DocstringStyle.NUMPYDOC)
            inputs_ = parse_inputs(docstring.params)
            outputs_ = parse_outputs(docstring.returns)
            actions.append(Action(func, docstring.short_description, inputs_, outputs_))

    return EquipmentInterface(class_.name, actions, class_.state)


def parse_inputs(parms: list) -> list[ActionParameters]:
    return []


def parse_outputs(parms: list) -> list[ActionParameters]:
    return []
