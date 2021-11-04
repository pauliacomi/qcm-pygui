import tkinter as tk
from datetime import datetime, timedelta
from typing import Iterable

from matplotlib import style

style.use("fast")

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.dates as mdates


class VerticalNavigationToolbar2Tk(NavigationToolbar2Tk):
    def __init__(self, canvas, window):
        super().__init__(canvas, window, pack_toolbar=False)

    # override _Button() to re-pack the toolbar button in vertical direction
    def _Button(self, text, image_file, toggle, command):
        b = super()._Button(text, image_file, toggle, command)
        b.pack(side=tk.TOP)  # re-pack button in vertical direction
        return b

    # override _Spacer() to create vertical separator
    def _Spacer(self):
        s = tk.Frame(self, width=26, relief=tk.RIDGE, bg="DarkGray", padx=2)
        s.pack(side=tk.TOP, pady=5)  # pack in vertical direction
        return s

    # disable showing mouse position in toolbar
    def set_message(self, s):
        pass


class TraceChart(tk.Frame):
    """Class to represent a single graphic representation of data.
    """
    def __init__(self, parent, xlabel=None, ylabel=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.xdata = []
        self.ydata = []

        # init mpl figure/line
        self.figure = Figure(dpi=100, figsize=(5, 3), tight_layout=True)
        self.plot = self.figure.add_subplot(111)
        self.plot.autoscale(True)
        if xlabel:
            self.plot.set_xlabel(xlabel)
        if ylabel:
            self.plot.set_ylabel(ylabel)

        self.line = Line2D(self.xdata, self.ydata, color='k', linewidth=0.8)
        self.plot.add_line(self.line)

        # init mpl tk backend
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()

        self.toolbar = VerticalNavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        self.canvas_widget = self.canvas.get_tk_widget()

        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
        self.canvas_widget.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

    def update(self, x: Iterable, y: Iterable):
        self.xdata = x
        self.ydata = y
        self.line.set_data(self.xdata, self.ydata)
        self.plot.set_xlim(self.xdata[0], self.xdata[-1])
        self.plot.set_ylim(0.9 * min(self.ydata), 1.1 * max(self.ydata))


class MarkerChart(tk.Frame):
    """Class to represent a single graphic representation of data.
    """
    def __init__(self, parent, xlabel=None, ylabel=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.maxt = 10  # max displayed in minutes
        self.changet = 300
        self.xdata = []
        self.ydata = []

        self.miny = 9975000
        self.maxy = 10010000

        # init mpl figure/line
        self.figure = Figure(dpi=100, figsize=(5, 3), tight_layout=True)
        self.plot = self.figure.add_subplot(111)
        self.plot.autoscale(True)
        if xlabel:
            self.plot.set_xlabel(xlabel)
        if ylabel:
            self.plot.set_ylabel(ylabel)
        self.plot.set_ylim(self.miny, self.maxy)

        self.line = Line2D(self.xdata, self.ydata, color='k', linewidth=0.8)
        self.plot.add_line(self.line)

        # init mpl tk backend
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()

        self.toolbar = VerticalNavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        self.canvas_widget = self.canvas.get_tk_widget()

        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
        self.canvas_widget.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.plot.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
        self.plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    def update(self, x: datetime, y: float):

        if self.xdata:
            last = self.xdata[-1]
            first = self.xdata[0]
            dtime = (last - first).seconds / 60
            if dtime > self.maxt:  # reset the arrays
                self.xdata = self.xdata[self.changet:]
                self.ydata = self.ydata[self.changet:]
                self.plot.set_xlim(
                    self.xdata[0], self.xdata[0] + self.maxt + self.changet
                )
        else:
            self.plot.set_xlim(x, x + timedelta(minutes=self.maxt))

        self.xdata.append(x)
        self.ydata.append(y)

        rescale = False
        if min(self.ydata) < self.miny:
            rescale = True
            self.miny = 0.99999 * min(self.ydata)
        if max(self.ydata) > self.maxy:
            rescale = True
            self.maxy = 1.00001 * max(self.ydata)
        if rescale:
            self.plot.set_ylim(self.miny, self.maxy)

        self.line.set_data(self.xdata, self.ydata)
