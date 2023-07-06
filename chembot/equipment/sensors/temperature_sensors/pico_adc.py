import logging

from unitpy import Quantity

from chembot.reference_data.pico_pins import PicoHardware
from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.communication.serial_pico import PicoSerial
from chembot.equipment.sensors.sensor import Sensor
from chembot.equipment.sensors.temperature_sensors.calibration import ThermalCalibration

logger = logging.getLogger(config.root_logger_name + ".temperature")


def analog_to_volt(num: int, supply_volt: Quantity, resolution: int) -> Quantity:
    return num * supply_volt / resolution


def voltage_divider_voltage_to_ohm(
        voltage: Quantity,
        resistor: Quantity,
        resistor_order: bool,
        supply_voltage: Quantity
) -> Quantity:
    """
    For a voltage divider

    V_in->R1->(V_out)->R2->ground
    order = True -> solve for R1
    order = False -> sovle for R2

    """
    if resistor_order:
        return resistor*((supply_voltage/voltage).v - 1)

    return resistor/((supply_voltage/voltage).v - 1)


class TemperatureProbePicoADC(Sensor):
    """ Voltage Divider setup"""
    def __init__(self,
                 name: str,
                 communication: str,
                 calibration: ThermalCalibration,
                 resistor: Quantity,
                 resistor_order: bool,
                 reference_voltage: Quantity = PicoHardware.v_sys,
                 ):
        """

        Parameters
        ----------
        name
        communication
        calibration
        resistor
        resistor_order:
            V_in->R1->(V_out)->R2->ground
            order = True -> solve for R1
            order = False -> solve for R2
        reference_voltage
        """
        super().__init__(name)
        self.communication = communication
        self.calibration = calibration
        self.resistor = resistor
        self.resistor_order = resistor_order
        self.reference_voltage = reference_voltage
        self._pin = PicoHardware.pin_internal_temp

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def _stop(self):
        pass

    def write_measure(self) -> Quantity:
        message = RabbitMessageAction(self.communication, self.name, PicoSerial.read_analog)
        reply = self.rabbit.send_and_consume(message, error_out=True)

        adc_reading = reply.value
        voltage = analog_to_volt(adc_reading, self.reference_voltage, PicoHardware.ADC_resolution)
        resistance = voltage_divider_voltage_to_ohm(voltage, self.resistor, self.resistor_order, self.reference_voltage)
        return self.calibration.to_temperature(resistance)
