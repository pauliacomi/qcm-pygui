import atexit
import queue
import sys
import threading
import traceback


class MainController(threading.Thread):
    """Event loop for the GUI/instrument connection.

    This class interfaces between the GUI and the underlying
    instrument. It runs in a separate thread and uses a queue to
    communicate tasks from the GUI to the instrument interface. This is
    important to keep the GUI responsive.
    """
    def __init__(self, model=None, app=None):
        super().__init__()

        # allow thread to run in background
        self.daemon = True

        # create a command queue
        self.queue = queue.Queue(maxsize=10)

        # event will be triggered to process queue
        self.queueEvent = threading.Event()

        # event will be triggered at exit to graceful close
        self.quitEvent = threading.Event()
        atexit.register(self.quitEvent.set)
        atexit.register(self.queueEvent.set)

        # connect model/app
        self.model = model
        self.model.set_trigger(
            queue=self.queue,
            queue_event=self.queueEvent,
            quit_event=self.quitEvent,
        )
        self.app = app
        self.app.set_trigger(
            queue=self.queue,
            queue_event=self.queueEvent,
            quit_event=self.quitEvent,
        )

    def run(self):
        while True:
            self.queueEvent.wait()  # blocked in waiting
            print("woke up")

            # Below what happens if event triggered
            if self.quitEvent.is_set():
                self.close()

            self.queueEvent.clear()

            while not self.queue.empty():
                job, kwargs = self.queue.get()
                print(job, kwargs.get('task'))

                try:
                    if job == 'ctrl':
                        func = getattr(self.model, kwargs.pop('task'))
                    elif job == 'disp':
                        func = getattr(self.app, kwargs.pop('task'))
                    else:
                        self.log(f'Unknown job type: {job}')
                        self.log(f'Kwargs:\n{kwargs}')
                except KeyError:
                    self.log(f'Could not find job {job}.')
                    self.log(f'Kwargs:\n{kwargs}')
                    continue

                try:
                    func(**kwargs)
                except Exception as e:
                    traceback.print_exc()
                    self.log(
                        f"Error caught -> {repr(e)} while running '{job}' with parameters '{kwargs}'"
                    )
                    self.log(e)

    def log(self, msg):
        self.queue.put(('disp', {'task': 'log', 'value': msg}))
        self.queueEvent.set()

    def close(self):
        for item in (self.model, self.app):
            try:
                item.close()
            except AttributeError as ex:
                print(f"Could not close with error: {ex}")
        print("Closed all components, now exiting...")
        sys.exit()
