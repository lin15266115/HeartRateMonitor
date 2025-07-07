cd /d "%~dp0"

chcp 65001

@echo off

"set your python path here(it will use system default if empty)"
"在这里修改Python环境路径(设为空时将使用系统默认环境)"
set PYTHONPATH=""

IF "%1"=="-testMode" (
    echo Test mode activated.
    "%PYTHONPATH%pythonw.exe" __main__.py -testMode
) ELSE (
    echo Normal mode activated.
    start "" "%PYTHONPATH%pythonw.exe" __main__.py
)
exit