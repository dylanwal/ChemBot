from unitpy import Unit

import chembot

from runs.individual_setup.equipment_names import NamesPump

pump_front = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.PUMP_FRONT,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("hamilton_1010"),
    port="COM11",
    max_pull=20 * Unit.cm,
)
pump_front.activate()

pump_middle = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.PUMP_MIDDLE,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("hamilton_1010"),
    port="COM11",
    max_pull=20 * Unit.cm,
)

pump_back = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.PUMP_BACK,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("hamilton_1010"),
    port="COM11",
    max_pull=20 * Unit.cm,
)


with chembot.utils.EquipmentManager() as manager:
    manager.add([pump_front, pump_middle, pump_back])
    manager.activate()
