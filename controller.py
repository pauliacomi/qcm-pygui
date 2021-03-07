import atexit
import queue
import sys
import threading
import traceback


class MainController(threading.Thread):
    """Event loop for the GUI.

    This class interfaces between the GUI and the underlying
    experiments. It runs in a separate thread and uses a queue to
    communicate tasks from the GUI to the instrument interface. This is
    important to keep the GUI responsive.
    """
    def __init__(self, instr=None, app=None, log=None):
        super().__init__()
        self.instr = instr
        self.app = app
        self.daemon = True

        self.log = log

        self.q = queue.LifoQueue(maxsize=5)
        self.triggerEvent = threading.Event()

        app.set_trigger(trigger=self.triggerEvent, q=self.q)
        instr.set_trigger(trigger=self.triggerEvent, q=self.q)
        instr.query()

        self.exitEvent = threading.Event()
        atexit.register(self.triggerEvent.set)
        atexit.register(self.exitEvent.set)
        atexit.register(self.close)

    def run(self):
        while True:
            self.triggerEvent.wait()
            self.triggerEvent.clear()

            if self.exitEvent.is_set():
                self.close()
                sys.exit()

            while not self.q.empty():
                job, kwargs = self.q.get()

                try:
                    if job == 'ctrl':
                        func = getattr(self.instr, kwargs.pop('task'))
                    elif job == 'disp':
                        func = getattr(self.app, kwargs.pop('task'))
                except KeyError:
                    print(f'Unknown job: {job}')
                    print(f'Kwargs:\n{kwargs}')
                    continue

                try:
                    func(**kwargs)
                except Exception as e:
                    traceback.print_exc()
                    self.instr.log(
                        f"Error caught -> {repr(e)} while running '{job}' with parameters '{kwargs}'"
                    )
                    self.instr.log(e)

    def close(self):
        for item in (self.instr, self.app):
            try:
                item.close()
            except AttributeError:
                pass
