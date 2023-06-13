import abc
import logging
import enum
from typing import Iterable

from chembot import registry
from chembot.configuration import config
import chembot.utils.numpy_parser as numpy_parser

logger = logging.getLogger(config.root_logger_name + ".equipment_interface")


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


class ParameterRange(abc.ABC):

    @abc.abstractmethod
    def valid_value(self, value) -> bool:
        ...


class NumericalRange(ParameterRange):
    def __init__(self, min_: float | int, max_: float | int, step: int | float | None = None):
        self.min_ = min_
        self.max_ = max_
        self.step = step

    def __str__(self):
        text = f"[{self.min_}:"
        if self.step is not None:
            text += f"{self.step}:"
        return text + f"{self.max_}]"

    def valid_value(self, value) -> bool:
        if self.min_ < value < self.max_:
            return True
        return False


class CategoricalRange(ParameterRange):
    def __init__(self, options: Iterable[int] | Iterable[float] | Iterable[str]):
        self.options = options

    def __str__(self):
        return str(self.options)

    def valid_value(self, value) -> bool:
        if value in self.options:
            return True

        return False


class NotDefinedParameter:
    def __init__(self):
        self.name = "not defined parameter"


class ActionParameter:
    def __init__(self,
                 name: str,
                 types: str | list[str],
                 descriptions: str = "",
                 range_: ParameterRange | None = None,
                 unit: str = None,
                 default=NotDefinedParameter(),
                 ):
        self.name = name
        self.descriptions = descriptions
        self.types = types
        self.range_ = range_
        self.unit = unit
        self.default = default

    def __str__(self):
        return self.name + f" || {self.types}"

    def __repr__(self):
        return self.__str__()

    @property
    def required(self) -> bool:
        if isinstance(self.default, NotDefinedParameter):
            return False
        return True

    def valid_value(self) -> bool:
        pass
        # validate type
        # validate unit
        # validate range


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

    @property
    def required_inputs(self) -> list[ActionParameter]:
        return [action for action in self.inputs if action.required]


class EquipmentInterface:
    def __init__(self, name: str, class_, actions: list[Action]):
        self.name = name
        self.class_ = class_
        self.actions = actions

    def __str__(self):
        return self.name + f"|| " + str(len(self.actions))

    def __repr__(self):
        return self.__str__()

    @property
    def action_names(self) -> set[str]:
        return {action.name for action in self.actions}

    def get_action(self, name: str):
        for action in self.actions:
            if action.name == name:
                return action

        raise ValueError(f"Action ({name}) not found in EquipmentInterface ({self.name}).")

    def data_row(self) -> dict:
        return {"name": self.name, "class": self.class_, "actions": len(self.actions)}


def get_equipment_interface(class_) -> EquipmentInterface:
    """ Given an Equipment create and equipment interface. """
    actions = []
    try:
        for func in dir(class_):
            if callable(getattr(class_, func)) and (func.startswith("read") or func.startswith("write")):
                docstring = numpy_parser.get_numpy_style_docstring(getattr(class_, func))
                inputs_ = parse_parameters(docstring.parameters)
                outputs_ = parse_parameters(docstring.returns)
                actions.append(Action(func, docstring.summary, inputs_, outputs_))
    except Exception as e:
        logger.exception(f"Exception raise while parsing: {class_.name} ({type(class_)}) "
                         f"function: {func if 'func' in locals() else None}")
        raise e

    return EquipmentInterface(class_.name, type(class_).__name__, actions)


def parse_parameters(list_: list[numpy_parser.Parameter]) -> list[ActionParameter]:
    results = []
    for parms in list_:
        description, range_, unit = parse_description(parms.description)
        type_ = parse_type(parms.type_)
        results.append(
            ActionParameter(
                parms.name,
                type_,
                description,
                range_,
                unit
            )
        )

    return results


def parse_description(text: list[str]) -> list[str, str, str]:
    result = ["", None, None]

    # text_list = text.split("\n")
    for line in text:
        if line.startswith("range"):
            result[1] = parse_range(line)
        elif line.startswith("unit"):
            result[2] = line
        else:
            result[0] += line

    return result


def parse_range(text: str) -> ParameterRange | None:
    if not text:
        return None

    text = text.replace("range:", "").replace(" ", "").replace("[", "").replace("]", "")

    if "'" in text or '"' in text:
        return parse_categorical_range(text)

    return parse_numerical_range(text)


def parse_categorical_range(text: str) -> CategoricalRange | None:
    options = text.replace("'", "").replace('"', "").split(",")
    if options:
        return CategoricalRange(options)

    return None


def parse_numerical_range(text: str) -> NumericalRange | CategoricalRange:
    count_collen = text.count(":")

    if count_collen == 0:
        options = text.split(",")
        options_numerical = []
        for op in options:
            try:
                num = float(op)
                if num == int(num):
                    num = int(num)
            except ValueError:
                if "None" in op:
                    num = None
            options_numerical.append(num)
        return CategoricalRange(options_numerical)

    if count_collen == 1:
        text = text.split(":")
        return NumericalRange(float(text[0]), float(text[1]))

    if count_collen == 2:
        text = text.split(":")
        return NumericalRange(float(text[0]), float(text[2]), float(text[1]))

    raise ValueError("Invalid doc sting range.")


def parse_type(type_: str) -> list[type] | type:

    # get built in python types; int, str, byte, etc.
    global __builtins__
    if type_ in __builtins__:
        return __builtins__[type_]

    if type_ in registry:
        return registry.get(type_)

    if type_.startswith("list"):
        pass
    if type_.startswith("tuple"):
        pass
    if type_.startswith("set"):
        pass
    if type_.startswith("dict"):
        pass


registry.register(EquipmentInterface)
registry.register(Action)
registry.register(ActionParameter)
registry.register(ActionType)
registry.register(EquipmentState)
registry.register(NumericalRange)
registry.register(CategoricalRange)
registry.register(NotDefinedParameter)
