"""
This code establishes a serial communication to an external devices and plots the reference_data in real time.
The code expects to receive a list of reference_data to be plotted.

"""

##

import time
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from pyqtgraph.dockarea import *
import pyqtgraph as pg
import numpy as np

# fixes scaling issues across monitors
import os
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

color_list = [
    [10, 36, 204],  # blue
    [172, 24, 25],  # red
    [6, 127, 16],  # green
    [251, 118, 35],  # orange
    [145, 0, 184],  # purple
    [255, 192, 0]  # yellow
]


class MyWindow(QMainWindow):
    def __init__(self, app):
        super(MyWindow, self).__init__()
        self.app = app
        # Generate window
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.resize(1200, 800)
        self.setWindowTitle('Plotting reference_data from serial connection.')
        # pg.setConfigOptions(antialias=True)    # nicer plots but slower code

        # Drop down menu
        bar = self.menuBar()
        file = bar.addMenu("File")
        file.addAction("New")
        file.addAction("save")
        file.addAction("quit")

        # Generate docks
        self.d2 = Dock("Dock2", size=(1200, 600), hideTitle=True)
        self.d3 = Dock("Dock3", size=(1200, 200), hideTitle=True)
        self.area.addDock(self.d2)  ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
        self.area.addDock(self.d3, 'bottom', self.d2)  # place d3 at bottom edge of d1


        # Dock 2 - plots
        self.w1 = pg.PlotWidget(title="Plot")
        self.d2.addWidget(self.w1)
        self.w1.setLabel('left', 'Signal', units='abs')
        self.w1.setLabel('bottom', 'Time', units='sec')

        self.num_lines = 6
        self.plot_points = 100
        self.w1_xdata = np.zeros(self.plot_points)
        self.w1_ydata = np.zeros([self.num_lines, self.plot_points])
        for i in range(self.num_lines):
            pen = pg.mkPen(color=color_list[i], width=3)
            exec(f"self.w1_plot_{i} = self.w1.plot(self.w1_xdata, self.w1_ydata[{i}, :], pen=pen)")


        # Dock 3 - Bottons
        self.w3 = pg.LayoutWidget()
        self.d3.addWidget(self.w3)
        self.b1 = QtWidgets.QPushButton('Start')
        # self.b1.clicked.connect(self.clicked)
        self.b2 = QtWidgets.QPushButton('Stop')
        # self.b1.clicked.connect(self.clicked)
        self.w3.addWidget(self.b1, row=0, col=0)
        self.w3.addWidget(self.b2, row=0, col=1)


        # Frames per second counter
        self.l1 = pg.ValueLabel(siPrefix=True, suffix='fps')
        self.l2 = pg.ValueLabel(siPrefix=True, suffix='count')
        self.w3.addWidget(self.l1, row=1, col=0)
        self.w3.addWidget(self.l2, row=1, col=1)
        self.fps_time = time.time()
        self.fps = 0



        # Update everything
        self.w1_timer = pg.QtCore.QTimer()
        self.w1_timer.timeout.connect(self.update_all)
        self.w1_timer.start(0)
        self.counter = 0

    def update_all(self):
        self.update_plots()
        if self.counter % 10 == 0:   # run every 10 loop
            self.update_labels()
        self.app.processEvents()
        self.counter += 1

    def update_plots(self):
        self.w1_xdata = np.roll(self.w1_xdata, -1)
        self.w1_ydata = np.roll(self.w1_ydata, -1)

        global in_phase_sensor
        new_data = in_phase_sensor.measure_mean(smooth=False)
        #print(new_data)
        self.w1_xdata[-1] = new_data[0]
        self.w1_ydata[:, -1] = new_data[1:]

        for i in range(self.num_lines):
            exec(f"self.w1_plot_{i}.setData(self.w1_xdata, self.w1_ydata[{i}, :])")

    def update_labels(self):
        now = time.time()
        dt = time.time() - self.fps_time
        self.fps_time = now
        a = 0.8
        self.fps = a*(10 / dt) + (1-a) * self.fps  # exponential smoothing
        self.l1.setValue(self.fps)
        self.l2.setValue(self.counter)

def main():
    from main_code import phase_sensor
    global in_phase_sensor
    in_phase_sensor = phase_sensor.PhaseSensor(name="in_phase_sensor",port="COM7", number_sensors=6)
    in_phase_sensor.get_mean()


def window():
    app = QApplication(sys.argv)
    win = MyWindow(app)
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    window()

