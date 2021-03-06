"""
All graphs needed for the live display of recorded QCM data.
"""

import tkinter as tk
from datetime import datetime, timedelta
from typing import Iterable

from matplotlib import style

style.use("fast")

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.dates as mdates


class VerticalNavigationToolbar2Tk(NavigationToolbar2Tk):
    """Overridden regular toolbar to make it vertical."""
    def __init__(self, canvas, window):
        super().__init__(canvas, window, pack_toolbar=False)

    def _Button(self, text, image_file, toggle, command):
        """override _Button() to re-pack the toolbar button in vertical direction"""
        b = super()._Button(text, image_file, toggle, command)
        b.pack(side=tk.TOP)  # re-pack button in vertical direction
        return b

    def _Spacer(self):
        """# override _Spacer() to create vertical separator"""
        s = tk.Frame(self, width=26, relief=tk.RIDGE, bg="DarkGray", padx=2)
        s.pack(side=tk.TOP, pady=5)  # pack in vertical direction
        return s

    def set_message(self, s):
        """disable showing mouse position in toolbar"""
        pass


class Chart(tk.Frame):
    """Base chart class from tk.Frame with MPL graph and toolbar."""
    def __init__(self, parent, *args, xlabel=None, ylabel=None, **kwargs):
        """
        Initialize the chart.
        Names for the labels are parameters.
        """
        # init frame
        super().__init__(parent, *args, **kwargs)

        # data source
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

        # blitting components
        self._bg = None
        self._artists = []
        self.cid = self.canvas.mpl_connect("draw_event", self.on_draw)
        self.add_artist(self.line)
        self.add_artist(self.plot.xaxis)
        self.add_artist(self.plot.yaxis)

    def add_artist(self, art):
        """Add an artist to be animated."""
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update_plot(self):
        """Update the plot through blitting."""
        cv = self.canvas
        fig = self.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()

    def set_data(self, x: Iterable, y: Iterable):
        """Set all data. To be overridden in various sublasses."""

    def append_data(self, x: datetime, y: float):
        """Append point to existing data. To be overridden in various sublasses."""


class TraceChart(Chart):
    """Class to represent a single graphic representation of frequency scan data."""
    def __init__(self, parent, *args, xlabel=None, ylabel=None, **kwargs):
        """
        Initialize the chart.
        Names for the labels are parameters.
        """
        super().__init__(parent, *args, xlabel=xlabel, ylabel=ylabel, **kwargs)
        self.markx = [0, 0]
        self.marky = [-100, 100]
        self.markline = Line2D(self.markx, self.marky, color='r', linewidth=1)
        self.plot.add_line(self.markline)
        self.add_artist(self.markline)

    def set_data(self, x: Iterable, y: Iterable):
        """Take in all data from a sweep and save it."""
        self.xdata = x
        self.ydata = y
        self.line.set_data(self.xdata, self.ydata)
        self.plot.set_xlim(self.xdata[0], self.xdata[-1])

        mn = min(self.ydata)
        mx = max(self.ydata)
        xmx = x[y.index(mx)]

        mn = 1.1 * mn if mn < 0 else 0.9 * mn
        mx = 0.9 * mx if mx < 0 else 1.1 * mx
        self.plot.set_ylim(mn, mx)

        self.markx = [xmx, xmx]
        self.markline.set_data(self.markx, self.marky)


class MarkerChart(Chart):
    """Class to represent a single graphic representation of resonance frequency in time."""
    def __init__(self, parent, *args, xlabel=None, ylabel=None, **kwargs):
        super().__init__(parent, *args, xlabel=xlabel, ylabel=ylabel, **kwargs)
        """
        Initialize the chart.
        Names for the labels are parameters.
        """

        self.maxt = 300  # total store time in minutes
        self.dispt = 60  # max display time in minutes
        self.displast = None  # where last point is displayed
        self.miny = 9975000  # default minimum frequency on y scale
        self.maxy = 10010000  # default maximum frequency on y scale

        self.plot.set_xlim(0, 0.005)
        self.plot.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        self.plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    def set_ylim(self, miny=9975000, maxy=10010000):
        """Set the graph frequency limits."""
        self.miny = miny
        self.maxy = maxy
        self.plot.set_ylim(self.miny, self.maxy)

    def append_data(self, x: datetime, y: float):
        """Append the new frequency max to all measurements."""
        if self.xdata:
            first = self.xdata[0]
            last = self.xdata[-1]
            dtime = (last - first).seconds / 60

            if dtime > self.maxt:  # cut a third of the arrays

                cut = int(len(self.xdata) / 3)
                self.xdata = self.xdata[cut:]
                self.ydata = self.ydata[cut:]

            last = self.xdata[-1]
            first = self.displast
            dtime = (last - first).seconds / 60
            if dtime > self.dispt:  # rescale display
                self.displast = self.displast + timedelta(minutes=self.dispt / 2)
                self.plot.set_xlim(self.displast, self.displast + timedelta(minutes=self.dispt))

        else:
            self.displast = x
            self.plot.set_xlim(x, x + timedelta(minutes=self.dispt))

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
