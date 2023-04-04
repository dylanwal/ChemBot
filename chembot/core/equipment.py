import enum

from unitpy import Unit, Quantity


class EquipmentState(enum.Enum):
    OFFLINE = 0
    PREACTIVATION = 1
    STANDBY = 2
    SCHEDULED_FOR_USE = 3
    TRANSIENT = 4
    RUNNING = 5
    SHUTTING_DOWN = 6
    CLEANING = 7
    ERROR = 8


class Equipment:
    states = EquipmentState

    def __init__(self,
                 name: str,
                 state: EquipmentState,
                 graph_in: list[str] = None,
                 graph_out: list[str] = None,
                 graph_group: list[str] = None,
                 max_pressure: Quantity = Quantity("1.1 atm"),
                 min_pressure: Quantity = Quantity("0.9 atm"),
                 max_temperature: Quantity = Quantity("15 degC"),
                 min_temperature: Quantity = Quantity("35 degC"),
                 ):
        self.name = name
        self.states = state
        self.graph_in = graph_in
        self.graph_out = graph_out
        self.graph_group = graph_group
        self.max_pressure = max_pressure
        self.min_pressure = min_pressure
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature
