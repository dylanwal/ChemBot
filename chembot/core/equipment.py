from unitpy import Unit, Quantity


class Equipment:
    def __init__(self,
                 max_pressure: Quantity = None,
                 min_pressure: Quantity = None,
                 max_temperature: Quantity = None,
                 min_temperature: Quantity = None,
                 ):
        self.max_pressure = max_pressure
        self.min_pressure = min_pressure
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature
