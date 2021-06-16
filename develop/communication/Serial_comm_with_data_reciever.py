"""
This code establishes a serial communication to an external devices and plots the data in real time.
The code expects to receive a list of data to be plotted.

"""

##

import time
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from pyqtgraph.dockarea import *
import pyqtgraph as pg
import numpy as np
import math

#
import comm_PC_side
import everything_data_numpy

class MyWindow(QMainWindow):
    def __init__(self, app):
        super(MyWindow, self).__init__()
        self.app = app
        self.initUI()

    def initUI(self):
        # Generate window
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.resize(2400, 1200)
        self.setWindowTitle('Self Racing Car')

        # Generate docks
        self.d1 = Dock("Dock1", size=(1200, 600))
        self.d2 = Dock("Dock2", size=(1200, 600))
        self.d3 = Dock("Dock3", size=(1200, 200))
        self.d4 = Dock("Dock4 ", size=(1200, 600))
        self.area.addDock(self.d1,'left')  ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
        self.area.addDock(self.d2, 'right')  ## place d2 at right edge of dock area
        self.area.addDock(self.d3, 'bottom', self.d1)  ## place d3 at bottom edge of d1
        self.area.addDock(self.d4, 'bottom', self.d2)  ## place d4 at right edge of dock area

        # Dock 1 - Car model
        self.d1.hideTitleBar()
        self.w1 = pg.PlotWidget()
        self.d1.addWidget(self.w1)
        self.car_draw = self.car_drawing(self.w1)


        # Dock 2 - Distance plot
        self.d2.hideTitleBar()
        self.w2 = pg.PlotWidget(title="Distance sensors")
        self.d2.addWidget(self.w2)
        self.w2.setLabel('left', 'Distance', units='cm')
        self.w2.setLabel('bottom', 'Time', units='sec')
        self.plot_points = 100
        self.w2_xdata = np.zeros([self.plot_points])
        self.w2_ydata = np.zeros([self.plot_points])
        pen_w2_1 = pg.mkPen(color=(0, 0, 255), width=5)
        self.w2_plot = self.w2.plot(self.w2_xdata, self.w2_ydata, pen=pen_w2_1)
        # pen_w2_2 = pg.mkPen(color=(255, 0, 0), width=5)
        # self.w2_plot2 = self.w2.plot(self.w2_xdata, self.w2_ydata, pen=pen_w2_2)
        # pen_w2_3 = pg.mkPen(color=(0, 255, 0), width=5)
        # self.w2_plot3 = self.w2.plot(self.w2_xdata, self.w2_ydata, pen=pen_w2_3)


        # Dock 3 - Bottons
        self.d3.hideTitleBar()
        self.w3 = pg.LayoutWidget()
        self.d3.addWidget(self.w3)
        self.b1 = QtWidgets.QPushButton('Start')
        # self.b1.clicked.connect(self.clicked)
        self.b2 = QtWidgets.QPushButton('Stop')
        # self.b1.clicked.connect(self.clicked)
        self.w3.addWidget(self.b1, row=0, col=0)
        self.w3.addWidget(self.b2, row=0, col=1)

        self.l1 = pg.ValueLabel(siPrefix=True, suffix='fps')
        self.l2 = pg.ValueLabel(siPrefix=True, suffix='count')
        self.w3.addWidget(self.l1, row=1, col=0)
        self.w3.addWidget(self.l2, row=1, col=1)
        self.fps_time = time.time()

        # Dock 4 - Accelerometer plot
        self.d4.hideTitleBar()
        self.w4 = pg.PlotWidget(title="Accelerometer sensors")
        self.d4.addWidget(self.w4)
        self.w4.setLabel('left', 'Acceleration', units='?')
        self.w4.setLabel('bottom', 'Time', units='sec')
        plot_points = 100
        self.w4_xdata = np.zeros([plot_points])
        self.w4_ydata = np.zeros([plot_points])
        pen_w4_1 = pg.mkPen(color=(0, 0, 255), width=5)
        self.w4_plot = self.w4.plot(self.w4_xdata, self.w4_ydata, pen=pen_w4_1)
        pen_w4_2 = pg.mkPen(color=(0, 255, 0), width=5)
        self.w4_plot2 = self.w4.plot(self.w4_xdata, self.w4_ydata, pen=pen_w4_2)
        pen_w4_3 = pg.mkPen(color=(255, 0, 0), width=5)
        self.w4_plot3 = self.w4.plot(self.w4_xdata, self.w4_ydata, pen=pen_w4_3)

        # Update everything
        self.counter = 0
        self.w2_timer = pg.QtCore.QTimer()
        self.w2_timer.timeout.connect(self.update_all)
        self.w2_timer.start(0)

    def update_all(self):
        global connection, data
        data.add(connection.receive_data())
        connection.send_data()
        print('hi')
        self.update_plots()
        if self.counter % 10 == 0:   # run every 10 loop
            self.update_labels()
        self.app.processEvents()
        self.counter += 1


    def update_plots(self):
        global data

        if self.counter < self.plot_points:
            xdata = data.df[:data.data_size, 0]
            ydata1 = data.df[:data.data_size, 1]
            ydata2 = data.df[:data.data_size, 2]
            ydata3 = data.df[:data.data_size, 3]
            ydata4 = data.df[:data.data_size, 4]
            #ydata5 = data.df[:data.data_size, 5]
            #ydata6 = data.df[:data.data_size, 6]
        else:
            xdata = data.df[data.data_size - self.plot_points:data.data_size, 0]
            ydata1 = data.df[data.data_size - self.plot_points:data.data_size, 1]
            ydata2 = data.df[data.data_size - self.plot_points:data.data_size, 2]
            ydata3 = data.df[data.data_size - self.plot_points:data.data_size, 3]
            ydata4 = data.df[data.data_size - self.plot_points:data.data_size, 4]
            #ydata5 = data.df[data.data_size - self.plot_points:data.data_size, 5]
            #ydata6 = data.df[data.data_size - self.plot_points:data.data_size, 6]

        self.w2_plot.setData(xdata, ydata1)
        #self.w2_plot2.setData(xdata, ydata5)
        #self.w2_plot3.setData(xdata, ydata6)
        self.w4_plot.setData(xdata, ydata2)
        self.w4_plot2.setData(xdata, ydata3)
        self.w4_plot3.setData(xdata, ydata4)


    def update_labels(self):
        now = time.time()
        dt = time.time() - self.fps_time
        self.fps_time = now
        self.fps = 10 / dt
        self.l1.setValue(self.fps)
        self.l2.setValue(self.counter)

    class car_drawing():
        def __init__(self, win_in):
            # car
            self.car_window = win_in
            L = 23
            W = 15
            self.car_body_pen = pg.mkPen(color=(255, 0, 0), width=30)
            self.car_body_top = self.car_window.plot([0, W, W, 0, 0], [0, 0, -L, -L, 0], pen=self.car_body_pen)
            # self.car_tire(-0.5, -3)
            # self.car_tire(-0.5, -15)
            # self.car_tire(13.5, -3)
            # self.car_tire(13.5, -15)
            self.sensor_dash(120, 120, 3, -3)
            self.sensor_dash(90, 250, W/2, -3)
            self.sensor_dash(60, 120, W-3, -3)
            self.sensor_dash(270, 125, W/2, -L)

        def car_tire(self, x_top, y_top):
            L = 7
            W = 2
            car_tire_pen = pg.mkPen(color=(255, 255, 255), width=15)
            self.car_window.plot([x_top+0, x_top+W, x_top+W, x_top+0, x_top+0],[y_top+0, y_top+0, y_top+-L, y_top+-L, y_top+0], pen=car_tire_pen)

        def sensor_dash(self, angle, max_distance, x_pos, y_pos):
            self.car_window.plot([x_pos], [y_pos], symbol='o', symbolSize=10, symbolBrush='b')
            sensor_dash = pg.mkPen(color=(150, 150, 150), width=1, style=QtCore.Qt.DashLine)
            angle = angle / 180 * math.pi
            x_cap = math.cos(angle)*max_distance
            y_cap = math.sin(angle)*max_distance
            self.car_window.plot([x_pos, x_pos+x_cap], [y_pos, y_pos+y_cap], pen=sensor_dash)
            dash_length = 5
            c = math.sqrt(dash_length**2+max_distance**2)
            dash_angle = math.acos(max_distance/c)
            dash_dy1 = math.sin(angle+dash_angle)*c
            dash_dx1 = math.cos(angle+dash_angle)*c
            dash_dy2 = math.sin(angle-dash_angle)*c
            dash_dx2 = math.cos(angle-dash_angle)*c
            self.car_window.plot([x_pos + dash_dx1, x_pos + dash_dx2], [y_pos + dash_dy1, y_pos + dash_dy2], pen=sensor_dash)



def window():
    app = QApplication([])
    win = MyWindow(app)
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    #global connection, data
    connection = comm_PC_side.intialize_comm()
    connection.receive_data_labels()
    data = everything_data_numpy.intialize_dataframe(connection.num_data_points)
    window()

