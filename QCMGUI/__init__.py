import pathlib
import tkinter as tk

from config import Config
from controller import MainController
from gui import MainWindow
from instrument import DSA815

wd = pathlib.Path(__file__).parent.parent
cfile = wd / "settings.cfg"
sfolder = wd / "QCMGUI"


def main():
    """Main entrypoint."""
    conf = Config(cfile)
    dfolder = wd / conf.get("data_folder")

    root = tk.Tk()
    app = MainWindow(root, conf, sfolder)
    model = DSA815(dfolder)
    ctrl = MainController(model=model, app=app)
    ctrl.start()  # start the controller thread
    root.mainloop()  # start the GUI thread


if __name__ == '__main__':
    main()
