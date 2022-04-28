"""
Class that abstracts interaction with the VISA instrument.
"""

import datetime as dt
import pathlib
import threading
import time

import numpy as np
import pyvisa
from pyvisa.util import from_ascii_block


class VISAInstrument():
    """
    Abstract instrument class that communicates with the VISA instrument.
    Needs subclassing for each instrument class.
    """
    def __init__(self, dfolder: pathlib.Path):
        # references to command queue
        self.queue = None
        self.queue_event = None
        self.quit_event = None

        # file paths and pointers
        if not dfolder.exists():
            dfolder.mkdir()
        self.fp_marker = open(dfolder / "markers.csv", 'a', encoding="utf8")
        self.f_traces = dfolder / "traces"
        if not self.f_traces.exists():
            self.f_traces.mkdir()

        # VISA init
        self.rm = None
        self.instrument = None
        try:
            self.rm = pyvisa.ResourceManager()
        except OSError:
            self.log(
                "Could not find a VISA library. Please install a VI library (NI-VISA, R&S VISA, etc.)."
            )

        # setup measurement thread
        self.reftime = None
        self.thread_measure = threading.Thread(target=self.measure, daemon=True)
        self.thread_measure_flag = False
        self.thread_record_flag = False
        self.thread_measure.start()

    def query_instruments(self):
        """Get all available instruments."""
        if not self.rm:
            return
        try:
            instruments = self.rm.list_resources("?*")
            instruments = instruments + ("Simulation", )
            self.queue.put(('disp', {
                'task': 'set_instruments',
                'instruments': instruments,
            }))
        except ValueError:
            self.log("Could not find a VISA resource. Switching to simulated connection.")
            self.queue.put(('disp', {
                'task': 'set_instruments',
                'instruments': ("Simulation", ),
            }))

    def connect(self, instrument='TCPIP::127.0.0.1::HISLIP'):
        """Connect to a specified instrument string."""
        if not self.rm:
            return

        if instrument == 'Simulation':
            self.instrument = self.rm.open_resource(
                'TCPIP::127.0.0.1::HISLIP',
                id_query=True,
                reset=True,
                option_string="Simulate=True",
            )
        else:
            try:
                self.instrument = self.rm.open_resource(
                    instrument,
                    read_termination='\n',
                )
            except Exception as e:
                self.log(f'Unexpected connection error {repr(e)}.')
                self.log(e.args[0])

        self.instrument.timeout = 3000
        self.log(f"Connected to {self.instrument.query('*IDN?')}")

    def measure(self):
        """Perform measurement. Should be implemented in subclasses."""

    ##################
    #### Control receive
    ##################

    def log(self, msg):
        """Send log message to queue."""
        self.queue.put(('disp', {'task': 'log', 'value': msg}))
        self.queue_event.set()

    def set_trigger(self, queue=None, queue_event=None, quit_event=None):
        """Start-up actions."""
        self.queue = queue
        self.queue_event = queue_event
        self.quit_event = quit_event

    def run_cmd(self, cmd):
        """Run an incoming random VISA command."""
        if cmd.endswith("?"):
            self.log("Querying Instrument...")
            resp = self.instrument.query(cmd)
            self.log("Response received.")
            self.log(resp)
            return
        self.instrument.write(cmd)

    def start_measure(self):
        """Start the measurement by setting the flag."""
        self.thread_measure_flag = True

    def stop_measure(self):
        """Stop the measurement by setting the flag."""
        self.thread_measure_flag = False

    def start_record(self):
        """Start recording by setting the flag."""
        self.reftime = dt.datetime.now()
        self.thread_record_flag = True

    def stop_record(self):
        """Stop recording by setting the flag."""
        self.thread_record_flag = False

    def close(self):
        """Ask the class to close."""
        print("Vector analyser asked to close.")
        self.quit_event.set()
        self.thread_measure.join()
        if self.instrument:
            self.instrument.close()
        self.fp_marker.close()
        print("Vector analyser closed.")


class DSA815(VISAInstrument):
    """Specific implementation for the Rigol DSA815."""
    def __init__(self, dfolder: pathlib.Path):
        super().__init__(dfolder=dfolder)
        self.frange = None

    def configure(self, start=9.92e6, stop=10.02e6):
        """Configure the connected instrument."""
        if not self.instrument:
            self.log('Not connected to any instrument.')

        # reset everything
        self.instrument.timeout = 30000
        self.instrument.write("*RST")

        # turn off measurement
        self.instrument.write("INIT:CONT OFF")

        # tracking generator
        self.instrument.write("OUTP:STAT ON")

        # freq range
        self.instrument.write(f"SENS:FREQ:START {start}")
        self.instrument.write(f"SENS:FREQ:STOP {stop}")

        # sweep settings
        self.instrument.write("SENS:BAND:RES 1KHZ")  # RBW 1 kHz
        self.instrument.write("SENS:BAND:VID 1MHZ")  # VBW 1 MHz
        self.instrument.write("SENS:DET:FUNC RMS")  # DET type RMS avg
        self.instrument.write("SENS:SWE:TIME:AUTO:RULES ACCURACY")
        self.instrument.write("SENS:SWE:TIME:AUTO ON")

        # scaling
        self.instrument.write("INIT:IMM; *WAI")  # measurement for reference
        self.instrument.write("DISP:WIN:TRAC:Y:SCALe:SPACing LIN")
        self.instrument.write("SENS:POWer:ASCale")

        # markers
        self.instrument.write("CALC:MARK1:STAT ON")
        self.instrument.write("CALC:MARK1:CPEak:STATe ON")

        # freq counter
        self.instrument.write('CALC:MARK:FCOunt:STATe ON')
        self.instrument.write('CALC:MARK:FCOunt:RESolution 1HZ')

        # query step length
        steps = int(self.instrument.query(":SENSe:SWEep:POINts?"))

        self.frange = np.linspace(start, stop, steps)

        # turn on continuous measurement
        self.instrument.write("INIT:CONT ON")

        # done
        self.log("Configuration complete.")

    def measure(self):
        """
        Perform measurements on the connected instrument.
        This function is designed to be called from a thread.
        """
        while True:
            # Exit if needed
            if self.quit_event and self.quit_event.is_set():
                print("Exiting VA measurement thread.")
                break

            if self.thread_measure_flag:

                # Read marker
                mark = None
                try:
                    mark = self.instrument.query("CALC:MARK1:X?")
        # mark = self.instrument.query('CALC:MARK:FCOunt:X?')
                except pyvisa.errors.VisaIOError as e:
                    self.log(f"Could not read marker. Error: {e}")
                if mark:
                    mark = float(mark)
                    timenow = dt.datetime.now()
                    self.queue.put((
                        'disp',
                        {
                            'task': 'add_mark',
                            'value': (timenow, mark)
                        },
                    ))

                # Read trace
                # With Rigol the instrument returns a header
                # which denotes the data length.
                # We remove this before passing it to pyVISA routines
                data = None
                try:
                    self.instrument.write('TRAC:DATA? TRACE1')
                    data = self.instrument.read()
                except pyvisa.errors.VisaIOError as e:
                    self.log(f"Could not read marker. Error: {e}")
                if data:
                    data = data[12:]
                    trace = from_ascii_block(data)
                    self.queue.put((
                        'disp',
                        {
                            'task': 'set_trace',
                            'x': self.frange,
                            'y': trace,
                        },
                    ))

                # inform read
                self.queue_event.set()

                # save if recording
                if self.thread_record_flag:

                    # Save marker
                    if mark:
                        self.fp_marker.write(f"{timenow},{mark}\n")

                    # Save trace every X seconds
                    if trace:
                        if (timenow - self.reftime).seconds > 60:
                            self.reftime = timenow
                            filename = str(timenow).replace(':', '') + ".csv"
                            with open(self.f_traces / filename, 'w', encoding="utf8") as f:
                                f.writelines(
                                    map(
                                        lambda x: f"{x[0]},{x[1]}\n",
                                        zip(self.frange, trace),
                                    )
                                )

            # Wait for required time
            time.sleep(0.5)


if __name__ == '__main__':

    print("Direct control.")
    va = DSA815(dfolder="")
    va.connect()
    print(va.measure())
