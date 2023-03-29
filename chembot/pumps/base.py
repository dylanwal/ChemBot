"""

syringe pump queues
    write to:
    * error
    * status
    * communication line (serial line to pump)
    read from:
    * SyringePump_i

logger

"""

import abc
import math
import enum
import logging

import chembot.utils.sig_figs as sig_figs
from chembot.errors import EquipmentError
from chembot.pumps.flow_profile import PumpFlowProfile


logger = logging.getLogger("ChemBot.pump")


def calc_pull(diameter: float, volume: float) -> float:
    return volume / (math.pi * (diameter / 2) ** 2)


def calc_volume(diameter: float, pull: float) -> float:
    return math.pi * (diameter / 2) ** 2 * pull


def calc_diameter(volume: float, pull: float) -> float:
    return 2 * math.sqrt(volume / (math.pi * pull))


class PumpControlMethod(enum.Enum):
    flow_rate = 0
    pressure = 1


class SyringePump(abc.ABC):
    control_methods = PumpControlMethod

    def __init__(
            self,
            name: str,
            diameter: float | int = None,  # units: cm
            max_volume: float | int = None,  # units: ml
            max_pull: float | int = None,  # units: cm
            control_method: PumpControlMethod = PumpControlMethod.flow_rate,
    ):
        self.name = name

        # setup everything
        self._diameter = None
        self._max_volume = None
        self._max_pull = None
        self._volume = 0
        self._flow_rate = 0
        self._flow_rate_profile = None
        self._target_volume = 0
        self._pull = 0
        self._set_syringe_settings(diameter, max_volume, max_pull)
        self._state = None
        self._control_method = None
        self.control_method = control_method

        # additional attributes
        self._flow_profile = None

        logger.info(self.name + "\n\t\tSetup complete.")

    def __str__(self):
        return self.name

    def details(self) -> str:
        text = f"Pump: {self.name} \n"
        text += f"current state: {self.state} \n"
        text += f"\tdiameter: {self.diameter} cm\n"
        text += f"\tmax_volume: {self.max_volume} ml\n"
        text += f"\tmax_pull: {self.max_pull} cm\n"
        text += f"\tvolume: {self.volume} ml\n"
        text += f"\tflow_rate: {self.flow_rate} ml/min\n"
        text += f"\tposition: {self.pull} ml \n"

        return text

    def _set_syringe_settings(self,
                              diameter: float | int | None,
                              max_volume: float | int | None,
                              max_pull: float | int | None):

        if isinstance(diameter, (float, int)):
            self._check_diameter(diameter)
            if isinstance(max_volume, (float, int)):
                self._check_max_volume(max_volume)
                self._diameter = diameter
                self._max_volume = max_volume
                self._max_pull = calc_pull(diameter, max_volume)
                return

            elif isinstance(max_pull, (float, int)):
                self._check_max_pull(max_pull)
                self._diameter = diameter
                self._max_volume = calc_volume(diameter, max_pull)
                self._max_pull = max_pull
                return

        elif isinstance(max_volume, float):
            self._check_max_volume(max_volume)
            if isinstance(max_pull, float):
                self._check_max_pull(max_pull)
                self._diameter = calc_diameter(max_volume, max_pull)
                self._max_volume = max_volume
                self._max_pull = max_pull
                return

        raise EquipmentError(self, "Insufficient information provided for setup. 2 of 3 need: [diameter, max_volume, "
                                   "max_pull]")

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, diameter: int | float):
        self._diameter_setter(diameter)

    def _diameter_setter(self, diameter: int | float):
        """
        This was broken out to allow overloading.

        Parameters
        ----------
        diameter

        Returns
        -------

        """
        self._check_diameter(diameter)
        max_volume = calc_volume(diameter, self.max_pull)
        self._check_max_volume(max_volume)
        self._max_volume = max_volume
        self._diameter = diameter

    def _check_diameter(self, diameter: float):
        if diameter <= 0 or not isinstance(diameter, (float, int)):
            raise EquipmentError(self, f"Diameter must be a positive float.\nGiven: {diameter}, {type(diameter)}")

    @property
    def max_volume(self):
        return self._max_volume

    @max_volume.setter
    def max_volume(self, max_volume: float | int):
        self._check_max_volume(max_volume)
        logger.warning(self.name + "Changing 'max_volume' after initialization can cause mismatch with max_pull and diameter.")
        self._max_volume = max_volume

    def _check_max_volume(self, max_volume: float | int):
        if max_volume <= 0 or not isinstance(max_volume, (float, int)):
            raise EquipmentError(self,
                                 f"Max volume must be a positive float.\n Given: {max_volume}, {type(max_volume)}")

    @property
    def max_pull(self):
        return self._max_pull

    @max_pull.setter
    def max_pull(self, max_pull: float | int):
        self._check_max_pull(max_pull)
        max_volume = calc_volume(self.diameter, max_pull)
        self._check_max_volume(max_volume)
        self._max_volume = max_volume
        self._max_pull = max_pull

    def _check_max_pull(self, max_pull: float | int):
        if max_pull <= 0 or not isinstance(max_pull, (float, int)):
            raise EquipmentError(self, f"Max pull must be a positive float.\n Given: {max_pull}, {type(max_pull)}")

    @property
    def volume(self):
        """ Current volume in syringe"""
        return self._volume

    @volume.setter
    def volume(self, volume: float):
        """
        Only should be used during setting up the pump.

        Parameters
        ----------
        volume: int | float
            current pump volume

        """
        self._check_volume(volume)
        pull = calc_pull(self.diameter, volume)
        self._check_pull(pull)
        self._pull = pull
        self._volume = volume

    def _check_volume(self, volume: int | float):
        if not isinstance(volume, (int, float)):
            raise EquipmentError(self, f"'volume' must be an int or float. \n given: {type(volume)}")

        if 0 > volume or self.max_volume < volume:
            raise EquipmentError(self, f"Requested 'volume' is outside the acceptable range. \n"
                                       f"range: [0, {self.max_volume}], requested: {volume}")

    @property
    def pull(self):
        """ Current pull """
        return self._pull

    @pull.setter
    def pull(self, pull: int | float):
        """
        Only should be used during setting up the pump.

        Parameters
        ----------
        pull: int | float
            current pump pull
        """
        self._check_pull(pull)
        volume = calc_volume(self.diameter, pull)
        self._check_volume(volume)
        self._volume = volume
        self._pull = pull

    def _check_pull(self, pull: int | float):
        if not isinstance(pull, (int, float)):
            raise EquipmentError(self, f"'pull' must be an int or float. \n given: {type(pull)}")

        if pull < 0 or pull > self.max_pull:
            raise EquipmentError(self, f"Requested 'pull' is outside the acceptable range. \n"
                                       f"range: [0, {self.max_pull}], requested: {pull}")

    @property
    def state(self):
        return self._state

    @property
    def flow_rate(self) -> int | float:
        return self._flow_rate

    @property
    def target_volume(self) -> int | float:
        return self.target_volume

    @property
    def flow_rate_profile(self) -> PumpFlowProfile:
        return self._flow_rate_profile

    ## Actions ##
    @abc.abstractmethod
    def zero(self):
        """"""
        self._pull = 0
        self._volume = 0

    @abc.abstractmethod
    def refill(self):
        self._pull = self.max_pull
        self._volume = self._max_volume

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self):
        ...

    def register(self):
        help_str = ""
        for name, func in SyringePump.__dict__.items():
            if callable(func):
                doc = func.__doc__ if func.__doc__ is not None else "No documentation available."
                help_str += f"{name}: {doc}\n"
        self.channel.basic_publish(exchange='', routing_key='pump_cmd', body=help_str)
        print("Sent help message.")
