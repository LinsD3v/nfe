@echo off

cd /d "%~dp0"
call "venv-jab\Scripts\activate.bat"
py -m worker.startup_worker

pause