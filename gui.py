import sys

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkFileDialog
import tkinter.messagebox as tkMessageBox
import tkinter.scrolledtext as tkScrolledText

from vectoranalyser import VectorAnalyser
from controller import MainController
from chart import Chart
from config import Config

NWE = tk.N + tk.E + tk.W
PADX = 5
PADY = 5
INDENT = 20


class MainApp(ttk.Frame):
    def __init__(self, parent, conf, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.conf = conf
        self.parent = parent
        self.reading = False
        self.recording = False
        self.configure_gui()
        self.create_widgets()
        self.on_timer()

    def configure_gui(self):

        top = self.winfo_toplevel()
        top.geometry('800x720+100+100')

        self.parent.title("QCM controller")
        self.parent.protocol('WM_DELETE_WINDOW', self.on_close)
        self.pack(side='top', fill='both', expand=True)

        self.parent.bind('<Return>', self.send_command)
        self.parent.bind('<Escape>', self.on_close)

    def create_widgets(self):

        # the layout is 4 rows:
        #    row 0 = menubar
        #    row 1 = graphs etc - expandable
        #    row 2 = output
        #    row 3 = input
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=2)
        self.rowconfigure(2, weight=2)
        self.rowconfigure(3, weight=0)

        # row 1 is constructed as 2 columns, with all the expansion
        # assigned to the graphs /output
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=1)

        # construct the widgets
        self.create_menu(self)
        self.create_controls(self)
        self.create_graph(self)
        self.create_output(self)
        self.create_input(self)

    def create_menu(self, parent):
        """Make a Frame to hold the menu in a horizontal row at the top."""
        self.menu_bar = tk.Frame(parent, bd=2)
        self.menu_bar.grid(row=0, column=0, sticky=NWE, columnspan=2)

        mbutton = ttk.Menubutton(self.menu_bar, text='File', underline=0)
        mbutton.pack(side=tk.LEFT)
        menu = tk.Menu(mbutton, tearoff=0)
        menu.add_command(label='Quit', command=self.on_close)
        mbutton['menu'] = menu
        self.fmenu = menu

        mbutton = ttk.Menubutton(self.menu_bar, text='Help', underline=0)
        mbutton.pack(side=tk.LEFT)
        menu = tk.Menu(mbutton, tearoff=0)
        menu.add_command(label='About', command=self.on_about)
        mbutton['menu'] = menu

    def create_controls(self, parent):
        """Make a Frame to hold the controls in a vertical column at right."""
        ctrl_col = ttk.Frame(parent)
        ctrl_col.grid(row=1, column=1, sticky=tk.NW)

        self.ipaddr = tk.Entry(ctrl_col)
        self.ipaddr.grid(row=0, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10)
        self.ipaddr.insert(tk.END, self.conf.sett["IP"])

        self.btn_connect = ttk.Button(ctrl_col)
        self.btn_connect["text"] = "Connect"
        self.btn_connect["command"] = self.task_connect
        self.btn_connect.grid(
            row=1, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10
        )

        self.btn_running = ttk.Button(ctrl_col)
        self.btn_running["text"] = "Prime"
        self.btn_running["command"] = self.task_configure
        self.btn_running.grid(
            row=2, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10
        )

        self.btn_acquire = ttk.Button(ctrl_col)
        self.btn_acquire["text"] = "Acquire"
        self.btn_acquire["command"] = self.task_toggle_read
        self.btn_acquire.grid(
            row=3, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10
        )

        self.btn_record = ttk.Button(ctrl_col)
        self.btn_record["text"] = "Record Start"
        self.btn_record["command"] = self.task_toggle_record
        self.btn_record.grid(
            row=4, sticky=tk.NW, padx=PADX, pady=PADY, ipadx=10
        )

    def create_graph(self, parent):
        """Make a Frame to hold the graphs (Canvas objects, see chart.py)."""
        self.chart_frame = tk.Frame(parent, padx=PADX, pady=PADY)
        self.chart_frame.grid(row=1, column=0, sticky=tk.NSEW)

        # Create the two figures
        self.plot_trace = Chart(self.chart_frame)
        self.plot_trace.widget.grid(row=0, column=0, sticky=tk.NSEW)
        self.plot_mark = Chart(self.chart_frame)
        self.plot_mark.widget.grid(row=1, column=0, sticky=tk.NSEW)

        # Allow charts to expand horizontally
        self.chart_frame.columnconfigure(0, weight=1)

        # allow charts to expand vertically
        self.chart_frame.rowconfigure(0, weight=1)
        self.chart_frame.rowconfigure(1, weight=1)

    def create_output(self, parent):
        self.output = tkScrolledText.ScrolledText(parent)
        self.output.grid(row=2, column=0, pady=PADY, padx=PADX, sticky=NWE)

        # Making the text read only
        self.output.configure(state='disabled')

    def create_input(self, parent):
        self.input = tk.Entry(parent)
        self.input.grid(
            row=3, column=0, columnspan=1, pady=PADY, padx=PADX, sticky=NWE
        )
        self.btn_input = ttk.Button(parent)
        self.btn_input["text"] = "Send command"
        self.btn_input.grid(
            row=3, column=1, sticky=tk.SW, padx=PADX, pady=PADY, ipadx=10
        )

    #########
    #########
    #########
    #########
    #########

    def send_command(self, *args, **kwargs):
        cmd = self.input.get()
        self.input.delete(0, tk.END)

        self.output.configure(state='normal')
        self.output.insert(tk.END, f"Command sent: {cmd}\n")
        self.output.configure(state='disabled')

        self.q.put(('ctrl', {'task': 'run_cmd', 'cmd': cmd}))
        self.triggerEvent.set()

    def set_trigger(self, trigger=None, q=None):
        self.triggerEvent = trigger
        self.q = q

    def task_configure(self, event=None):
        self.q.put(('ctrl', {'task': 'configure'}))
        self.triggerEvent.set()

    def task_connect(self, event=None):
        ipaddr = self.ipaddr.get()
        self.output.configure(state='normal')
        self.output.insert(tk.END, f"Connecting to {ipaddr}\n")
        self.output.configure(state='disabled')
        self.q.put(('ctrl', {'task': 'connect', 'ip': ipaddr}))
        self.triggerEvent.set()
        if ipaddr != self.conf.sett['IP']:
            self.conf.sett['IP'] = ipaddr

    def task_toggle_read(self, event=None):
        if self.reading:
            self.q.put(('ctrl', {'task': 'stop_measure'}))
            self.btn_acquire["text"] = "Read Start"
            self.reading = False
        else:
            self.q.put(('ctrl', {'task': 'start_measure'}))
            self.btn_acquire["text"] = "Read Stop"
            self.reading = True
        self.triggerEvent.set()

    def task_toggle_record(self, event=None):
        if self.reading:
            if self.recording:
                self.q.put(('ctrl', {'task': 'stop_record'}))
                self.btn_record["text"] = "Record Start"
                self.recording = False
            else:
                self.q.put(('ctrl', {'task': 'start_record'}))
                self.btn_record["text"] = "Record Stop"
                self.recording = True
            self.triggerEvent.set()

        else:
            self.log("Nothing to record, start reading first.")

    def log(self, value=None):
        self.output.configure(state='normal')
        self.output.insert(tk.END, f"{value}\n")
        self.output.configure(state='disabled')

    def get_trace(self, x=None, y=None):
        self.plot_trace.plot_full(x, y)

    def get_mark(self, value=None):
        self.plot_mark.plot_append(value)

    def on_timer(self):
        self.plot_trace.canvas.draw()
        self.plot_mark.canvas.draw()
        self.after(500, self.on_timer)

    def on_about(self):
        tkMessageBox.showinfo(
            'About', "QCM controller to R&S VA over pyVISA \nPaul Iacomi 2020"
        )

    def on_close(self, *args, **kwargs):
        try:
            self.conf.save()
        except AttributeError:
            pass
        sys.exit()


if __name__ == '__main__':

    conf = Config()

    root = tk.Tk()
    app = MainApp(root, conf)
    instr = VectorAnalyser()

    ctrl = MainController(instr=instr, app=app)
    ctrl.start()

    root.mainloop()
