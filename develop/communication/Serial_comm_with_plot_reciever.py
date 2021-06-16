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
        self.setWindowTitle('Plotting data from serial connection.')

        # Generate docks
        self.d2 = Dock("Dock2", size=(2400, 1200))


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
        # self.d3.hideTitleBar()
        # self.w3 = pg.LayoutWidget()
        # self.d3.addWidget(self.w3)
        # self.b1 = QtWidgets.QPushButton('Start')
        # # self.b1.clicked.connect(self.clicked)
        # self.b2 = QtWidgets.QPushButton('Stop')
        # # self.b1.clicked.connect(self.clicked)
        # self.w3.addWidget(self.b1, row=0, col=0)
        # self.w3.addWidget(self.b2, row=0, col=1)
        #
        # self.l1 = pg.ValueLabel(siPrefix=True, suffix='fps')
        # self.l2 = pg.ValueLabel(siPrefix=True, suffix='count')
        # self.w3.addWidget(self.l1, row=1, col=0)
        # self.w3.addWidget(self.l2, row=1, col=1)
        # self.fps_time = time.time()


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




def window():
    app = QApplication([])
    win = MyWindow(app)
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    #global connection, data
    connection = serial.intialize_comm()
    connection.receive_data_labels()
    data = everything_data_numpy.intialize_dataframe(connection.num_data_points)
    window()

