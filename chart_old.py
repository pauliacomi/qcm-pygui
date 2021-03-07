import tkinter as tk

CHART_COLOR = '#e8e8ff'
PLOT_COLOR = 'black'


class Buffer():
    pass


class Plot(Buffer):
    """Class to represent a single plot on a Chart."""
    def __init__(self, chart, color, _id, length=128):
        Buffer.__init__(self, _id, length)
        self.color = color
        self.value = 0
        self.mark = 0
        self.chart = chart
        self.plot = chart.create_line(0, 0, 0, 1, fill=self.color, width=1)
        self.item_text = chart.create_text((0, 0),
                                           fill=self.color,
                                           anchor=tk.NW)


class Chart(tk.Canvas):
    """Class to represent a single graphic representation of data.

    It can show one or more data plots.
    """
    left_margin = 0

    def __init__(self, master, *args, **kwargs):
        tk.Canvas.__init__(
            self,
            master,
            background=CHART_COLOR,
            bd=2,
            relief=tk.GROOVE,
            cursor="crosshair",
            *args,
            **kwargs
        )

    def add_plot(self, plot_id, color=PLOT_COLOR):
        self.plot = Plot(self, color, plot_id)

    def plot_full(self, data):
        plot.replace(data)

    def plot_append(self, value):
        plot.update(value)