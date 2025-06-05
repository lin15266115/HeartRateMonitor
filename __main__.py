import os
import sys
import json
import asyncio
import subprocess

is_frozen = getattr(sys, 'frozen', False)

frozenvname = "v1.2.2-alpha"
frozenver = 1.002002

from config_manager import logger, init_config, add_errorfunc, handle_exception

# 设置全局异常钩子
sys.excepthook = handle_exception

if is_frozen:
    __version__ = frozenvname
    ver = frozenver
else:
    __version__ = '1.3.0-build'
    ver = 1.00300001
    # 检查或创建文件
    os.makedirs("log", exist_ok=True)
    with open("version.json", "w", encoding="utf-8") as f:
        data = {
             "name": __version__
            ,"version": ver
            ,"frozen-name":  frozenvname
            ,"frozen-version": frozenver
            ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/{frozenvname}"
            ,"Githubindex": f"https://github.com/lin15266115/HeartRateMonitor/tags"
        }
        json.dump(data, f, ensure_ascii=False, indent=4)

logger.info(f'运行程序 -{__version__}[{ver}] -{__file__}')

init_config()

from UI import MainWindow, QApplication, QEventLoop

import urllib.request

# 检查更新
def checkupdata() -> tuple[bool, str]:
    logger.info("检查更新中...")
    try:
        url = "https://raw.gitcode.com/lin15266115/HeartBeat/raw/main/version.json"

        with urllib.request.urlopen(url) as response: 
            # 读取json格式
            data = json.loads(response.read().decode('utf-8'))

            if is_frozen:
                vnumber = data['frozen-version']
                vname = data['frozen-name']
                up_index  = data['index']
            else:
                vnumber = data['version']
                vname = data['name']
                up_index = 'https://gitcode.com/lin15266115/HeartBeat'
            if vnumber > ver:
                logger.info(f"发现新版本 {vname}[{vnumber}]")
                return True, up_index
            else:
                logger.info("当前已是最新版本")
    except Exception as e:
        logger.warning(f"更新检查失败: {e}")
    return False, ''

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

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
            updata, index = checkupdata()
            if updata:
                window.updata_window_show(index)
            loop.run_forever()
    except Exception as e:
        logger.error(f"未标识的异常：{e}")
        sys.exit(1)