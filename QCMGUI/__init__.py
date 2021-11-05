import pathlib
import tkinter as tk

from config import Config
from controller import MainController
from gui import MainWindow
from instrument import DSA_815

wd = pathlib.Path(__file__).parent.parent
cfile = wd / "settings.cfg"
dfolder = wd / "data"
sfolder = wd / "QCMGUI"


def main():

    conf = Config(cfile)

    root = tk.Tk()
    app = MainWindow(root, conf, sfolder)
    model = DSA_815(dfolder)
    ctrl = MainController(model=model, app=app)
    ctrl.start()  # start the controller thread
    root.mainloop()  # start the GUI thread


if __name__ == '__main__':
    main()
