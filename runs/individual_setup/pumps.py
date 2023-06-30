from unitpy import Unit

import chembot

from runs.individual_setup.equipment_names import NamesSerial, NamesPump

# serial_pump_front = chembot.communication.Serial(NamesSerial.PUMP_FRONT, "COM11")
pump_front = chembot.equipment.pumps.SyringePumpHarvard(
    name=NamesPump.PUMP_FRONT,
    syringe=chembot.equipment.pumps.Syringe.get_syringe("hamilton_1010"),
    communication=NamesSerial.PUMP_FRONT,
    max_pull=20 * Unit.cm,
    max_pull_rate=20 * Unit("cm/min")
)
pump_front.activate()

# serial_pump_middle = chembot.communication.Serial(NamesSerial.PUMP_MIDDLE, $$$)
# pump_middle = chembot.equipment.pumps.SyringePumpHarvard(
#     name=NamesPump.PUMP_MIDDLE,
#     syringe=chembot.equipment.pumps.Syringe.get_syringe("hamilton_1010"),
#     communication=NamesSerial.PUMP_MIDDLE,
#     max_pull=20 * Unit.cm,
#     max_pull_rate=20 * Unit("cm/min")
# )
#
# serial_pump_back = chembot.communication.Serial(NamesSerial.PUMP_FRONT, $$$$)
# pump_back = chembot.equipment.pumps.SyringePumpHarvard(
#     name=NamesPump.PUMP_BACK,
#     syringe=chembot.equipment.pumps.Syringe.get_syringe("hamilton_1010"),
#     communication=NamesSerial.PUMP_BACK,
#     max_pull=20 * Unit.cm,
#     max_pull_rate=20 * Unit("cm/min")
# )


with chembot.utils.EquipmentManager() as manager:
    manager.add([serial_pump_front, pump_front])  # serial_pump_middle, pump_middle, serial_pump_back, pump_back
    manager.activate()
