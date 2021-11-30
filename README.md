# QCMGUI

Simple python-based GUI for data acquisition from a quartz crystal microbalance (QCM).

Currently the connected instrument is a RIGOL DSA815TG, however the modular
format means that other types of vector analysers can also be adapted.

## Install

Conda must be installed on the local computer. Use the `environment.yml` file to
create a local Conda environment in the `./.venv` folder:

    conda env create -f environment.yml -p ./venv

You should be good to go by double clicking `QCMGUI.bat`.

If for any reason you want to install everything manually:

    conda create -p ./.venv python=3.9
    conda activate ./.venv
    conda install numpy nomkl matplotlib-base pyvisa


It has been tested using python3.9, but other versions should work fine.

## Operation

Once started by clicking `QCMGUI.bat` or by manually activating the Conda
environment and running `python QCMGUI`, the GUI should start.

1. Connected VISA instruments are shown in the top drop-down. Select the Network
   Analyser and click **[Connect]**. Check output to confirm connection.
2. Select the frequency range of interest in the setup row. Then click on
   **[Prime]**. Check output and Analyser display to confirm correct settings.
3. Start reading data by clicking **[Read Start]**. The graphs should now show a
   full frequency scan (top) and the measured maximum frequency (bottom).
4. Start recording data by clicking **[Record Start]**. Full frequency sweeps
   (top graph) are saved in `./current_data/traces/` while individual resonance
   frequencies (bottom graph) are saved in `./current_data/markers.csv`
5. To finalize, click **[Record Stop]**, **[Read Stop]** and then exit program
   normally.

