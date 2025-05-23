setlocal

set "PROJECT_NAME=HeartRateMonitor_5"

pyinstaller ^
 --name "%PROJECT_NAME%" ^
 --windowed ^
 --clean ^
 __main__.py

set SOURCE_FILE="heart-rate.png"
set TARGET_DIR=".\dist\%PROJECT_NAME%\"

echo 正在复制文件...
copy %SOURCE_FILE% %TARGET_DIR%

set SOURCE_FILE="LICENSE"
copy %SOURCE_FILE% %TARGET_DIR%

set SOURCE_FILE="version.json"
copy %SOURCE_FILE% %TARGET_DIR%

if %errorlevel% equ 0 (
    echo 文件复制成功！
) else (
    echo 文件复制失败！
)

endlocal