import time
from dataclasses import dataclass


def volt_to_temp(volts):
    if volts == 0:
        return 0
    ohms = ((1 / volts) * 3300) - 1000  # calculate the ohms of the thermististor
    lnohm = log1p(ohms)  # take ln(ohms)

    # a, b, & c values from http://www.thermistor.com/calculators.php
    # using curve R (-6.2%/C @ 25C) Mil Ratio X
    a = 0.002197222470870
    b = 0.000161097632222
    c = 0.000000125008328

    # Steinhart Hart Equation
    # T = 1/(a + b[ln(ohm)] + c[ln(ohm)]^3)
    t1 = (b * lnohm)  # b[ln(ohm)]
    c2 = c * lnohm  # c[ln(ohm)]
    t2 = pow(c2, 3)  # c[ln(ohm)]^3
    temp = 1 / (a + t1 + t2)  # calculate temperature_sensors

    temp_c = temp - 273.15 - 4  # K to C
    # the -4 is error correction for bad python math
    return temp_c

@dataclass
class Thermistor:
    B_value: (float, int)
    B_min: (float, int)
    B_max: (float, int)
    min_temp: (float, int)
    max_temp: (float, int)

    def volt_to_temp(self, volts: (float, int)) -> (float, int):
        if volts == 0:
            return 0
        ohms = volts_to_ohms(volts)  # calculate the ohms of the thermistor
        lnohm = log1p(ohms)  # take ln(ohms)


thermister = Thermistor(
    B_value=3435,  # K
    B_min=25,  # K
    B_max=85,  # K
    min_temp=-40,  # C
    max_temp=125,  # C
)


def analog_to_volt(num: float, supply_volt: float = 3.3, res: int = 65536) -> float:
    return num * supply_volt / res


def volts_to_ohms(volts: float, resistor: (float, int) = 10000, resistor_order: bool = True, supply_volt: float = 3.3):
    """
    For a voltage divider

    V_in->R1->(V_out)->R2->ground
    order = True -> solve for R1
    order = False -> sovle for R2

    """
    if resistor_order:
        return resistor*(supply_volt/volts - 1)

    return resistor/(supply_volt/volts - 1)


def main():
    test_serial = connect_serial('COM4')
    analog_pin = 1
    try:
        for i in range(10):
            # send
            mes = "t" + str(analog_pin).zfill(2) + "\r"
            test_serial.write(mes.encode())
            # receive
            mes = test_serial.read_until()
            if mes[0] == "t":
                analog_value = float(mes[1:])
                volts = analog_to_volt(analog_value)

                # process
                print(f"{i}\t{analog_value}")
            else:
                print(mes)

            time.sleep(0.3)

    finally:
        mes = "e" + "\r"
        test_serial.write(mes.encode())
        print(test_serial.read_until())
        print("lights off, program done")


if __name__ == "__main__":
    main()
