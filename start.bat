@echo off
chcp 65001 >nul

cd /d "%~dp0"

REM set your python path here
set PYTHONPATH=".conda\"

start "" "%PYTHONPATH%pythonw.exe" __main__.py
exit