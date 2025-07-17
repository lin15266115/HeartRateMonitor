cd /d "%~dp0"
chcp 65001
@echo off

:: "set your python path here(if you don't set it, it may not work properly)"
:: "在这里修改Python环境路径(设为空时可能无法实现开机自启)"
set PYTHONPATH=".conda/"

IF "%1"=="-testMode" (
    "%PYTHONPATH%pythonw.exe" __main__.py -testMode
) ELSE (
    start "" "%PYTHONPATH%pythonw.exe" __main__.py
)
exit