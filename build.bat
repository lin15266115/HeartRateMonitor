setlocal

set "PROJECT_NAME=HeartRateMonitor_3"

pyinstaller ^
 --name "%PROJECT_NAME%" ^
 --add-data "LICENSE;." ^
 --windowed ^
 --clean ^
 __main__.py

endlocal