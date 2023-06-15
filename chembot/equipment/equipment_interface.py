import abc
import enum
from typing import Iterable, Callable

from unitpy import Unit, Quantity

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


class ParameterRange(abc.ABC):
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


class TypeOptions:
    def __init__(self, types: list[type | TypeList] = None):
        self.types = types if types is not None else []

    def add(self, option: type | TypeList):
        self.types.append(option)

    def validate(self, value):
        for type_ in self.types:
            if isinstance(type_, type):
                if isinstance(value, type_):
                    return
            else:  # TypeList
                try:
                    type_.validate(value)
                    return
                except TypeError:
                    pass

        raise TypeError(f"Received: {type(value)} || Expected: {self.types}")


class NotDefinedParameter:
    def __init__(self):
        self.name = "not defined parameter"


class ActionParameter:
    def __init__(self,
                 name: str,
                 types: TypeOptions,
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

    def validate(self, value):
        self.types.validate(value)
        if self.unit is not None:
            if not isinstance(value, Quantity):
                raise TypeError(f"Received: {type(value)} || Expected: Quantity")
            if Unit(self.unit).dimensionality != value.dimensionality:
                raise ValueError(f"Wrong unit dimensionality. "
                                 f"\nReceived: {value.dimensionality} || Expected: {Unit(self.unit).dimensionality} "
                                 f"({self.unit})")

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
        return self.name + f" || {self.inputs} --> {self.outputs}"

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
    def action_names(self) -> set[str]:
        return {action.name for action in self.actions}

    def get_action(self, name: str):
        for action in self.actions:
            if action.name == name:
                return action

        raise ValueError(f"Action ({name}) not found in EquipmentInterface ({self.class_}).")

    # def data_row(self) -> dict:
    #     return {"name": self.name, "class": self.class_, "actions": len(self.actions)}


#######################################################################################################################
# Additional parsing on docstring

def get_equipment_interface(class_: type) -> EquipmentInterface:
    """ Given an Equipment create and equipment interface. """
    funcs = get_class_functions(class_)
    actions = []
    for func in funcs:
        try:
            actions.append(get_action(getattr(class_, func)))
        except Exception as e:
            raise ValueError(f"Exception raise while parsing: ({class_.__name__}) "
                             f"function: {func if 'func' in locals() else None}") from e

    return EquipmentInterface(class_, actions)


def get_class_functions(class_: type) -> list[str]:
    funcs = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and (func.startswith("read") or func.startswith("write")):
            funcs.append(func)
    return funcs


def get_action(func: Callable) -> Action:
    docstring = numpy_parser.parse_numpy_docstring_and_typehints(func)
    inputs_ = parse_parameters(docstring.parameters)
    outputs_ = parse_parameters(docstring.returns)
    return Action(func.__name__, "".join(docstring.summary), inputs_, outputs_)


def parse_parameters(list_: list[numpy_parser.Parameter]) -> list[ActionParameter]:
    results = []
    for parms in list_:
        description, range_, unit = parse_description(parms.description)
        results.append(
            ActionParameter(
                parms.name,
                type_conversion(parms.type_),
                description,
                range_,
                unit
            )
        )

    return results


def type_conversion(type_: type | numpy_parser.NOT_DEFINED) -> type | NotDefinedParameter:
    if isinstance(type_, numpy_parser.NOT_DEFINED):
        return NotDefinedParameter()
    return type_


def parse_description(text: list[str]) -> list[str, ParameterRange | None, str | None]:
    result = ["", None, None]  # [description, range, unit]

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
        return CategoricalRange(text.replace("'", "").replace('"', "").split(","))

    return parse_numerical_range(text)


def parse_numerical_range(text: str) -> NumericalRangeContinuous | NumericalRangeDiscretized | CategoricalRange:
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
                else:
                    raise ValueError(f"Invalid doc-sting range. \ntext: {text}")
            options_numerical.append(num)
        return CategoricalRange(options_numerical)

    if count_collen == 1:
        text = text.split(":")
        return NumericalRangeContinuous(float(text[0]), float(text[1]))

    if count_collen == 2:
        text = text.split(":")
        return NumericalRangeDiscretized(float(text[0]), float(text[2]), float(text[1]))

    raise ValueError(f"Invalid doc-sting range. \ntext: {text}")


registry.register(EquipmentInterface)
registry.register(Action)
registry.register(ActionParameter)
registry.register(ActionType)
registry.register(EquipmentState)
registry.register(NumericalRangeContinuous)
registry.register(NumericalRangeDiscretized)
registry.register(CategoricalRange)
registry.register(NotDefinedParameter)
