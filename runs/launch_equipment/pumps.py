from unitpy import Unit

import chembot

from runs.launch_equipment.names import NamesPump

pump_front = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.FRONT,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("norm_ject_22768"),
    port="COM11",
    max_pull=12 * Unit.cm,
)
# pump_front.activate()

pump_middle = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.MIDDLE,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("norm_ject_22768"),
    port="COM9",
    max_pull=12 * Unit.cm,
)

pump_back = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.BACK,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("KDS_SS_780802"),
    port="COM10",
    max_pull=12 * Unit.cm,
)


with chembot.utils.EquipmentManager() as manager:
    manager.add([pump_front, pump_middle, pump_back])
    manager.activate()
