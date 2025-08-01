from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QWidget,
    QMessageBox, QGroupBox,
    QSystemTrayIcon, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal

import time
import threading

from .DevCtrl import *
from .basicwidgets import *
from .heartratepng import *
from .UpDownloadwin import UpdWindow as DownloadWindow
from system_utils import IS_FROZEN, VER2, logger, try_except, ups, gs, checkupdate, add_to_startup, remove_from_startup, check_startup

from .Floatingwin_old import *

# 主窗口类
class MainWindow(QMainWindow):
    updata_window_show_ = pyqtSignal(str, str, str, str)
    iserror = False
    @try_except("主窗口初始化")
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.setup_ui()
        self.setup_connections()
        
        self.updata_window_show_.connect(self.updata_window_show)

        # 启动后台线程检查更新
        if self.settings_ui._get_set("update_check", False, bool):
            self.start_update_check()
        
        self.settings_ui.check_startup()

    def auto_FixedSize(self):
        self.setWindowTitle(f"心率监测设置 -[{self.version}]")
        # 获取逻辑DPI
        sc = self.screen()
        x_ = sc.logicalDotsPerInchX()
        y_ = sc.logicalDotsPerInchY()
        def sfs(x_,y_):
            self.logical_dpix = x_
            self.logical_dpiy = y_
            logger.info(f"逻辑DPI: {self.logical_dpix}x{self.logical_dpiy}")
            x =  int(self.logical_dpix / 96 * 700)
            y = int(self.logical_dpiy / 96 * 500)
            self.setFixedSize(x, y)
            # 应用字体大小
            self.setStyleSheet("font-size: " + str(int(self.logical_dpiy / 96 * 12)) + "px;")

        if not hasattr(self, "logical_dpix") or not hasattr(self, "logical_dpiy"):
            sfs(x_,y_)
        elif self.logical_dpix != x_ or self.logical_dpiy != y_:
            sfs(x_,y_)

    def setup_ui(self):

        self.auto_FixedSize()

        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)


        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        setting_layout = QHBoxLayout()
        main_layout.addLayout(setting_layout, stretch=2)

        # 添加各个模块
        self.device_ui = DeviceConnectionUI(self.status_label)
        self.float_ui = FloatingWindowSettingUI()
        self.settings_ui = AppSettingsUI()

        self.setWindowIcon(get_icon())

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.float_ui, 5)
        right_layout.addWidget(self.settings_ui, 3)

        setting_layout.addLayout(self.device_ui, stretch=2)
        setting_layout.addLayout(right_layout, stretch=1)

        main_layout.addWidget(self.status_label)

    def setup_connections(self):
        # 连接各模块之间的信号和槽
        self.device_ui.heart_rate_updated.connect(self.float_ui.update_heart_rate)
        self.device_ui.status_changed.connect(self.status_label.setText)
        self.settings_ui.quit_application.connect(self.check_device_status_before_close)
        self.settings_ui.show_settings.connect(self.show_window)
        self.settings_ui.updsig.connect(self.start_update_check)

    def show_window(self):
        """显示设置窗口"""
        self.show()
        self.activateWindow()

    def closeEvent(self, a0):
        """窗口关闭事件"""
        if self.settings_ui._get_set("use_bg", False, bool):
            # 如果允许后台运行，则隐藏窗口
            self.hide()
            a0.ignore()
        else:
            self.check_device_status_before_close(a0)
    # 检查设备连接状态后执行退出逻辑
    def check_device_status_before_close(self, event = None):
        if event:
            def e_accept():event.accept()
            def e_ignore():event.ignore()
        else:
            e_accept = e_ignore = lambda: None

        # 否则正常退出
        if self.device_ui.ble_monitor.client and self.device_ui.ble_monitor.client.is_connected:
            reply = QMessageBox.question(
                self, '确认',
                "当前已连接设备，确定要退出吗?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.close_application()
                e_accept()
            else:
                e_ignore()
        else:
            self.close_application()
            e_accept()


    def verylarge_error(self, error_message: str):
        if not self.iserror:
            self.iserror = True
            QMessageBox.critical(self, "严重错误", error_message, QMessageBox.Ok)
        self.close_application()

    def close_application(self):
        """执行退出程序的操作"""
        if self.settings_ui.tray_icon:
            self.settings_ui.tray_icon.hide()
        self.float_ui.floating_window.close()
        QApplication.quit()

    def start_update_check(self):
        """启动后台线程进行自动更新检查"""
        def update_check_thread():
            try:
                # 检查更新
                update_available, index, vname, gxjs, down_url = checkupdate()
                if update_available:
                    # 使用信号机制将结果显示到主线程
                    self.updata_window_show_.emit(index, vname, gxjs, down_url)
            except Exception as e:
                logger.error(f"自动更新检查失败: {str(e)}")
    
        # 创建并启动线程
        threading.Thread(target=update_check_thread, daemon=True).start()

    def updata_window_show(self, index, vname, gxjs, down_url):
        self.updmsg_box = QMessageBox(self)
        logger.debug(f"开启了更新提示窗口(-1/-2)")
        self.updmsg_box.setWindowTitle('提示')
        self.updmsg_box.setText(f'版本-{vname} 已更新:\n {gxjs}')
        self.updmsg_box.addButton("查看新版本", QMessageBox.YesRole)
        btn_no = self.updmsg_box.addButton("取消", QMessageBox.NoRole)
        self.updmsg_box.setDefaultButton(btn_no)
        logger.debug(f"窗口正常加载 (-1)")
        reply = self.updmsg_box.exec()
        logger.debug(f"reply: {reply} (-2)")
        if reply == 0:
            self.updwin = DownloadWindow(self)
            self.updwin.set_url(down_url,index)
            self.updwin.show()

# 应用设置UI类
class AppSettingsUI(QWidget):
    quit_application = pyqtSignal()
    show_settings = pyqtSignal()
    updsig = pyqtSignal()

    @try_except("设置UI初始化")
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_tray_icon()
    
    def check_startup(self):
        Csup1, Csup2 = check_startup()
        print(Csup1, end=", ")
        print(Csup2)
        if Csup2 != "":
            logger.debug("[GUI] 检查到启动项")
            if Csup1: 
                self._up_set('startup', True)
                self.set_starup.setChecked(True)
            else:
                re = QMessageBox.warning(self, "提示", f"启动项被其它应用程序占用,是否覆盖?\n相关启动项位置: {Csup2}", QMessageBox.Yes | QMessageBox.No)
                if re == QMessageBox.Yes:
                    add_to_startup()
                    self._up_set('startup', True)
                    self.set_starup.setChecked(True)
                else:
                    self._up_set('startup', False)
                    self.set_starup.setChecked(False)
        else:
            logger.debug("[GUI] 未检查到启动项")
            self._up_set('startup', False)
            self.set_starup.setChecked(False)

    def setup_ui(self):
        self.app_icon = get_icon()

        layout = QVBoxLayout()
        
        settings_group = QGroupBox("软件设置")
        settings_layout = QVBoxLayout()
        
        CheackBox_(
             "允许后台运行"
            ,settings_layout
            ,self._get_set("use_bg", False, bool)
            ,self.toggle_use_bg
        )

        self.set_starup = CheackBox_(
             "开机自启动"
             ,settings_layout
             ,self._get_set("startup", False, bool)
             ,self.toggle_startup
        )

        CheackBox_(
             "启动时检查更新"
            ,settings_layout
            ,self._get_set("update_check", False, bool)
            ,lambda state: self._up_set("update_check", state==Qt.Checked)
        )

        # 添加手动检查更新按钮
        self.check_update_btn = QPushButton("检查更新")
        self.check_update_btn.clicked.connect(self.updsig.emit)
        
        settings_layout.addWidget(self.check_update_btn)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        self.setLayout(layout)


    def setup_tray_icon(self):
        """设置系统托盘图标"""

        if QSystemTrayIcon.isSystemTrayAvailable():

            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(get_icon())

            tray_menu = QMenu()

            # 添加菜单项
            show_settings_action = tray_menu.addAction("打开设置")
            show_settings_action.triggered.connect(self.show_settings.emit)

            tray_menu.addSeparator()

            quit_action = tray_menu.addAction("退出程序")
            quit_action.triggered.connect(self.quit_application.emit)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.Trigger:  # 单击
            # 显示托盘菜单
            self.tray_icon.contextMenu().popup(self.tray_icon.geometry().center())

    def toggle_use_bg(self, state):
        """切换允许后台运行"""
        if state == Qt.Checked:
            self._up_set('use_bg', True)
        else:
            self._up_set('use_bg', False)
    
    def toggle_startup(self, state):
        """切换开机启动"""
        if state == Qt.Checked:
            output = add_to_startup()
            if output == "成功":
                self._up_set('startup', True)
            elif output == "脚本":
                QMessageBox.information(self, "提示", "测试启动脚本 start.bat 不通过, 请用文本编辑器打开并修改 PYTHONPATH 项为python目录", QMessageBox.Ok)
                self.set_starup.setChecked(False)
            elif output == "启动项":
                QMessageBox.information(self, "错误", "添加启动项失败", QMessageBox.Ok)
                self.set_starup.setChecked(False)
        else:
            remove_from_startup()
            self._up_set('startup', False)

    def _up_set(self, option: str, value):
        ups('GUI', option, value, debugn="GUI")

    def _get_set(self, option: str, default, type_ = None):
        return gs('GUI', option, default, type_ , debugn="GUI")
