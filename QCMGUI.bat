@ECHO OFF
@ECHO Starting QCM/VA control
call conda activate ./venv
python ./gui.py
call conda deactivate