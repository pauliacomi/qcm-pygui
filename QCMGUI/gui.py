"""The graphical user interface, built in TK."""

import pathlib
import sys
import datetime as dt

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as tkMessageBox
import tkinter.scrolledtext as tkScrolledText
from typing import Iterable

from chart import TraceChart, MarkerChart
from config import Config

NWE = tk.N + tk.W + tk.E
PADX = 5
PADY = 5


class MainWindow(ttk.Frame):
    """Class for the main program window."""
    def __init__(
        self,
        parent: tk.Tk,
        config: Config,
        wd: pathlib.Path,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.wd = wd
        self.parent = parent

        self.queue = None  # event queue reference
        self.queue_event = None  # event queue trigger
        self.quit_event = None  # exit event

        self.instruments = ("", )
        self.instrument = tk.StringVar(self)
        self.instrument.set("")

        self.reading = False
        self.recording = False
        self.configure_window()
        self.create_layout()

    ##################
    #### GUI config
    ##################

    def configure_window(self):
        """Global window settings and shortcuts."""
        top = self.winfo_toplevel()
        top.geometry('700x800+100+100')

        self.parent.title("QCM controller")
        self.parent.protocol('WM_DELETE_WINDOW', self.signal_close)
        self.parent.iconbitmap(self.wd / 'qcm.ico')
        self.parent.bind('<Return>', self.send_command)
        self.parent.bind('<Escape>', self.signal_close)

        self.pack(side='top', fill='both', expand=True)

    def create_layout(self):
        """Initialize the window layout."""
        # the layout is 5 rows:
        #    row 0 = menubar
        #    row 1 = control buttons
        #    row 2 = graphs etc - expandable
        #    row 3 = output
        #    row 4 = ipt_visa
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=3)
        self.rowconfigure(3, weight=2)
        self.rowconfigure(4, weight=0)

        # all expanding
        self.columnconfigure(0, weight=1)

        # # construct the widgets
        self.create_menu(row=0)
        self.create_controls(row=1)
        self.create_graph(row=2)
        self.create_output(row=3)
        self.create_input(row=4)

    def create_menu(self, row):
        """Menu row."""
        self.menu_bar = tk.Frame(self, bd=2)
        self.menu_bar.grid(row=row, column=0, sticky=NWE, columnspan=2)

        mbutton = ttk.Menubutton(self.menu_bar, text='File', underline=0)
        mbutton.pack(side=tk.LEFT)
        menu = tk.Menu(mbutton, tearoff=0)
        menu.add_command(label='Quit', command=self.signal_close)
        mbutton['menu'] = menu

        mbutton = ttk.Menubutton(self.menu_bar, text='Help', underline=0)
        mbutton.pack(side=tk.LEFT)
        menu = tk.Menu(mbutton, tearoff=0)
        menu.add_command(label='About', command=self.about)
        mbutton['menu'] = menu

    def create_controls(self, row):
        """Controls row."""
        self.ctrl_row = ttk.Frame(self)
        self.ctrl_row.grid(row=row, column=0)

        self.lbl_instr = tk.Label(self.ctrl_row)
        self.lbl_instr["text"] = "Instrument:"
        self.lbl_instr.grid(column=0, row=0, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        self.edt_instr = tk.OptionMenu(self.ctrl_row, self.instrument, *self.instruments)
        self.edt_instr.configure(anchor='w')
        self.edt_instr.grid(
            column=1, row=0, columnspan=2, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10
        )

        self.btn_connect = ttk.Button(self.ctrl_row)
        self.btn_connect["text"] = "Connect"
        self.btn_connect["command"] = self.task_connect
        self.btn_connect.grid(column=3, row=0, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        #

        self.lbl_setup = tk.Label(self.ctrl_row)
        self.lbl_setup["text"] = "Setup:"
        self.lbl_setup.grid(column=0, row=1, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        self.ipt_start = tk.Entry(self.ctrl_row, width=10)
        self.ipt_start.insert(0, self.config.get('start'))
        self.ipt_start.grid(column=1, row=1, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        self.ipt_stop = tk.Entry(self.ctrl_row, width=10)
        self.ipt_stop.insert(0, self.config.get('stop'))
        self.ipt_stop.grid(column=2, row=1, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        self.btn_running = ttk.Button(self.ctrl_row)
        self.btn_running["text"] = "Prime"
        self.btn_running["command"] = self.task_configure
        self.btn_running.grid(column=3, row=1, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        #

        self.lbl_run = tk.Label(self.ctrl_row)
        self.lbl_run["text"] = "Acquisition:"
        self.lbl_run.grid(column=0, row=2, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        self.btn_acquire = ttk.Button(self.ctrl_row)
        self.btn_acquire["text"] = "Read Start"
        self.btn_acquire["command"] = self.task_toggle_read
        self.btn_acquire.grid(column=1, row=2, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

        self.btn_record = ttk.Button(self.ctrl_row)
        self.btn_record["text"] = "Record Start"
        self.btn_record["command"] = self.task_toggle_record
        self.btn_record.grid(column=2, row=2, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)

    def create_graph(self, row):
        """Graphs row."""
        self.chart_row = tk.Frame(self, padx=PADX, pady=PADY)
        self.chart_row.grid(row=row, column=0, sticky=tk.NSEW)

        # Create the two figures
        self.plot_trace = TraceChart(
            self.chart_row,
            xlabel="Frequency [Hz]",
            ylabel="Power [mV]",
        )
        self.plot_trace.grid(row=0, column=0, sticky=tk.NSEW)

        separator = ttk.Separator(self.chart_row, orient='horizontal')
        separator.grid(row=1, column=0, sticky="")

        self.plot_mark = MarkerChart(
            self.chart_row,
            xlabel="Time",
            ylabel="Frequency [Hz]",
        )
        self.plot_mark.set_ylim(
            miny=float(self.config.get('start')),
            maxy=float(self.config.get('stop')),
        )
        self.plot_mark.grid(row=2, column=0, sticky=tk.NSEW)

        # Allow charts to expand horizontally
        self.chart_row.columnconfigure(0, weight=1)

        # allow charts to expand vertically
        self.chart_row.rowconfigure(0, weight=1)
        self.chart_row.rowconfigure(2, weight=1)

    def create_output(self, row):
        """Output log row."""
        self.output_row = ttk.Frame(self)
        self.output_row.grid(row=row, column=0, sticky=tk.NSEW)

        self.output = tkScrolledText.ScrolledText(self.output_row)
        self.output.grid(row=0, column=0, pady=PADY, padx=PADX, sticky=NWE)

        # Making the text read only
        self.output.configure(state='disabled')

        self.output_row.columnconfigure(0, weight=1)

    def create_input(self, row):
        """Input commands row."""
        self.input_row = ttk.Frame(self)
        self.input_row.grid(row=row, column=0, sticky=tk.NSEW)

        self.ipt_visa = tk.Entry(self.input_row)
        self.ipt_visa.grid(row=0, column=0, columnspan=1, pady=PADY, padx=PADX, sticky=NWE)
        self.btn_input = ttk.Button(self.input_row)
        self.btn_input["text"] = "Send command"
        self.btn_input["command"] = self.send_command
        self.btn_input.grid(row=0, column=1, sticky=tk.SW, padx=PADX, pady=PADY, ipadx=10)
        self.input_row.columnconfigure(0, weight=1)

    ##################
    #### Gui callbacks
    ##################

    def about(self):
        """Msgbox with info."""
        tkMessageBox.showinfo(
            'About',
            "Record QCM over Ethernet using pyVISA \nPaul Iacomi 2021\nFor updates check https://github.com/pauliacomi/qcm-pygui"
        )

    def close(self):
        """Close program."""
        print("Window asked to close.")
        self.parent.quit()
        print("Window closed.")

    def signal_close(self):
        """Send a signal to the queue to stop everything and close."""
        print("Ask shutdown.")
        self.config.save()
        self.queue_event.set()
        self.quit_event.set()

    ##################
    #### Control send
    ##################

    def send_command(self, *args, **kwargs):
        """Send a general VISA command to the connected instrument."""
        cmd = self.ipt_visa.get()
        self.ipt_visa.delete(0, tk.END)

        self.queue.put(('ctrl', {'task': 'run_cmd', 'cmd': cmd}))
        self.queue_event.set()

        self.log(f"Command sent: \"{cmd}\".")

    def task_configure(self):
        """Send a task to the controller that configures the instrument."""
        start = float(self.ipt_start.get())
        stop = float(self.ipt_stop.get())
        self.config.set('start', start)
        self.config.set('stop', stop)
        self.plot_mark.set_ylim(start, stop)
        self.queue.put(('ctrl', {'task': 'configure', 'start': start, 'stop': stop}))
        self.queue_event.set()

    def task_connect(self):
        """Send a task to the controller that connects to the instrument."""
        instrument = self.instrument.get()
        self.queue.put(('ctrl', {'task': 'connect', 'instrument': instrument}))
        self.queue_event.set()

        self.log(f"Connecting to {instrument}.")

        if instrument != self.config.get('instrument'):
            self.config.set('instrument', instrument)
            self.log("Instrument set as default.")

    def task_toggle_read(self):
        """Send a task to the controller that toggles whether the data is read or not."""
        if self.reading:
            self.queue.put(('ctrl', {'task': 'stop_measure'}))
            self.btn_acquire["text"] = "Read Start"
            self.reading = False
            self.log("Stopped reading.")
        else:
            self.queue.put(('ctrl', {'task': 'start_measure'}))
            self.btn_acquire["text"] = "Read Stop"
            self.reading = True
            self.log("Started reading.")
        self.queue_event.set()

    def task_toggle_record(self):
        """Send a task to the controller that toggles whether the data is recorded or not."""
        if self.reading:
            if self.recording:
                self.queue.put(('ctrl', {'task': 'stop_record'}))
                self.btn_record["text"] = "Record Start"
                self.recording = False
                self.log("Stopped recording.")
            else:
                self.queue.put(('ctrl', {'task': 'start_record'}))
                self.btn_record["text"] = "Record Stop"
                self.recording = True
                self.log("Started recording.")
            self.queue_event.set()

        else:
            self.log("Nothing to record, start reading first.")

    def task_query_instruments(self):
        """Send a task to the controller that queries all VISA instruments."""
        self.queue.put(('ctrl', {'task': 'query_instruments'}))
        self.queue_event.set()

    def task_update_charts(self):
        """Send a task to the controller that updates the graph."""
        self.queue.put(('disp', {'task': 'update_chart'}))
        self.queue_event.set()
        self.after(1000, self.task_update_charts)

    ##################
    #### Control receive
    ##################

    def log(self, value=None):
        """Log to the output text field."""
        time = dt.datetime.now().isoformat(sep=" ", timespec="seconds")
        self.output.configure(state='normal')
        self.output.insert(tk.END, f"{time} : {value}\n")
        self.output.configure(state='disabled')

    def set_trigger(self, queue=None, queue_event=None, quit_event=None):
        """Start-up actions."""
        self.queue = queue
        self.queue_event = queue_event
        self.quit_event = quit_event
        self.task_query_instruments()
        self.task_update_charts()

    def set_instruments(self, instruments):
        """Save instrument"""
        self.instruments = instruments

        # Reset var and delete all old options
        self.instrument.set(instruments[0])
        self.edt_instr['menu'].delete(0, tk.END)

        # Insert list of new options (tk._setit hooks them up to var)
        for choice in self.instruments:
            self.edt_instr['menu'].add_command(
                label=choice, command=tk._setit(self.instrument, choice)
            )

    def set_trace(self, x: Iterable = None, y: Iterable = None):
        """Save incoming full trace."""
        self.plot_trace.set_data(x, y)

    def add_mark(self, value=None):
        """Save incoming resonance frequency point."""
        x, y = value
        self.plot_mark.append_data(x, y)

    def update_chart(self):
        """Update all charts."""
        self.plot_trace.update_plot()
        self.plot_mark.update_plot()


##################
#### Run detached
##################

if __name__ == '__main__':
    root = tk.Tk()
    app = MainWindow(root, Config("../settings.cfg"), wd=".")
    root.mainloop()
