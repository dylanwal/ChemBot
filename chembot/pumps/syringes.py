from __future__ import annotations

import core.equipment
from unitpy import Unit, Quantity


class Syringe(core.equipment.Equipment):
    def __init__(self,
                 name: str,
                 volume: Quantity,
                 diameter: Quantity,
                 max_pressure: Quantity = None,
                 min_pressure: Quantity = None,
                 max_temperature: Quantity = None,
                 min_temperature: Quantity = None,
                 vendor: str = None,
                 ):
        super().__init__(max_pressure, min_pressure, max_temperature, min_temperature)
        self.name = name
        self.volume = volume
        self.diameter = diameter
        self.vendor = vendor

    def __str__(self):
        return f"{self.name} || volume: {self.volume}, diameter: {self.diameter}"

    @classmethod
    def get_syringe(cls, name: str) -> Syringe:
        from chembot.data.syringe_configs import syringe_configs
        if name in syringe_configs:
            return Syringe(name=name, **syringe_configs[name])
        raise KeyError(f"'{name}' not within syringe configuration.")
