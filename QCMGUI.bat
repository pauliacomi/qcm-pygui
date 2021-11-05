@ECHO OFF
@ECHO Starting QCM/VA control
call conda activate ./venv
python ./QCMGUI
call conda deactivate