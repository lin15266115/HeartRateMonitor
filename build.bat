setlocal

set "PROJECT_NAME=HeartRateMonitor_2"

pyinstaller --onefile^
 --name "%PROJECT_NAME%" ^
 --windowed ^
 --clean ^
 __main__.py

endlocal