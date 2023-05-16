
from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction, RabbitMessageCritical, RabbitMessageError, \
    RabbitMessageRegister, RabbitMessageReply
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog
from chembot.master_controller.registry import EquipmentRegistry


class GUIData:
    LOGO = "assets/icon-research-catalysis-white.svg"

    def __init__(self):
        self.equipment_registry = None


class GUIInterface:
    name = "GUI"

    def __init__(self, app):
        self.app =app
        self.data = GUIData()
        self.rabbit = RabbitMQConnection("GUI")
        self.watchdog = RabbitWatchdog(self)

    def read_equipment_registry(self):
        ...
