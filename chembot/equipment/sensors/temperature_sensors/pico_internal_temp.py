import logging

from unitpy import Quantity

from chembot.reference_data.pico_pins import PicoHardware
from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.communication.serial_pico import PicoSerial

from chembot.equipment.sensors.sensor import Sensor

logger = logging.getLogger(config.root_logger_name + ".temperature")


class TemperaturePICO(Sensor):
    def __init__(self,
                 name: str,
                 communication: str,
                 ):
        super().__init__(name)
        self.communication = communication
        self._pin = PicoHardware.pin_internal_temp

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def _stop(self):
        pass

    def write_measure(self) -> Quantity:
        message = RabbitMessageAction(self.communication, self.name, PicoSerial.read_internal_temperature)
        reply = self.rabbit.send_and_consume(message, error_out=True)
        return reply.value
