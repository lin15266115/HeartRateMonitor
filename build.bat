setlocal

set "PROJECT_NAME=HeartRateMonitor_5"

pyinstaller ^
 --name "%PROJECT_NAME%" ^
 --windowed ^
 --clean ^
 __main__.py

set TARGET_DIR=".\dist\%PROJECT_NAME%\"

echo 正在复制文件...
copy "heart-rate.png" %TARGET_DIR%

copy "LICENSE" %TARGET_DIR%

copy "version.json" %TARGET_DIR%

if %errorlevel% equ 0 (
    echo "文件复制成功！"
) else (
    echo "文件复制失败！"
)

endlocal