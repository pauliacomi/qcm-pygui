import pathlib
import time
import datetime as dt
import threading

import pyvisa
from pyvisa.util import from_ascii_block


class VectorAnalyser():
    def __init__(self, dfolder: pathlib.Path):

        # references to command queue
        self.queue = None
        self.queueEvent = None
        self.quitEvent = None

        # file paths and pointers
        self.fp_marker = open(dfolder / "markers.csv", 'a')
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
                "Could not find a VISA library. "
                "Please install a VI library (NI-VISA, R&S VISA, etc.)."
            )

        # setup measurement thread
        self.threadMeasure = threading.Thread(target=self.measure, daemon=True)
        self.threadMeasureBool = False
        self.threadRecordBool = False
        self.threadMeasure.start()

    def query_instruments(self):
        """Get the available instruments."""
        if not self.rm:
            return
        try:
            instruments = self.rm.list_resources("?*")
            instruments = instruments + ("Simulation", )
            self.queue.put((
                'disp', {
                    'task': 'set_instruments',
                    'instruments': instruments
                }
            ))
        except ValueError:
            self.log(
                "Could not find a VISA resource. "
                "Switching to simulated connection."
            )
            self.queue.put((
                'disp', {
                    'task': 'set_instruments',
                    'instruments': ("Simulation", )
                }
            ))

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
                    instrument, read_termination='\n'
                )
            except Exception as e:
                self.log(f'Unexpected connection error {repr(e)}.')
                self.log(e.args[0])

        self.instrument.visa_timeout = 3000
        self.log(f"Connected to {self.instrument.query('*IDN?')}")

    def configure(self):
        """Configure the connected instrument."""
        if not self.instrument:
            self.log('Not connected to any instrument.')

        # reset everything
        self.instrument.write("*RST")

        # turn off measurement
        self.instrument.write("INIT:CONT OFF")

        # tracking generator
        self.instrument.write("OUTP:STAT ON")

        # freq range
        self.instrument.write("SENS:FREQ:START 9.92MHZ")
        self.instrument.write("SENS:FREQ:STOP 10.03MHZ")

        # sweep settings
        self.instrument.write("SENS:SWE:TIME:AUTO ON")
        self.instrument.write("SENS:SWE:POIN 3001")

        # markers
        self.instrument.write("CALC:MARK1:STAT ON")
        self.instrument.write("CALC:MARK1:CPEak:STATe ON")

        # turn on continuous measurement
        self.instrument.write("INIT:CONT ON")

        # TODO display enable/disable?
        # TODO marker points

        # done
        self.log("Configuration complete.")

    def measure(self):
        """
        Perform measurements on the connected instrument.
        This function is designed to be called from a thread.
        """
        while True:
            # Exit if needed
            if self.quitEvent and self.quitEvent.is_set():
                print("Exiting VA measurement thread.")
                break

            if self.threadMeasureBool:

                # Update screen
                # self.instrument.write("SYSTem:DISPlay:UPDate ONCE")

                # Read marker
                mark = self.instrument.query("CALC:MARK1:X?")
                mark = float(mark)
                timenow = dt.datetime.now()
                self.queue.put(
                    ('disp', {
                        'task': 'add_mark',
                        'value': (timenow, mark)
                    })
                )

                # Read trace
                # With Rigol the instrument returns a header
                # which denotes the data length.
                # We remove this before passing it to pyVISA routines
                self.instrument.write('TRAC:DATA? TRACE1')
                data = self.instrument.read()
                data = data[12:]
                trace = from_ascii_block(data)
                stat = list(range(len(trace)))
                # stim = self.instrument.query_ascii_values("CALC:DATA:STIM?")
                self.queue.put(
                    ('disp', {
                        'task': 'set_trace',
                        'x': stat,
                        'y': trace,
                    })
                )

                # save if recording
                if self.threadRecordBool:
                    # Save marker
                    self.fp_marker.write(f"{timenow},{mark}\n")

                    # Save trace every X seconds
                    if (timenow - self.reftime).seconds > 60:
                        self.reftime = timenow
                        filename = str(timenow).replace(':', '') + ".csv"
                        with open(self.f_traces / filename, 'w') as f:
                            f.writelines(
                                map(
                                    lambda x: f"{x[0]},{x[1]}\n",
                                    zip(stim, trace)
                                )
                            )

                self.queueEvent.set()

            # Wait for required time
            time.sleep(0.5)

    ##################
    #### Control receive
    ##################

    def log(self, msg):
        self.queue.put(('disp', {'task': 'log', 'value': msg}))
        self.queueEvent.set()

    def set_trigger(self, queue=None, queue_event=None, quit_event=None):
        self.queue = queue
        self.queueEvent = queue_event
        self.quitEvent = quit_event

    def run_cmd(self, cmd):
        if cmd.endswith("?"):
            self.log("Querying Instrument...")
            resp = self.instrument.query(cmd)
            self.log("Response received.")
            self.log(resp)
            return

        self.instrument.write(cmd)

    def start_measure(self):
        self.threadMeasureBool = True

    def stop_measure(self):
        self.threadMeasureBool = False

    def start_record(self):
        self.reftime = dt.datetime.now()
        self.threadRecordBool = True

    def stop_record(self):
        self.threadRecordBool = False

    def close(self):
        print("Vector analyser asked to close.")
        self.quitEvent.set()
        self.threadMeasure.join()
        if self.instrument:
            self.instrument.close()
        self.fp_marker.close()
        print("Vector analyser closed.")


if __name__ == '__main__':

    print("Direct control.")
    va = VectorAnalyser()
    va.connect()
    print(va.measure())
