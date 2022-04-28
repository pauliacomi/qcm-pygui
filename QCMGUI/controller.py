"""
The controller class which executes read/write functions in a separate thread. 
"""
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
        self.queue_event = threading.Event()

        # event will be triggered at exit to graceful close
        self.quit_event = threading.Event()
        atexit.register(self.quit_event.set)
        atexit.register(self.queue_event.set)

        # connect model/app
        self.model = model
        self.model.set_trigger(
            queue=self.queue,
            queue_event=self.queue_event,
            quit_event=self.quit_event,
        )
        self.app = app
        self.app.set_trigger(
            queue=self.queue,
            queue_event=self.queue_event,
            quit_event=self.quit_event,
        )

    def run(self):
        """Main event loop."""
        while True:
            self.queue_event.wait()  # blocked in waiting

            # Below what happens if event triggered
            if self.quit_event.is_set():
                self.close()

            self.queue_event.clear()

            while not self.queue.empty():
                job, kwargs = self.queue.get()

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
                except Exception as err:
                    traceback.print_exc()
                    self.log(
                        f"Error caught -> {repr(err)} while running '{job}' with parameters '{kwargs}'"
                    )
                    self.log(err)

    def log(self, msg):
        """Self-add a log to the queue."""
        self.queue.put(('disp', {'task': 'log', 'value': msg}))
        self.queue_event.set()

    def close(self):
        """Call exit on all components then exit thread."""
        for item in (self.model, self.app):
            try:
                item.close()
            except AttributeError as ex:
                print(f"Could not close with error: {ex}")
        print("Closed all components, now exiting...")
        sys.exit()
