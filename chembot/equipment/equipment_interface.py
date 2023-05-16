
import enum

from chembot import registry
import chembot.utils.numpy_parser as numpy_parser


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


class ActionParameter:
    def __init__(self,
                 name: str,
                 types: str | list[str],
                 descriptions: str = "",
                 range_: list | tuple = None,
                 unit: str = None
                 ):
        self.name = name
        self.descriptions = descriptions
        self.types = types
        self.range_ = range_
        self.unit = unit

    def __str__(self):
        return self.name + f" || {self.types}"

    def __repr__(self):
        return self.__str__()


class Action:
    def __init__(self,
                 name: str,
                 description: str = "",
                 inputs: list[ActionParameter] = None,
                 outputs: list[ActionParameter] = None
                 ):
        self.name = name
        self.description = description
        if name.startswith("read"):
            self.type_ = ActionType.READ
        else:
            self.type_ = ActionType.WRITE
        self.inputs = inputs
        self.outputs = outputs

    def __str__(self):
        return self.name + f" || {self.inputs} --> {self.outputs}"

    def __repr__(self):
        return self.__str__()


class EquipmentInterface:
    def __init__(self, name: str, class_, actions: list[Action], state: EquipmentState):
        self.name = name
        self.class_ = class_
        self.state = state
        self.actions = actions

    def __str__(self):
        return self.name + f" ({self.state.name}) || " + str(len(self.actions))

    def __repr__(self):
        return self.__str__()

    def data_row(self) -> dict:
        return {"name": self.name, "class": self.class_, "state": self.state.name, "actions": len(self.actions)}


def get_equipment_interface(class_) -> EquipmentInterface:
    """ Given an Equipment create and equipment interface. """
    actions = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and (func.startswith("read") or func.startswith("write")):
            docstring = numpy_parser.get_numpy_style_docstring(getattr(class_, func))
            inputs_ = parse_parameters(docstring.parameters)
            outputs_ = parse_parameters(docstring.returns)
            actions.append(Action(func, docstring.summary, inputs_, outputs_))

    return EquipmentInterface(class_.name, type(class_).__name__, actions, class_.state)


def parse_parameters(list_: list[numpy_parser.Parameter]) -> list[ActionParameter]:
    results = []
    for parms in list_:
        description, range_, unit = parse_description(parms.description)
        results.append(
            ActionParameter(
                parms.name,
                parms.type_,
                description,
                range_,
                unit
            )
        )

    return results


def parse_description(text: list[str]) -> list[str, str, str]:
    result = ["", "", ""]

    # text_list = text.split("\n")
    for line in text:
        if line.startswith("range"):
            result[1] = line
        elif line.startswith("unit"):
            result[2] = line
        else:
            result[0] += line

    return result


registry.register(EquipmentInterface)
registry.register(Action)
registry.register(ActionParameter)
registry.register(ActionType)
registry.register(EquipmentState)
