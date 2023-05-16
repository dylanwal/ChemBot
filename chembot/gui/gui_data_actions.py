
class GUIData:
    name = "GUI"
    pulse = 0.01
    LOGO = "assets/icon-research-catalysis-white.svg"
    default_refresh_rate = 2
    refresh_rates = (1, 2, 5, 10, 30)




    # @property
    # def equipment_registry(self) -> EquipmentRegistry:
    #     if self._equipment_registry is None:  # or self._time_last_updated + self.update_rate < time.time()
    #         # self._time_last_updated = time.time()
    #         reply = self.rabbit.send_and_consume(
    #             RabbitMessageAction(MasterController.name, self.name, "read_equipment_status"),
    #             timeout=2,
    #             error_out=True
    #         )
    #         self._equipment_registry = reply.value
    #
    #     return self._equipment_registry
    #
    # @property
    # def equipment_status(self) -> dict[str, EquipmentState]:
    #     return {k: v.state for k, v in self.equipment_registry.equipment.items()}
    #
