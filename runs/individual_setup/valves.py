
import chembot

from runs.individual_setup.names import NamesValves, NamesSerial

config_front = chembot.equipment.valves.ValveConfiguration.get_configuration("4L")
config_front.ports[0].name = "to_pump"
config_front.ports[1].name = "to_reactor"
config_front.ports[2].name = "to_fill"
config_front.ports[3].name = "pump"
config_front.ports[3].blocked = True

config_front.positions[0].setting = 1638
config_front.positions[1].setting = 3932
config_front.positions[2].setting = 6225
config_front.positions[3].setting = 8191

valve_front = chembot.equipment.valves.ValveServo(
    name=NamesValves.VALVE_FRONT,
    communication=NamesSerial.PICO2,
    configuration=config_front,
    pin=15,
)

config_middle = chembot.equipment.valves.ValveConfiguration.get_configuration("4L")
config_middle.ports[0].name = "to_pump"
config_middle.ports[1].name = "to_reactor"
config_middle.ports[2].name = "to_fill"
config_middle.ports[3].name = "pump"
config_middle.ports[3].blocked = True

config_middle.positions[0].setting = 1638
config_middle.positions[1].setting = 3932
config_middle.positions[2].setting = 6225
config_middle.positions[3].setting = 8191

valve_middle = chembot.equipment.valves.ValveServo(
    name=NamesValves.VALVE_MIDDLE,
    communication=NamesSerial.PICO2,
    configuration=config_middle,
    pin=15,
)

config_back = chembot.equipment.valves.ValveConfiguration.get_configuration("4L")
config_back.ports[0].name = "to_pump"
config_back.ports[1].name = "to_reactor"
config_back.ports[2].name = "to_fill"
config_back.ports[3].name = "pump"
config_back.ports[3].blocked = True

config_back.positions[0].setting = 1638
config_back.positions[1].setting = 3932
config_back.positions[2].setting = 6225
config_back.positions[3].setting = 8191

valve_back = chembot.equipment.valves.ValveServo(
    name=NamesValves.VALVE_BACK,
    communication=NamesSerial.PICO2,
    configuration=config_back,
    pin=15,
)


with chembot.utils.EquipmentManager() as manager:
    manager.add([valve_front, valve_middle, valve_back])
    manager.activate()
