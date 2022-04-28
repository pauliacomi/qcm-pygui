@ECHO OFF
@ECHO Installing QCMGUI
@ECHO Creating conda environment
conda env create -f environment.yml -p ./.venv && (
  ECHO Install success
) || (
  ECHO failed/error: Conda not found. Install a version of Anaconda/Miniconda
)