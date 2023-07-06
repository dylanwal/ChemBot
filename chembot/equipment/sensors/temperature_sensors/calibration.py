import abc
import math
import logging

from unitpy import Unit, Quantity

from chembot.utils.unit_validation import validate_quantity
from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name + ".temperature")


class ThermalCalibration:
    resistance_dimensionality = Unit("ohm").dimensionality
    temperature_dimensionality = Unit("K").dimensionality

    def __init__(self,
                 temperature_limit_min: Quantity,
                 temperature_limit_max: Quantity,
                 ):
        self._temperature_limit_min = None
        self.temperature_limit_min = temperature_limit_min
        self._temperature_limit_max = None
        self.temperature_limit_max = temperature_limit_max

    @property
    def temperature_limit_min(self) -> Quantity:
        return self._temperature_limit_min

    @temperature_limit_min.setter
    def temperature_limit_min(self, temperature_limit_min: Quantity):
        validate_quantity(temperature_limit_min, self.temperature_dimensionality,
                          f"{type(self).__name__}.temperature_limit_min")
        self._temperature_limit_min = temperature_limit_min

    @property
    def temperature_limit_max(self) -> Quantity:
        return self._temperature_limit_max

    @temperature_limit_max.setter
    def temperature_limit_max(self, temperature_limit_max: Quantity):
        validate_quantity(temperature_limit_max, self.temperature_dimensionality,
                          f"{type(self).__name__}.temperature_limit_max")
        self._temperature_limit_max = temperature_limit_max

    def check_temperature_limits(self, temperature: Quantity):
        if not (self.temperature_limit_min < temperature < self.temperature_limit_max):
            logger.error(f"Temperature outside bound of calibration.\n\tReading: {temperature}"
                         f"\n\tRange: [{self.temperature_limit_min}, {self.temperature_limit_max}]")

    @abc.abstractmethod
    def to_temperature(self, arg: Quantity) -> Quantity:
        pass


class ThermistorCalibrationB(ThermalCalibration):
    def __init__(self,
                 B: Quantity,
                 resistance_min: Quantity,
                 temperature_min: Quantity,
                 temperature_limit_min: Quantity,
                 temperature_limit_max: Quantity,
                 ):
        super().__init__(temperature_limit_min, temperature_limit_max)
        self._B = None
        self.B = B
        self._resistance_min = None
        self.resistance_min = resistance_min
        self._temperature_min = None
        self.temperature_min = temperature_min

    @property
    def B(self) -> Quantity:
        return self._B

    @B.setter
    def B(self, B: Quantity):
        validate_quantity(B, self.temperature_dimensionality, f"{type(self).__name__}.B")
        self._B = B

    @property
    def resistance_min(self) -> Quantity:
        return self._resistance_min

    @resistance_min.setter
    def resistance_min(self, resistance_min: Quantity):
        validate_quantity(resistance_min, self.resistance_dimensionality, f"{type(self).__name__}.resistance_min")
        self._resistance_min = resistance_min

    @property
    def temperature_min(self) -> Quantity:
        return self._temperature_min

    @temperature_min.setter
    def temperature_min(self, temperature_min: Quantity):
        validate_quantity(temperature_min, self.temperature_dimensionality, f"{type(self).__name__}.temperature_min")
        self._temperature_min = temperature_min

    def to_temperature(self, resistance: Quantity) -> Quantity:
        validate_quantity(resistance, self.resistance_dimensionality, f"{type(self).__name__}.resistance", True)

        temperature = self.B * self.temperature_min / \
                      (self.temperature_min * math.log((resistance / self.resistance_min).value) + self.B)

        self.check_temperature_limits(temperature)
        return temperature


class ThermistorCalibrationSH(ThermalCalibration):
    """
    Steinhart–Hart equation
    """

    def __init__(self,
                 a,
                 b,
                 c,
                 temperature_limit_min: Quantity,
                 temperature_limit_max: Quantity,
                 ):
        super().__init__(temperature_limit_min, temperature_limit_max)
        self.a = a
        self.b = b
        self.c = c

    def to_temperature(self, resistance: Quantity) -> Quantity:
        validate_quantity(resistance, self.resistance_dimensionality, f"{type(self).__name__}.resistance", True)

        lnohm = math.log1p(resistance.v)  # take ln(ohms)

        # a, b, & c values from http://www.thermistor.com/calculators.php
        # using curve R (-6.2%/C @ 25C) Mil Ratio X
        a = 0.002197222470870
        b = 0.000161097632222
        c = 0.000000125008328

        # Steinhart Hart Equation
        # T = 1/(a + b[ln(ohm)] + c[ln(ohm)]^3)
        t1 = (b * lnohm)  # b[ln(ohm)]
        c2 = c * lnohm  # c[ln(ohm)]
        t2 = pow(c2, 3)  # c[ln(ohm)]^3
        temperature = 1 / (a + t1 + t2)  # calculate temperature_sensors

        temperature = temperature * Unit.K
        self.check_temperature_limits(temperature)
        return temperature.to("degC")
