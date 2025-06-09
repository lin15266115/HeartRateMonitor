import sys
import json
import asyncio
import argparse
import threading

is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS") or ("__compiled__" in globals())

frozenvname = "v1.3.0-alpha"
frozenver = 1.003000

import config_manager
from config_manager import (
     getlogger, upmod_logger, add_errorfunc, handle_exception
    ,init_config, pip_install_models
    ,handle_update_mode,handle_end_update
    ,checkupdata
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

    # 如果是更新模式，直接处理更新并退出
    if args.updatemode:
        logger.info("进入更新模式...")
        handle_update_mode()

    # 如果是更新结束模式，清理更新文件后继续
    if args.endup:
        logger.info("进入更新结束模式...")
        handle_end_update()
else:
    __version__ = '1.3.1-build'
    ver = 1.00300100
    with open("version.json", "w", encoding="utf-8") as f:
        sdata = {
             "name": __version__
            ,"version": ver
            ,"gxjs": "改进浮窗和一系列优化"
            ,"frozen":{
                 "name":  frozenvname
                ,"version": frozenver
                ,"gxjs": "本次更新修改了更新检查相关功能, 优化了日志记录, 新增浮窗亮度滑条设置"
                ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{frozenvname}"
                ,"download": f"https://gitcode.com/lin15266115/HeartBeat/releases/download/{frozenvname}/HRMLink.exe"
            }
        }
        json.dump(sdata, f, ensure_ascii=False, indent=2)

config_manager.ver = ver
logger.info(f'运行程序 -{__version__}[{ver}]'.join(' '+argv for argv in sys.argv[1:] if argv))
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

# 检查更新

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app_id = 'Zerolinofe.HRMLink.Main.1'
    QtWin.setCurrentProcessExplicitAppUserModelID(app_id)

    # 设置异步事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(__version__)
    window.show()

    def errwin(exc_type, exc_value):
        window.verylarge_error(f"{exc_type.__name__}: {exc_value}")

    add_errorfunc(errwin)

    with loop:
        screens = app.screens()
        def upc():
            if window.settings_ui._get_set('update_check',True,bool):
                updata, index, vname, gxjs = checkupdata(is_frozen)
                if updata:
                    window.updata_window_show(index, vname, gxjs, is_frozen)
        threading.Thread(target=upc).start()
        loop.run_forever()