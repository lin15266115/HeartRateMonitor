@echo off
chcp 65001
cd /d "%~dp0"

    REM "在这里修改Python环境路径(设为空时可能无法实现开机自启)"
    REM "set your python path here(if you don't set it, it may not work properly)"
    set PYTHONPATH=.conda/

    IF "%1"=="" (
        "%PYTHONPATH%pythonw.exe" __main__.py
    ) ELSE IF "%1"=="-startup" (
        "%PYTHONPATH%python.exe" __main__.py -startup
    ) ELSE (
        "%PYTHONPATH%pythonw.exe" __main__.py "%1"
    )
    exit