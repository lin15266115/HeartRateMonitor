import sys
import json
import asyncio
import argparse
import threading

is_frozen = getattr(sys, 'frozen', False)

frozenvname = "v1.3.0-alpha"
frozenver = 1.003000

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

    # 如果是更新模式，直接处理更新并退出
    if args.updatemode:
        logger.info("进入更新模式...")
        handle_update_mode()

    # 如果是更新结束模式，清理更新文件后继续
    if args.endup:
        logger.info("进入更新结束模式...")
        handle_end_update()
else:
    __version__ = '1.3.0-build'
    ver = 1.00300005
    with open("version.json", "w", encoding="utf-8") as f:
        sdata = {
             "name": __version__
            ,"version": ver
            ,"gxjs": "本次更新了用于版本更新自动替换的相关功能"
            ,"frozen":{
                 "name":  frozenvname
                ,"version": frozenver
                ,"gxjs": "本次更新修改了更新检查相关功能, 优化了日志记录, 新增浮窗亮度滑条设置"
                ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{frozenvname}"
                ,"download": f"https://gitcode.com/lin15266115/HeartBeat/releases/download/{frozenvname}/HRMLink.exe"
            }
            ,"frozen-name":  "版本更新: 允许关闭版本更新检查"
            ,"frozen-version": frozenver
            ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{frozenvname}"
        }
        json.dump(sdata, f, ensure_ascii=False, indent=2)

logger.info(f'运行程序 -{__version__}[{ver}] -{__file__}')

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

import urllib.request

# 检查更新
def checkupdata() -> tuple[bool, str, str, str]:
    logger.info("检查更新中...")
    try:
        url = "https://raw.gitcode.com/lin15266115/HeartBeat/raw/main/version.json"

        with urllib.request.urlopen(url) as response: 
            # 读取json格式
            data = json.loads(response.read().decode('utf-8'))

            if is_frozen:
                data_ = data['frozen']
                up_index = data_['index']
            else:
                data_ = data
                up_index = 'https://gitcode.com/lin15266115/HeartBeat'
            vnumber = data_['version']
            vname = data_['name']
            gxjs = data_['gxjs']
            if vnumber > ver:
                logger.info(f"发现新版本 {vname}[{vnumber}]")
                return True, up_index, vname, gxjs
            else:
                logger.info("当前已是最新版本")
    except Exception as e:
        logger.warning(f"更新检查失败: {e}")
    return False, '', '', ''

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
                updata, index, vname, gxjs = checkupdata()
                if updata:
                    window.updata_window_show(index, vname, gxjs, is_frozen)
        threading.Thread(target=upc).start()
        loop.run_forever()