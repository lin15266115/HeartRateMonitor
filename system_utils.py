import os
import sys
import json
import shutil
import logging
import datetime
import subprocess
import urllib.request
from typing import Any

VER:float
VER2:tuple[int,int,int,int]
IS_FROZEN = None

# --------日志处理--------

class AppisRunning(Exception):pass

def getlogger():
    global logger
    # 创建日志记录器
    logger = logging.getLogger('__main__')
    logger.setLevel(logging.DEBUG)

    if not os.path.exists('log'):
        os.mkdir('log')
    if os.path.exists('log/loger1.log'):
        if os.path.exists('log/loger2.log'):
            os.remove('log/loger2.log')
        try:
            os.rename('log/loger1.log', 'log/loger2.log')
        except Exception:
            raise AppisRunning('程序正在运行!')

    handler = logging.FileHandler('log/loger1.log', 'w', encoding='utf-8')
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def upmod_logger():
    global logger

    logger = logging.getLogger('__main__')

    if not os.path.exists('log'):
        os.mkdir('log')

    handler = logging.FileHandler('log/uplog.log', 'a', encoding='utf-8')
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --------错误输出处理函数--------

errorfunc = None

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    elif isinstance(exc_type, ModuleNotFoundError):
        logger.warning("缺少模块: %s", exc_type.name)
        logger.error(
            "模块导入错误: \n",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        if errorfunc:
            errorfunc(exc_type, exc_value)
        pip_install_package(exc_type.name)
    logger.error(
        "严重错误: \n",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    if errorfunc:
        errorfunc(exc_type, exc_value)

def add_errorfunc(func):
    """用于添加错误处理函数
    函数必须接收参数: exc_type, exc_value
    """
    global errorfunc
    errorfunc= func


def try_except(errlogname = "", func_ = None):
    """用于初始化错误处理的装饰器"""
    def try_(func):
        def main(*args, **kwargs):
            try:
                logger.info(f"{errlogname} 开始")
                anything = func(*args, **kwargs)
                logger.info(f"{errlogname} 完成")
                return anything
            except Exception as e:
                if func_ is not None: func_(e=e)
                logger.error(f"严重错误: {errlogname} 失败: {e}", exc_info=True)
                sys.exit(1)
        return main
    return try_

# --------配置文件操作--------

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
    sectionlist = ['GUI', 'FloatingWindow', 'Device']
    s_ = False
    for section in sectionlist:
        if not config.has_section(section):
            config.add_section(section)
            s_ = True
    if s_: save_settings()

@try_except("修改配置")
def update_settings(**kwargs: SETTINGTYPE):
    global config
    logger.info(f"{kwargs}")
    for section in kwargs.keys():
        if not config.has_section(section):
            config.add_section(section)
        data = kwargs[section]
        for key in data.keys():
            config.set(section, key, str(data[key]))
    save_settings()

def save_settings():
    global config
    with open(config_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def gs(section, option, default, type_:type = None, debugn = ""):
    if type_ == bool:
        data = config.getboolean(section, option, fallback=default)
    else :
        data = config.get(section, option, fallback=default)
    logger.debug(f' [{debugn}] -获取配置项 {option} 的值: {data}')
    if data is None or data == "None":
        return default
    if type_ is None:
        return data
    else:return type_(data)

def ups(section, option: str, value, debugn = ""):
    config.set(section, option, str(value))
    logger.debug(f'[{debugn}] 更新配置项 {option} 的值: {value}')
    save_settings()

# --------下载前置--------

def pip_install_models(import_models_func: callable, pip_modelname: str):
    try:
        import_models_func()
    except ModuleNotFoundError as e:
        logger.warning(f"缺少依赖包 {e.name}")
        if IS_FROZEN:
            logger.error("编译时错误: 请确保编译时已安装所有依赖包")
            sys.exit(1)
        else:
            pip_install_package(pip_modelname)
    except Exception as e:
        logger.error(f"无法导入模块: {e}")

def pip_install_package(package_name: str):
    # 尝试下载依赖包
    python_exe = sys.executable
    logger.info(f"正在尝试下载依赖包到: {python_exe}")
    try:
        try:
            os.system(f"{python_exe} -m pip install {package_name}")
        except Exception as e:
            logger.error(f"下载依赖包 {package_name} 失败: {e}")
            logger.warning(f"尝试使用阿里云镜像源下载依赖包 {package_name}")
            os.system(f"{python_exe} -m pip install {package_name} -i https://mirrors.aliyun.com/pypi/simple/")
        logger.info(f"已安装依赖包: {package_name}")
    except Exception as e:
        logger.error(f"依赖包安装失败: {e}", exc_info=True)
        sys.exit(1)

# --------启动管理--------

import winreg as reg

def check_startbat(path):
    "检查启动脚本"
    try:
        result = subprocess.run([path, "--startup"], capture_output=True, timeout=5)
        logger.info(f"启动脚本: {result.stdout.decode()}")
        return True
    except Exception as e:
        logger.error(f"启动项检查失败: {e}", exc_info=True)
        return False

def add_to_startup():
    # 获取当前可执行文件路径
    if IS_FROZEN:
        # 如果是打包后的exe
        # 获取当前可执行文件路径
        value = os.path.abspath(sys.executable)
    else:
        # 如果是脚本
        # 获取当前可执行文件目录
        b_ = os.path.dirname(os.path.abspath(sys.argv[0]))
        value = os.path.join(b_, "start.bat")
        # 测试启动脚本是否正确运行
        if not check_startbat(value):
            return "脚本"

    logger.info(f"正在添加到启动项 {value}")

    # 应用的名称
    app_name = "Zero_linofe-HRMlink"
    
    # 打开注册表中的启动项键
    key = reg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        registry_key = reg.OpenKey(key, key_path, 0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, app_name, 0, reg.REG_SZ, rf'"{value}"')
        reg.CloseKey(registry_key)
        return "成功"
    except WindowsError:
        logger.error("添加到启动项失败", exc_info=True)
        return "启动项"

def remove_from_startup():
    app_name = "Zero_linofe-HRMlink"
    key = reg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        registry_key = reg.OpenKey(key, key_path, 0, reg.KEY_WRITE)
        reg.DeleteValue(registry_key, app_name)
        reg.CloseKey(registry_key)
        return True
    except WindowsError:
        logger.error("无法从注册表中删除启动项", exc_info=True)
        return False

# --------应用更新--------

# 处理更新模式
def handle_update_mode():
    """处理更新模式，替换旧的主程序"""
    try:
        # 获取当前可执行文件路径(upd.exe)
        current_exe = sys.executable
        logger.info(f"当前更新程序路径: {current_exe}")

        # 获取目标路径(HRMLink.exe)
        target_dir = os.path.dirname(current_exe)
        target_exe = os.path.join(target_dir, "HRMLink.exe")

        # 删除旧的主程序
        if os.path.exists(target_exe):
            logger.info("正在删除旧的主程序...")
            os.remove(target_exe)

        # 将upd.exe复制为HRMLink.exe
        logger.info("正在复制更新文件...")
        shutil.copy2(current_exe, target_exe)
        
        # 以-endup参数运行新的主程序
        logger.info("启动新的主程序...")
        os.startfile(target_exe, arguments="-endup")

        # 退出当前进程
        logger.info("更新程序即将退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"更新过程中出错: {e}")
        sys.exit(1)

# 处理更新结束模式
def handle_end_update():
    """处理更新结束，清理更新文件"""
    try:
        # 获取当前可执行文件路径(HRMLink.exe)
        current_exe = sys.executable
        logger.info(f"当前主程序路径: {current_exe}")
        
        # 获取更新文件路径(upd.exe)
        target_dir = os.path.dirname(current_exe)
        update_exe = os.path.join(target_dir, "upd.exe")
        
        # 删除更新文件
        if os.path.exists(update_exe):
            logger.info("正在清理更新文件...")
            os.remove(update_exe)
    except Exception as e:
        logger.error(f"清理更新文件时出错: {e}")

# 启动更新程序
def start_update_program():
    """启动更新程序"""
    try:
        # 获取当前可执行文件路径(HRMLink.exe)
        current_exe = sys.executable
        logger.info(f"当前主程序路径: {current_exe}")
        
        # 获取更新文件路径(upd.exe)
        target_dir = os.path.dirname(current_exe)
        update_exe = os.path.join(target_dir, "upd.exe")
        
        # 启动更新程序
        logger.info("正在启动更新程序...")
        os.startfile(update_exe, arguments="-updatemode")

        logger.info("更新程序已启动，请稍等...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动更新程序时出错: {e}")
        sys.exit(1)

def checkupdate() -> tuple[bool, str, str, str, str]:
    logger.info("检查更新中...")
    try:
        url = "https://raw.gitcode.com/lin15266115/HeartBeat/raw/main/version.json"

        with urllib.request.urlopen(url) as response: 
            # 读取json格式
            data = json.loads(response.read().decode('utf-8'))
            
            durl = data['frozen']['download']

            if IS_FROZEN:
                data_ = data['frozen']
                up_index = data_['index']
                updatetime = data_['updateTime']
                try:
                    if datetime.datetime.now() < datetime.datetime.strptime(updatetime, '%Y-%m-%d-%H:%M:%S'):
                        return False, '', '', '', ''
                except Exception as e:
                    logger.error(f"更新时间检查失败:{e}")
            else:
                data_ = data
                up_index = 'https://gitcode.com/lin15266115/HeartBeat'
            vnumber = data_['version']
            vname = data_['name']
            gxjs = data_['gxjs']
            if vnumber > VER:
                logger.info(f"发现新版本 {vname}[{vnumber}]")
                return True, up_index, vname, gxjs, durl
            else:
                logger.info("当前已是最新版本")
    except Exception as e:
        logger.warning(f"更新检查失败: {e}")
    return False, '', '', '', ''
