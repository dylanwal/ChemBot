
from chembot.rabbitmq.messages import RabbitMessageRegister
from chembot.equipment.equipment_interface import EquipmentInterface


class EquipmentRegistry:
    def __init__(self):
        self.equipment: dict[str, EquipmentInterface] = dict()

    def register(self, message: RabbitMessageRegister):
        self.equipment[message.source] = message.equipment_interface

    def unregister(self, name: str):
        del self.equipment[name]
