import sys
import json
import asyncio
import argparse

import system_utils
system_utils.IS_FROZEN = IS_FROZEN = getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS") or ("__compiled__" in globals())

VER2 = (1, 3, 6, 2)
BINARY_BUILD = 0
v1      = "v" + ".".join(map(str, VER2[0:3]))
F_      = f"-beta.{BINARY_BUILD}"
vname   = v1 + (F_ if IS_FROZEN else f"+code.{VER2[3]}")
Fvname  = v1 +  F_
__version__ = vname

system_utils.VER2  = VER2
system_utils.vname = vname
IS_NUITKA = IS_FROZEN and "__compiled__" in globals()

from system_utils import (check_run,AppisRunning,
     getlogger, upmod_logger, add_errorfunc, handle_exception
    ,init_config, pip_install_models
    ,handle_update_mode,handle_end_update, try_except
)

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('-updatemode', action='store_true', help='更新模式标志')
parser.add_argument('-endup', action='store_true', help='更新结束标志')
parser.add_argument('-startup', action='store_true', help='用于测试应用能否通过start.bat脚本正常启动')
parser.add_argument('-start_', action='store_true', help='开机启动标志')
args = parser.parse_args()

if args.start_:
    system_utils.SLEEP_TIME = 10

if args.startup:
    print("Success!")
    sys.exit(0)

# 检查软件是否已经运行
try:
    check_run()
except AppisRunning:
    from PyQt5.QtWidgets import QMessageBox, QWidget, QApplication
    from qasync import QEventLoop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.sleep(0.1))
    QMessageBox.critical(QWidget(),"程序正在运行", "错误程序正在运行", QMessageBox.Ok)
    sys.exit(0)

# 如果是更新模式，使用简单日志输出
if args.updatemode:
    logger = upmod_logger()
else:
    logger = getlogger()

# 设置全局异常钩子
sys.excepthook = handle_exception

if IS_FROZEN:
    # 更新模式
    if args.updatemode:
        logger.info("进入更新模式...")
        handle_update_mode()

    # 更新结束模式
    if args.endup:
        logger.info("进入更新结束模式...")
        handle_end_update()
else:
    with open("version.json", "w", encoding="utf-8") as f:
        sdata = {
             "name": vname
            ,"version": 2
            ,"VER2": VER2
            ,"gxjs": "优化应用启动，修复无法保存文件的问题等"
        }
        text = json.dumps(sdata, ensure_ascii=False, indent=2)
        frozendata = {
                 "name": Fvname
                ,"version": 2
                ,"VER2": VER2
                ,"updateTime": "2025-10-24-4:00:00"
                ,"gxjs": "本次更新新增浮窗背景纯度设置，修复了定时断开和保存文件无法使用的问题，以及一系列优化"
                ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{Fvname}"
                ,"download": f"https://gitcode.com/lin15266115/HeartBeat/releases/download/{Fvname}/HRMLink.exe"
            }
        frozentext = f""",\n\n\n  "frozen":{json.dumps(frozendata, ensure_ascii=False)}\n}}"""
        text = text[0:-2] + frozentext
        f.write(text)
    try:
        from importlib import import_module
        buildbatmain = import_module("build_bat").main
        buildbatmain(VER2, Fvname)
    except Exception: pass

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

from importlib.metadata import metadata as get_metadata, distributions, distribution, Distribution
packages: list[dict[str, str|int]] = []
packages.append({"nameandversion": "包名 == 版本号", "len": 10, "license":"开源许可证", "name":""})
if not IS_NUITKA: # 避免nuitka编译后无法运行
    for entry in distributions():
        nameandversion = f"{entry.name} == {entry.version}"
        packages.append({"name": entry.name, "nameandversion": nameandversion, "len": len(nameandversion)})

def add_pak(name:Distribution):
    @try_except(f"手动获取依赖包名{name}", exit_ = False, exc_info=False)
    def add_pak_():
        NaVer = f"{name.name} == {name.version}"
        packages.append({"name": name.name, "nameandversion": NaVer, "len": len(NaVer)})
    if name.name not in [x["name"] for x in packages]:
        add_pak_()

def get_license(name:str):
    try:
        return get_metadata(name).get('License')
    except Exception as e:
        logger.warning(f"无法获取依赖包 {name} 的授权信息: {e}")
        return "Unknown"

# pyinstaller编译的应用必须直接使用`distribution`函数获取模块信息, 否则会报错
data = [
     distribution('bleak'),
     distribution('pyinstaller') if not IS_NUITKA else None,
     distribution('PyQt5'),distribution('PyQt5-Qt5'),distribution('PyQt5_sip')
    ,distribution('qasync'),distribution('winrt-runtime')
]
[add_pak(d_) if d_ else None for d_ in data]

max_len = max(map(lambda x: x["len"], packages))

packageslogtext = "\n  ".join(
    map(
    lambda x: f"{x["nameandversion"]:<{max_len+2}}-{get_metadata(x["name"]).get('License') if "license" not in x else x["license"]}"
    , packages
    )
)

logger.info("[项目依赖包清单:\n  "+packageslogtext + "\n]")

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

    window = MainWindow()
    window.show()
    hwnd = window.winId()

    def errwin(exc_type, exc_value):
        window.verylarge_error(f"{exc_type.__name__}: {exc_value}")
    add_errorfunc(errwin)


    screen = app.primaryScreen()
    screen.logicalDotsPerInchChanged.connect(window.auto_FixedSize)

    with loop:
        screens = app.screens()
        loop.run_forever()