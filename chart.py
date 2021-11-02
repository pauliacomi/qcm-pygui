import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")

from matplotlib import style
style.use("fast")

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.animation as animation

import numpy as np


class Chart():
    """Class to represent a single graphic representation of data.
    """
    def __init__(self, parent, *args, **kwargs):
        self.figure = Figure(dpi=100, figsize=(5, 3))
        self.plot = self.figure.add_subplot(111)
        self.plot.autoscale(True)

        self.maxt = 6000
        self.changet = 300

        self.xdata = []
        self.ydata = []
        self.line = Line2D(self.xdata, self.ydata, color='k', linewidth=1)
        self.plot.add_line(self.line)
        self.plot.set_xlim(0, self.maxt + self.changet)
        #

        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.draw()
        self.widget = self.canvas.get_tk_widget()

    def plot_full(self, x, y):
        self.xdata = x
        self.ydata = y
        self.line.set_data(self.xdata, self.ydata)
        self.plot.set_xlim(self.xdata[0], self.xdata[-1])
        self.plot.set_ylim(0.9 * min(self.ydata), 1.1 * max(self.ydata))

    def plot_append(self, value):
        if self.xdata:
            lastt = self.xdata[-1]
            if lastt > self.xdata[0] + self.maxt:  # reset the arrays
                self.xdata = self.xdata[self.changet:]
                self.ydata = self.ydata[self.changet:]
                self.plot.set_xlim(
                    self.xdata[0], self.xdata[0] + self.maxt + self.changet
                )

            t = self.xdata[-1] + 1
        else:
            t = 0
        self.xdata.append(t)
        self.ydata.append(value)

        self.plot.set_ylim(
            0.99999 * min(self.ydata), 1.00001 * max(self.ydata)
        )

        self.line.set_data(self.xdata, self.ydata)