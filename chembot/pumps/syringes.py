import json


with open("chembot/data/syringe_data.json") as f:
    syringe_configs = json.load(f)


class Syringe:
    units = syringe_configs["units"]

    def __init__(self,
                 name: str,
                 volume: float,
                 diameter: float,
                 max_pressure: float = None,
                 min_pressure: float = None,
                 max_temperature: float = None,
                 min_temperature: float = None,
                 vendor: str = None,
                 ):
        self.name = name
        self.volume = volume
        self.diameter = diameter
        self.vendor = vendor
        self.max_pressure = max_pressure
        self.min_pressure = min_pressure
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature

    def __str__(self):
        return f"{self.name} || volume: {self.volume}, diameter: {self.diameter}"


def get_syringe(name: str):
    if name in syringe_configs:
        return Syringe(name=name, **syringe_configs[name])

    raise KeyError(f"'{name}' not within syringe configuration.")
