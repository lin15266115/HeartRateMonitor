import sys
import json
import asyncio
import argparse

VER2 = (1, 3, 4, 1)
vname = "v" + ".".join(map(str, VER2[0:3])) + "-beta"

import system_utils
system_utils.IS_FROZEN = IS_FROZEN = getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS") or ("__compiled__" in globals())

from system_utils import (
     getlogger, upmod_logger, add_errorfunc, handle_exception
    ,init_config, pip_install_models
    ,handle_update_mode,handle_end_update
)

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('-updatemode', action='store_true', help='更新模式标志')
parser.add_argument('-endup', action='store_true', help='更新结束标志')
parser.add_argument('-startup', action='store_true', help='用于测试应用能否通过start.bat脚本正常启动')
args = parser.parse_args()

if args.startup:
    print("Success!")
    sys.exit(0)

# 如果是更新模式，使用简单日志输出
if args.updatemode:
    logger = upmod_logger()
else:
    logger = getlogger()

# 设置全局异常钩子
sys.excepthook = handle_exception

if IS_FROZEN:
    __version__ = vname

    # 更新模式
    if args.updatemode:
        logger.info("进入更新模式...")
        handle_update_mode()

    # 更新结束模式
    if args.endup:
        logger.info("进入更新结束模式...")
        handle_end_update()
else:
    __version__ = 't' + '.'.join(map(str, VER2))
    with open("version.json", "w", encoding="utf-8") as f:
        sdata = {
             "name": __version__
            ,"version": 2
            ,"VER2": VER2
            ,"gxjs": "优化启动项管理以及其它优化"
            ,"frozen":{
                 "name":  vname
                ,"version": 2
                ,"VER2": VER2
                ,"updateTime": "2025-7-17-15:00:00"
                ,"gxjs": "本次更新新增开机自启和启动时自动连接设备功能，以及一系列优化"
                ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{vname}"
                ,"download": f"https://gitcode.com/lin15266115/HeartBeat/releases/download/{vname}/HRMLink.exe"
            }
        }
        json.dump(sdata, f, ensure_ascii=False, indent=2)

system_utils.VER2 = VER2

logger.info(f"运行程序 -{__version__}" + " ".join(argv for argv in sys.argv if argv))
logger.info(f"Python版本: {sys.version}; 运行位置：{sys.executable}")

init_config()

def import_pyqt5():
    global QApplication, QtWin
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWinExtras import QtWin

def import_qasync():
    global QEventLoop
    from qasync import QEventLoop

def import_models():
    import bleak

pip_install_models(import_pyqt5, "pyqt5")
pip_install_models(import_qasync, "qasync")
pip_install_models(import_models, "bleak")

from importlib.metadata import version
logger.info(f"pyqt5({version('PyQt5')}); qasync({version('qasync')}); bleak({version('bleak')})")

from UI import MainWindow
import ctypes

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app_id = 'Zerolinofe.HRMLink.Main.1'
    QtWin.setCurrentProcessExplicitAppUserModelID(app_id)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    # 设置异步事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(__version__)
    window.show()
    hwnd = window.winId()

    screen = app.primaryScreen()
    screen.logicalDotsPerInchChanged.connect(window.auto_FixedSize)

    def errwin(exc_type, exc_value):
        window.verylarge_error(f"{exc_type.__name__}: {exc_value}")

    add_errorfunc(errwin)

    with loop:
        screens = app.screens()
        loop.run_forever()