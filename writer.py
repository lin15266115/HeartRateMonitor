import os
import sys
import logging
from typing import Any

__all__  = ['logger','config', 'init_config', 'update_settings', 'save_settings', 'install_models']

# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not os.path.exists('log'):
    os.mkdir('log')
if os.path.exists('log/loger1.log'):
    if os.path.exists('log/loger2.log'):
        os.remove('log/loger2.log')
    os.rename('log/loger1.log', 'log/loger2.log')

str
handler = logging.FileHandler('log/loger1.log', 'w', encoding='utf-8')
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

from configparser import ConfigParser

SETTINGTYPE = dict[str, Any]
config_file = 'config.ini'

config = ConfigParser()

def init_config():
    global config
    try:
        if not os.path.exists(config_file):
            logger.warning("未找到配置文件 config.ini, 尝试创建默认配置文件")
            config.add_section('FloatingWindow')
            save_settings()
        config.read(config_file, encoding='utf-8')
    except Exception as e:
        logger.error(f"无法加载配置文件: {e}")

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

def install_models(import_models_func: callable, pip_modelname: str):
    try:
        import_models_func()
    except ModuleNotFoundError as e:
        logger.warning(f"缺少依赖包 {e.name}")
        # 检查是否是编译版本
        if getattr(sys, 'frozen', False):
            logger.error("编译时错误: 请确保编译时已安装所有依赖包")
            sys.exit(1)
        else:
            # 尝试下载依赖包
            logger.info("正在尝试下载依赖包")
            # 获取python.exe路径
            python_exe = sys.executable
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