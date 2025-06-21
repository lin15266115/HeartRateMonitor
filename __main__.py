import sys
import json
import asyncio
import argparse

frozenvname = "v1.3.3-alpha"
frozenver = 1.003003

import config_manager
config_manager.is_frozen = is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS") or ("__compiled__" in globals())

from config_manager import (
     getlogger, upmod_logger, add_errorfunc, handle_exception
    ,init_config, pip_install_models
    ,handle_update_mode,handle_end_update
)

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('-updatemode', action='store_true', help='更新模式标志')
parser.add_argument('-endup', action='store_true', help='更新结束标志')
args = parser.parse_args()

# 如果是更新模式，使用简单日志输出
if args.updatemode:
    logger = upmod_logger()
else:
    logger = getlogger()

# 设置全局异常钩子
sys.excepthook = handle_exception

if is_frozen:
    __version__ = frozenvname
    ver = frozenver

    # 更新模式
    if args.updatemode:
        logger.info("进入更新模式...")
        handle_update_mode()

    # 更新结束模式
    if args.endup:
        logger.info("进入更新结束模式...")
        handle_end_update()
else:
    __version__ = '1.3.3.0'
    ver = 1.00300300
    with open("version.json", "w", encoding="utf-8") as f:
        sdata = {
             "name": __version__
            ,"version": ver
            ,"gxjs": "本次更新修改和优化了应用图标相关的逻辑。"
            ,"frozen":{
                 "name":  frozenvname
                ,"version": frozenver
                ,"updateTime": "2025-06-21-12:00:00"
                ,"gxjs": "本次更新修改和优化了应用图标相关的逻辑。"
                ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{frozenvname}"
                ,"download": f"https://gitcode.com/lin15266115/HeartBeat/releases/download/{frozenvname}/HRMLink.exe"
            }
        }
        json.dump(sdata, f, ensure_ascii=False, indent=2)

config_manager.ver = ver

logger.info(f"运行程序 -{__version__}[{ver}]" + " ".join(argv for argv in sys.argv if argv))
logger.info(f"Python版本: {sys.version}; 运行位置：{sys.executable}")

init_config()

def import_pyqt5():
    global QApplication, QtWin
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWinExtras import QtWin

def import_qasync():
    global QEventLoop
    from qasync import QEventLoop

pip_install_models(import_pyqt5, "pyqt5")
pip_install_models(import_qasync, "qasync")

from UI import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app_id = 'Zerolinofe.HRMLink.Main.1'
    QtWin.setCurrentProcessExplicitAppUserModelID(app_id)

    

    # 设置异步事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(__version__)
    window.show()

    screen = app.primaryScreen()
    screen.logicalDotsPerInchChanged.connect(window.auto_FixedSize)

    def errwin(exc_type, exc_value):
        window.verylarge_error(f"{exc_type.__name__}: {exc_value}")

    add_errorfunc(errwin)

    with loop:
        screens = app.screens()
        loop.run_forever()