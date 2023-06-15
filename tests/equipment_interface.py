
from chembot.communication import PicoSerial
from chembot.equipment.lights import LightPico

from chembot.equipment.equipment_interface import get_equipment_interface


def main():
    interface_pico_serial = get_equipment_interface(PicoSerial)
    interface_light_pico = get_equipment_interface(LightPico)


if __name__ == "__main__":
    main()
