from __future__ import annotations

from unitpy import Quantity, Unit

from chembot.utils.unit_validation import validate_quantity


class Syringe:
    volume_dimensionality = Unit("liter").dimensionality
    diameter_dimensionality = Unit("meter").dimensionality
    pull_dimensionality = diameter_dimensionality

    def __init__(self,
                 volume: Quantity = None,
                 diameter: Quantity = None,
                 pull: Quantity = None,
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
            name of syringe vendor
        """
        if sum(1 for i in (volume, diameter, pull) if i is not None) != 2:
            raise ValueError("Provide 2 of 3 values to define a syringe: volume, diameter, pull")

        self._volume = volume
        self._diameter = diameter
        self._pull = pull
        self.vendor = vendor
        self.name = name if name is not None else f"syringe: {self.volume}"

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
        validate_quantity(volume, self.volume_dimensionality, f"Syringe.volume", positive=True)
        self._volume = volume

    @property
    def diameter(self) -> Quantity:
        return self._diameter

    @diameter.setter
    def diameter(self, diameter: Quantity):
        validate_quantity(diameter, self.volume_dimensionality, f"Syringe.diameter", positive=True)
        self._diameter = diameter

    @property
    def pull(self) -> Quantity:
        return self._pull

    @pull.setter
    def pull(self, pull: Quantity):
        validate_quantity(pull, self.volume_dimensionality, f"Syringe.pull", positive=True)
        self._pull = pull

    @classmethod
    def get_syringe(cls, name: str) -> Syringe:
        from chembot.reference_data.syringe_configs import syringe_configs
        if name in syringe_configs:
            return Syringe(name=name, **syringe_configs[name])
        raise KeyError(f"'{name}' not within syringe configuration.")
