import os
import sys
import logging
from typing import Any

__all__  = ['logger','config', 'init_config', 'update_settings', 'save_settings', 'pip_install_models',  'gs', 'ups', 'try_except']

# 创建日志记录器
logger = logging.getLogger('__main__')
logger.setLevel(logging.DEBUG)

if not os.path.exists('log'):
    os.mkdir('log')
if os.path.exists('log/loger1.log'):
    if os.path.exists('log/loger2.log'):
        os.remove('log/loger2.log')
    os.rename('log/loger1.log', 'log/loger2.log')

handler = logging.FileHandler('log/loger1.log', 'w', encoding='utf-8')
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

errorfuncs = []

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error(
        "严重错误: \n",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    for func in errorfuncs:
        func(exc_type, exc_value)

def add_errorfunc(func):
    """用于添加错误处理函数
    函数必须接收参数: exc_type, exc_value
    """
    global errorfuncs
    errorfuncs.append(func)


def try_except(errlogtext = "", func_ = None):
    """用于初始化错误处理的装饰器"""
    def try_(func):
        def main(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if func_ is not None: func_(e=e)
                logger.error(f"{errlogtext}: {e}", exc_info=True)
        return main
    return try_

from configparser import ConfigParser

SETTINGTYPE = dict[str, Any]
config_file = 'config.ini'

config = ConfigParser()

def init_config():
    global config
    try:
        if not os.path.exists(config_file):
            logger.warning("未找到配置文件 config.ini, 尝试创建默认配置文件")
            save_settings()
        config.read(config_file, encoding='utf-8')
        check_sections()
    except Exception as e:
        logger.error(f"无法加载配置文件: {e}", exc_info=True)

def check_sections():
    sectionlist = ['GUI', 'FloatingWindow']
    s_ = False
    for section in sectionlist:
        if not config.has_section(section):
            config.add_section(section)
            s_ = True
    if s_: save_settings()

def update_settings(**kwargs: SETTINGTYPE):
    global config
    try:
        logger.info(f"修改配置: {kwargs}")
        for section in kwargs.keys():
            if not config.has_section(section):
                config.add_section(section)
            data = kwargs[section]
            for key in data.keys():
                config.set(section, key, str(data[key]))
        save_settings()
    except Exception as e:
        logger.error(f"修改配置失败: {e}")

def save_settings():
    global config
    with open(config_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def pip_install_models(import_models_func: callable, pip_modelname: str):
    try:
        import_models_func()
    except ModuleNotFoundError as e:
        logger.warning(f"缺少依赖包 {e.name}")
        # 检查是否是编译版本
        if getattr(sys, 'frozen', False):
            logger.error("编译错误: 请确保编译时已安装所有依赖包")
            sys.exit(1)
        else:
            # 尝试下载依赖包
            python_exe = sys.executable
            logger.info(f"正在尝试下载依赖包到{python_exe}")
            try:
                try:
                    os.system(f"{python_exe} -m pip install {pip_modelname}")
                except Exception as e:
                    logger.error(f"下载依赖包 {pip_modelname} 失败: {e}")
                    logger.warning(f"尝试使用阿里云镜像源下载依赖包 {pip_modelname}")
                    os.system(f"{python_exe} -m pip install {pip_modelname} -i https://mirrors.aliyun.com/pypi/simple/")
                logger.info(f"已安装依赖包: {pip_modelname}")
                import_models_func()
            except Exception as e:
                logger.error(f"依赖包安装失败: {e}")
                sys.exit(1)
    except Exception as e:
        logger.error(f"无法导入模块: {e}")


def gs(section, option, default, type_ = None, debugn = ""):
    if type_ == bool:
        data = config.getboolean(section, option, fallback=default)
    else :
        data = config.get(section, option, fallback=default)
    logger.debug(f' [{debugn}] -获取配置项 {option} 的值: {data}')
    if type_ is None:
        return data
    else:return type_(data)

def ups(section, option: str, value, debugn = ""):
    config.set(section, option, str(value))
    logger.debug(f'[{debugn}] 更新配置项 {option} 的值: {value}')
    save_settings()
