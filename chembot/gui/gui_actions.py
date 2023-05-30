from typing import Iterable

from chembot.gui.gui_data import GUIData
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.rabbitmq.rabbit_http_messages import write_and_read_message
from chembot.master_controller.master_controller import MasterController
from chembot.equipment.equipment import Equipment


def get_equipment_registry() -> dict[str, object]:  # JSON
    reply = write_and_read_message(
        RabbitMessageAction(
            destination="chembot." + MasterController.name,
            source=GUIData.name,
            action=MasterController.read_equipment_registry.__name__
        )
    )
    return reply["value"]


def get_equipment_update(equipments: Iterable) -> dict[str, object]:
    data = {}
    for equipment in equipments:
        reply = write_and_read_message(
            RabbitMessageAction(
                destination="chembot." + equipment,
                source=GUIData.name,
                action=Equipment.read_update.__name__
            )
        )
        data[equipment] = reply["value"]

    return data
