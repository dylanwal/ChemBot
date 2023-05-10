

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction, RabbitMessageCritical, RabbitMessageError, \
    RabbitMessageRegister, RabbitMessageReply
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog
from chembot.master_controller.registry import EquipmentRegistry
from chembot.gui.app import app


class GUI:
    name = "GUI"

    def __init__(self):
        self.rabbit = RabbitMQConnection(self.name)
        self.watchdog = RabbitWatchdog(self)

    @staticmethod
    def activate():
        app.run_server(debug=True)

    def write_deactivate(self):
        ...
