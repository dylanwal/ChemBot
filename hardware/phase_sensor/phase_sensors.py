def measure_norm(self):
    data = [0, 0, 0, 0]
    for i, sensor in enumerate(self.sensors):
        data[i] = (sensor.measure() - sensor.liq) / (sensor.gas - sensor.liq)

    return data


def measure_phase(self):
    phase = [0, 0, 0, 0]
    for i, sensor in enumerate(self.sensors):
        phase[i] = self.determine_phase(sensor.measure(), sensor.gas, sensor.liq)

    return phase

@staticmethod
def determine_phase(value, gas, liq):
    gas_diff = abs(value - gas)
    liq_diff = abs(value - liq)
    if gas_diff < liq_diff:
        return "gas"

    return "liquid"