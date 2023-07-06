

from unitpy import Unit, Quantity


class SensorCallback:
    def __init__(self, condition, function):
        self.condition = condition
        self.function = function


class Sensor:
    def __init__(self,
                 name: str,
                 equipment=None,
                 callbacks: list[SensorCallback] = None,
                 max_pressure: Quantity = Quantity("1.1 atm"),
                 min_pressure: Quantity = Quantity("0.9 atm"),
                 max_temperature: Quantity = Quantity("15 degC"),
                 min_temperature: Quantity = Quantity("35 degC"),
                 ):
        self.name = name
        self.equipment = equipment
        self.callbacks = callbacks
        self.max_pressure = max_pressure
        self.min_pressure = min_pressure
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature
