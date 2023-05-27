
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.rabbitmq.rabbit_http_messages import write_and_read_message
from chembot.gui.gui_data import GUIData
from chembot.master_controller.master_controller import MasterController


def equipment_registry() -> dict[str, object]:  # JSON
    return write_and_read_message(
        RabbitMessageAction(MasterController.name, GUIData.name, "read_equipment_status")
    )


# def equipment_status(self) -> dict[str, EquipmentState]:
#     return {k: v.state for k, v in self.equipment_registry.equipment.items()}

