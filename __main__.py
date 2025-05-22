import os
import sys
import json

is_frozen = getattr(sys, 'frozen', False)

if os.path.exists("version.json"):
    with open("version.json", "r") as f:
        vp  = json.load(f)
        if is_frozen:
            __version__ = vp['frozen-name']
            ver = vp['frozen-version']
        else:
            __version__ = vp['name']
            ver = vp['version']
        

from writer import logger

logger.info(f'运行程序 -{__version__}[{ver}] -{__file__}')


from UI import *

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

        window = HeartRateMonitorGUI(__version__)
        window.show()

        def handle_exception(exc_type, exc_value, exc_traceback):
            """全局异常处理函数"""
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            logger.error(
                "严重错误: \n",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            # 报错弹窗
            window.verylarge_error(f"{exc_type.__name__}: {exc_value}")

        # 设置全局异常钩子
        sys.excepthook = handle_exception

        with loop:
            screens = app.screens()
            updata, index = checkupdata()
            if updata:
                window.updata_window_show(index)
            loop.run_forever()
    except Exception as e:
        logger.error(f"未标识的异常：{e}")
        if window:
            window.close_application()
        sys.exit(1)