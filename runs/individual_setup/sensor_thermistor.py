
from unitpy import U

import chembot

from runs.individual_setup.names import NamesSensors, NamesSerial

calibration = chembot.equipment.sensors.ThermistorCalibrationB(
    B=3984 * U.K,
    resistance_min=10 * U.ohm,
    temperature_min=25 * U.degC,
    temperature_limit_min=-55 * U.degC,
    temperature_limit_max=150 * U.degC
)

thermistor = chembot.equipment.sensors.TemperatureProbePicoADC(
    NamesSensors.REACTOR1_THERMISTOR,
    NamesSerial.PICO2,
    calibration,
    10_000 * U.ohm,
    resistor_order=True  # ??
)
thermistor.activate()
