from unitpy import Unit

import chembot

from runs.launch_equipment.names import NamesPump

pump_one = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.ONE,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("norm_ject_22768"),
    port="COM11",
    max_pull=12 * Unit.cm,
)
# pump_front.activate()

pump_two = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.TWO,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("norm_ject_22768"),
    port="COM9",
    max_pull=12 * Unit.cm,
)

pump_three = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.THREE,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("KDS_SS_780802"),
    port="COM10",
    max_pull=17 * Unit.cm,
)

pump_four = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.FOUR,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("norm_ject_22768"),
    port="COM15",
    max_pull=12 * Unit.cm,
)


with chembot.utils.EquipmentManager() as manager:
    manager.add([pump_one, pump_two, pump_three, pump_four])
    manager.activate()
