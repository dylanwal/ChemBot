from typing import Iterable

import jsonpickle

from chembot.gui.gui_data import GUIData
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.rabbitmq.rabbit_http_messages import write_read_create_message
from chembot.master_controller.master_controller import MasterController
from chembot.equipment.equipment import Equipment
from chembot.equipment.equipment_interface import EquipmentRegistry


def get_equipment_registry() -> str:
    reply = write_read_create_message(
        RabbitMessageAction(
            destination="chembot." + MasterController.name,
            source=GUIData.name,
            action=MasterController.read_equipment_registry.__name__
        )
    )

    equipment_registry: EquipmentRegistry = reply.value
    return jsonpickle.dumps(equipment_registry)


def get_equipment_attributes(equipments: Iterable) -> str:
    data = {}
    for equipment in equipments:
        reply = write_read_create_message(
            RabbitMessageAction(
                destination="chembot." + equipment,
                source=GUIData.name,
                action=Equipment.read_all_attributes.__name__
            )
        )
        data[equipment] = reply.value

    return jsonpickle.dumps(data)


def get_equipment_update(equipments: Iterable) -> str:
    data = {}
    for equipment in equipments:
        reply = write_read_create_message(
            RabbitMessageAction(
                destination="chembot." + equipment,
                source=GUIData.name,
                action=Equipment.read_update.__name__
            )
        )
        data[equipment] = reply.value

    return jsonpickle.dumps(data)


def do_action(equipment: str, action: str, kwargs):
    message = RabbitMessageAction(
        destination="chembot." + equipment,
        source=GUIData.name,
        action=action,
        kwargs=kwargs
    )
    reply = write_read_create_message(message)

    return reply.value
