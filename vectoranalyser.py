import time
import sys
import datetime as dt
import threading
import atexit

import RsInstrument as rsi


class VectorAnalyser:
    def __init__(self):
        self.instr = None
        self.q = None
        self.triggerEvent = None

        self.fp_marker = open("./markers.csv", 'a')

    def query(self):
        try:
            self.log(rsi.RsInstrument.list_resources("?*"))
        except ValueError:
            self.log(
                "Could not find a VISA implementation. Switching to simulated connection."
            )

    def connect(self, ip='127.0.0.1'):
        try:
            self.instr = rsi.RsInstrument(
                f'TCPIP::{ip}::HISLIP',
                True,
                True,
            )
        except ValueError:
            self.instr = rsi.RsInstrument(
                f'TCPIP::{ip}::HISLIP', True, True, "Simulate=True"
            )
        except rsi.ResourceError as e:
            self.log(e.args[0])
            self.log('Your instrument is probably OFF...')
            return

        self.instr.visa_timeout = 3000

        self.log(self.instr.query_str('*IDN?'))

    def configure(self):
        # turn off measurement
        self.instr.write_str("INIT:CONT:ALL OFF")

        # freq range
        self.instr.write_str("SENS1:FREQ:START 9.92MHZ")
        self.instr.write_str("SENS1:FREQ:STOP 10.01MHZ")

        # sweep settings
        self.instr.write_str("SENS1:SWE:TIME:AUTO On")
        self.instr.write_str("SENS1:SWE:POIN 5001")

        # traces
        self.instr.write_str("CALC1:PAR:SDEF 'Linear', 'S21'")
        self.instr.write_str("CALC1:FORMAT MLIN")

        self.instr.write_str("DISP:WIND2:STAT ON")
        self.instr.write_str("DISP:WIND2:TRAC1:FEED 'Linear'")

        # do one measurement for reference vals
        self.instr.write_str("INIT1:IMM; *WAI")
        
        # now scale
        self.instr.write_str("DISP:WIND1:TRAC1:Y:SCAL:AUTO ONCE")
        self.instr.write_str("DISP:WIND2:TRAC1:Y:SCAL:AUTO ONCE")

        # markers
        self.instr.write_str("CALC1:MARK1:STAT ON")
        self.instr.write_str("CALC1:MARK1:FUNC:EXEC MAX")
        self.instr.write_str("CALC1:MARK1:COUPLED ON")
        self.instr.write_str("CALC1:MARK1:SEAR:TRAC ON")
        self.instr.write_str("CALC1:MARK1:SEAR:FORM MLIN")

        # turn on continuous measurement
        self.instr.write_str("INIT:CONT:ALL ON")

        # update screen
        self.instr.write_str("SYST:DISP:UPD ONCE")

        # threaded events
        self.threadMeasureBool = False
        self.threadRecordBool = False
        self.threadMeasure = threading.Thread(target=self.measure, daemon=True)

        self.exitEvent = threading.Event()
        atexit.register(self.exitEvent.set)
        self.threadMeasure.start()

        # time deltas
        self.reftime = dt.datetime.now()

        # done
        self.log("Configuration complete.")

    def start_measure(self):
        self.threadMeasureBool = True

    def stop_measure(self):
        self.threadMeasureBool = False

    def start_record(self):
        self.threadRecordBool = True

    def stop_record(self):
        self.threadRecordBool = False

    def measure(self):
        while True:
            # Exit if needed
            if self.exitEvent.is_set():
                print("exiting")
                sys.exit()

            if self.threadMeasureBool:

                # Update screen
                self.instr.write_str("SYSTem:DISPlay:UPDate ONCE")

                # Read marker
                mark = self.instr.query_float("CALC1:MARK:X?")
                self.q.put(('disp', {'task': 'get_mark', 'value': mark}))

                # Read trace
                trace = self.instr.query_bin_or_ascii_float_list(
                    "CALC1:DATA? FDAT"
                )
                stim = self.instr.query_bin_or_ascii_float_list(
                    "CALC1:DATA:STIM?"
                )
                self.q.put(
                    ('disp', {
                        'task': 'get_trace',
                        'x': stim,
                        'y': trace,
                    })
                )

                # save if recording
                if self.threadRecordBool:
                    # Save marker
                    now = dt.datetime.now()
                    self.fp_marker.write(f"{now},{mark}\n")

                    # Save trace every X seconds
                    if (now - self.reftime).seconds > 60:
                        self.reftime = now
                        filename = str(now).replace(':', '')
                        with open(f"./traces/{filename}.csv", 'w') as f:
                            f.writelines(
                                map(
                                    lambda x: f"{x[0]},{x[1]}\n",
                                    zip(stim, trace)
                                )
                            )

                self.triggerEvent.set()

            # Wait for required time
            time.sleep(0.5)

    def set_trigger(self, trigger=None, q=None):
        self.triggerEvent = trigger
        self.q = q

    def log(self, msg):
        self.q.put(('disp', {'task': 'log', 'value': msg}))
        self.triggerEvent.set()

    def run_cmd(self, cmd):
        self.instr.write_str(cmd)

    def close(self):
        self.exitEvent.set()
        self.instr.close()
        self.fp_marker.close()


if __name__ == '__main__':

    print("Direct control.")
    va = VectorAnalyser()
    va.connect()
    print(va.measure())
