from __future__ import annotations

import numpy as np
from unitpy import Quantity, Unit

from chembot.utils.unit_validation import validate_quantity


class Syringe:
    default_fill_time = 2 * Unit.min
    volume_dimensionality = Unit("liter").dimensionality
    diameter_dimensionality = Unit("meter").dimensionality
    pull_dimensionality = diameter_dimensionality
    flow_rate_dimensionality = Unit('mL/min').dimensionality

    def __init__(self,
                 volume: Quantity = None,
                 diameter: Quantity = None,
                 pull: Quantity = None,
                 default_flow_rate: Quantity = None,
                 force: int =None,
                 name: str = None,
                 vendor: str = None,
                 **kwargs
                 ):
        """
        Parameters
        ---------
        volume:
            volume (set 2 of 3 values: volume, diameter, pull)
        diameter:
            diameter (set 2 of 3 values: volume, diameter, pull)
        pull:
            pull (set 2 of 3 values: volume, diameter, pull)
        name:
            anything you like to write
        vendor:
            class_name of syringe vendor
        """
        if sum(1 for i in (volume, diameter, pull) if i is not None) != 2:
            raise ValueError("Provide 2 of 3 values to define a syringe: volume, diameter, pull")

        self._volume = None
        self._diameter = None
        self._pull = None
        self._default_flow_rate = None
        self.volume = volume
        self.diameter = diameter
        self.pull = pull
        self.default_flow_rate = default_flow_rate
        self.force = force

        self.vendor = vendor
        self.name = name if name is not None else f"syringe: {self.volume}"

        self._compute_missing_parameter()

        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def __str__(self):
        return f"{self.name} || volume: {self.volume}, diameter: {self.diameter}"

    @property
    def volume(self) -> Quantity:
        return self._volume

    @volume.setter
    def volume(self, volume: Quantity):
        if volume is None:
            return

        validate_quantity(volume, self.volume_dimensionality, f"Syringe.volume", positive=True)
        self._volume = volume

    @property
    def diameter(self) -> Quantity:
        return self._diameter

    @diameter.setter
    def diameter(self, diameter: Quantity):
        if diameter is None:
            return

        validate_quantity(diameter, self.diameter_dimensionality, f"Syringe.diameter", positive=True)
        self._diameter = diameter

    @property
    def pull(self) -> Quantity:
        return self._pull

    @pull.setter
    def pull(self, pull: Quantity):
        if pull is None:
            return

        validate_quantity(pull, self.pull_dimensionality, f"Syringe.pull", positive=True)
        self._pull = pull

    @property
    def default_flow_rate(self) -> Quantity:
        if self._default_flow_rate is None:
            return self.volume / self.default_fill_time

        return self._default_flow_rate

    @default_flow_rate.setter
    def default_flow_rate(self, default_flow_rate: Quantity):
        if default_flow_rate is None:
            default_flow_rate = self.volume / self.default_fill_time

        validate_quantity(default_flow_rate, self.flow_rate_dimensionality, f"Syringe.default_flow_rate", positive=True)
        self._default_flow_rate = default_flow_rate

    def _compute_missing_parameter(self):
        if self.diameter is not None and self.volume is not None and self.pull is None:
            self.pull = self.volume / (np.pi * (self.diameter/2)**2)
        if self.volume is not None and self.pull is not None and self.diameter is None:
            self.diameter = (self.volume / self.pull / np.pi)**(1/2) * 2
        if self.pull is not None and self.diameter is not None and self.volume is None:
            self.volume = self.pull * np.pi * (self.diameter/2)**2

    @classmethod
    def get_syringe(cls, name: str) -> Syringe:
        from chembot.reference_data.syringe_configs import syringe_configs
        if name in syringe_configs:
            return Syringe(name=name, **syringe_configs[name])
        raise KeyError(f"'{name}' not within syringe configuration.")
