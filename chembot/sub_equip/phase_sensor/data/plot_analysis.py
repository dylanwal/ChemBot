import numpy as np
import matplotlib.pyplot as plt
import os
import re

from main_code.utils.plotting import color_list_norm
from main_code.sub_equip.phase_sensor.phase_sensor import PhaseSensor


# Loading data
file_prefix = "in_phase_sensor_"
files = [f for f in os.listdir(".") if re.match(fr'^({file_prefix})[0-9]+.*\.(csv)$', f)]


for file in files:
    try:
        data = np.vstack(data, np.loadtxt(open(file, "rb"), delimiter=",", skiprows=1))
    except NameError:
        data = np.loadtxt(open(file, "rb"), delimiter=",", skiprows=1)


gas = np.array(data[10, 1:])
liq = np.array(data[160, 1:])
phase = PhaseSensor.determine_phase(data[:, 1:], gas, liq)

fig, (ax1, ax2) = plt.subplots(2, 1)
ax1.set_xlabel('time (sec)')
ax1.set_ylabel('signal')
for line, color in zip(range(data[0, 1:].size), color_list_norm):
    ax1.plot(data[:, 0]/1_000_000, data[:, line+1], color=color)
    ax2.plot(data[:, 0]/1_000_000, phase[:, line], color=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()





