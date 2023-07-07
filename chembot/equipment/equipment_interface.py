import abc
import enum
import types
import inspect
from typing import Iterable, Callable
import functools
import logging

from unitpy import Unit, Quantity

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

    def __repr__(self):
        return self.__str__()

    @abc.abstractmethod
    def validate(self, value) -> bool:
        ...


class NumericalRangeContinuous(ParameterRange):
    def __init__(self, min_: float | int, max_: float | int):
        self.min_ = min_
        self.max_ = max_

    def __str__(self):
        return f"[{self.min_}:{self.max_}]"

    def validate(self, value):
        if not (self.min_ < value < self.max_):
            raise ValueError(f"{type(self).__name__}: Outside Range: [{self.min_}:{self.max_}]")


class NumericalRangeDiscretized(ParameterRange):
    def __init__(self, min_: float | int, max_: float | int, step: int | float | None = None):
        self.min_ = min_
        self.max_ = max_
        self.step = step

    def __str__(self):
        text = f"[{self.min_}:"
        if self.step is not None:
            text += f"{self.step}:"
        return text + f"{self.max_}]"

    def validate(self, value):
        if not (self.min_ < value < self.max_) or (value % self.step) == (self.min_ % self.step):
            raise ValueError(f"{type(self).__name__}: Outside Range: [{self.min_}:{self.max_}:{self.step}]")


class CategoricalRange(ParameterRange):
    def __init__(self, options: Iterable[int] | Iterable[float] | Iterable[str]):
        self.options = options

    def __str__(self):
        return str(self.options)

    def validate(self, value):
        if value not in self.options:
            raise ValueError(f"{type(self).__name__}: Invalid option. Expected: {self.options}")


class ActionParameter:
    empty = inspect.Parameter.empty

    def __init__(self,
                 name: str,
                 type_: type | types.UnionType | empty,
                 descriptions: str = "",
                 range_: ParameterRange | None = None,
                 unit: str = empty,
                 default=empty,
                 ):
        self.name = name
        self.descriptions = descriptions
        self.type_ = type_
        self.range_ = range_
        self.unit = unit
        self.default = default

    def __str__(self):
        text = self.name
        if self.type_ is not self.empty:
            if not hasattr(self.type_, "__origin__"):
                text += ": " + self.type_.__name__
            else:
                text += ": " + str(self.type_)
        if self.default is not self.empty:
            text += " = " + str(self.default)
        return text

    def __repr__(self):
        return self.__str__()

    @property
    def required(self) -> bool:
        if self.default is self.empty:
            return False
        return True

    def validate(self, value):
        validate_type(self.type_, value)

        if self.unit is not self.empty:
            if not isinstance(value, Quantity):
                raise TypeError(f"Received: {type(value)} || Expected: Quantity")
            if Unit(self.unit).dimensionality != value.dimensionality:
                raise ValueError(f"Wrong unit dimensionality. "
                                 f"\nReceived: {value.dimensionality} || Expected: {Unit(self.unit).dimensionality} "
                                 f"({self.unit})")
            value = value.to(self.unit)

        if self.range_ is not None:
            self.range_.validate(value)


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
        return self.name + f"({''.join(str(i) for i in self.inputs)}) -> {''.join(str(i) for i in self.outputs)}"

    def __repr__(self):
        return self.__str__()

    @property
    def required_inputs(self) -> list[ActionParameter]:
        return [action for action in self.inputs if action.required]


class EquipmentInterface:
    def __init__(self, class_, actions: list[Action]):
        self.class_ = class_
        self.actions = actions

    def __str__(self):
        return self.class_.__name__ + f"|| " + str(len(self.actions))

    def __repr__(self):
        return self.__str__()

    @property
    def class_name(self) -> str:
        return self.class_.__name__

    @property
    def action_names(self) -> set[str]:
        return {action.name for action in self.actions}

    def get_action(self, name: str):
        for action in self.actions:
            if action.name == name:
                return action

        raise ValueError(f"Action ({name}) not found in EquipmentInterface ({self.class_}).")

    # def data_row(self) -> dict:
    #     return {"class_name": self.class_name, "class": self.class_, "actions": len(self.actions)}


class EquipmentRegistry:
    def __init__(self):
        self.equipment: dict[str, EquipmentInterface] = dict()

    def register(self, name: str, equipment_interface: EquipmentInterface):
        self.equipment[name] = equipment_interface

    def register_equipment(self, name: str, equipment):
        equipment_interface = get_equipment_interface(equipment)
        self.register(name, equipment_interface)

    def unregister(self, name: str):
        try:
            del self.equipment[name]
        except KeyError:
            logger.error(f"Error unregistering '{name}'. Not in registry.")


#######################################################################################################################
# Additional parsing on docstring

@functools.lru_cache
def get_equipment_interface(class_: type) -> EquipmentInterface:
    """ Given an Equipment create and equipment interface. """
    funcs = get_class_functions(class_)
    actions = []
    for func in funcs:
        try:
            actions.append(get_action(getattr(class_, func)))
        except Exception as e:
            raise ValueError(f"Exception raise while parsing: {class_.__name__}.{func}") from e

    return EquipmentInterface(class_, actions)


def get_class_functions(class_: type) -> list[str]:
    funcs = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and (func.startswith("read") or func.startswith("write")):
            funcs.append(func)
    return funcs


def get_action(func: Callable) -> Action:
    docstring = numpy_parser.parse_numpy_docstring_and_signature(func)
    inputs_ = parse_parameters(docstring.parameters)
    outputs_ = parse_parameters(docstring.returns)
    return Action(func.__name__, docstring.summary, inputs_, outputs_)


def parse_parameters(list_: list[numpy_parser.Parameter] | None) -> list[ActionParameter]:
    if list_ is None:
        return []

    results = []
    for parms in list_:
        description, range_, unit = parse_description(parms.description)
        results.append(
            ActionParameter(
                parms.name,
                get_type(parms.type_),
                description,
                range_,
                unit
            )
        )

    return results


def parse_description(text: list[str]) -> list[str, ParameterRange | None, str | None]:
    result = ["", ActionParameter.empty, ActionParameter.empty]  # [description, range, unit]

    if text is None:
        return result

    for line in text:
        line = line.strip()
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
        return CategoricalRange(text.replace("'", "").replace('"', "").split(","))

    return parse_numerical_range(text)


def parse_numerical_range(text: str) -> NumericalRangeContinuous | NumericalRangeDiscretized | CategoricalRange:
    count_collen = text.count(":")

    if count_collen == 0:
        options = text.split(",")
        options_numerical = []
        for op in options:
            try:
                num = number_to_int_or_float(op)
            except ValueError:
                if "None" in op:
                    num = None
                else:
                    raise ValueError(f"Invalid doc-sting range. \ntext: {text}")
            options_numerical.append(num)
        return CategoricalRange(options_numerical)

    if count_collen == 1:
        text = text.split(":")
        return NumericalRangeContinuous(number_to_int_or_float(text[0]), number_to_int_or_float(text[1]))

    if count_collen == 2:
        text = text.split(":")
        return NumericalRangeDiscretized(
            min_=number_to_int_or_float(text[0]),
            max_=number_to_int_or_float(text[2]),
            step=number_to_int_or_float(text[1])
        )

    raise ValueError(f"Invalid doc-sting range. \ntext: {text}")


def number_to_int_or_float(number: str) -> int | float:
    num = float(number)
    if num == int(num):
        return int(num)
    return num


import builtins
builtin_types = {d: getattr(builtins, d) for d in dir(builtins) if isinstance(getattr(builtins, d), type)}


def get_type(type_: str | type) -> type:
    if isinstance(type_, type):
        return type_

    if type_ in builtin_types:
        return builtin_types[type_]
    if type_ == "Quantity":
        return Quantity

    if type_ == "RampFlowRate":
        from chembot.equipment.pumps.harvard_apparatus_syringe_pump import RampFlowRate
        return RampFlowRate

    if type_ == "Syringe":
        from chembot.equipment.pumps.syringes import Syringe
        return Syringe

    if type_ == "HarvardPumpStatusMessage":
        from chembot.equipment.pumps.harvard_apparatus_syringe_pump import HarvardPumpStatusMessage
        return HarvardPumpStatusMessage

    if type_ == "HarvardPumpVersion":
        from chembot.equipment.pumps.harvard_apparatus_syringe_pump import HarvardPumpVersion
        return HarvardPumpVersion

    # TODO: make more general
    raise TypeError(f"Type not known: {type_}; it needs to be added.")


def validate_type(type_: type, value):
    error = TypeError(f"Expected type:{type_}\nReceived type: {type(value)} ({value})")

    if hasattr(type_, "__origin__"):
        outer_layer = type_.__origin__
        inner_layer = type_.__args__
        if outer_layer is list:
            if not isinstance(value, list):
                raise error
            if not isinstance(value[0], inner_layer[0]):  # handle full list and  ...
                raise error
        # TODO: dict, tuple

    else:
        if not isinstance(value, type_):
            raise error
