
from unitpy import Unit

import chembot

from runs.launch_equipment.names import NamesEquipment


bath = chembot.equipment.temperature_control.PolyRecirculatingBath(
    name=NamesEquipment.BATH,
    comport="COM19",
    temp_limits=(5 * Unit.degC, 60 * Unit.degC)
)

bath.activate()
