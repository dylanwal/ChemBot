from __future__ import annotations

from equipment.equipment import Equipment
from unitpy import Quantity


class Syringe(Equipment):
    def __init__(self,
                 name: str,
                 volume: Quantity,
                 diameter: Quantity,
                 vendor: str = None,
                 **kwargs
                 ):
        super().__init__(name, state=Equipment.states.pre_activation, **kwargs)
        self.volume = volume
        self.diameter = diameter
        self.vendor = vendor

    def __str__(self):
        return f"{self.name} || volume: {self.volume}, diameter: {self.diameter}"

    @classmethod
    def get_syringe(cls, name: str) -> Syringe:
        from chembot.reference_data.syringe_configs import syringe_configs
        if name in syringe_configs:
            return Syringe(name=name, **syringe_configs[name])
        raise KeyError(f"'{name}' not within syringe configuration.")
