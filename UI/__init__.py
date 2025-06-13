from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QWidget, QLineEdit,
    QSpinBox, QMessageBox, QCheckBox, QGroupBox,
    QSystemTrayIcon, QMenu, QSlider, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap

import time
import threading
import webbrowser

from .fhrw import *
from .DevCtrl import *
from .basicwidgets import *
from .heartratepng import *
from .UpDownloadwin import DownloadWindow
from config_manager import try_except, ups, gs, start_update_program, logger, checkupdate, is_frozen

# 主窗口类
class MainWindow(QMainWindow):
    updata_window_show_ = pyqtSignal(str, str, str, bool, str)
    @try_except("主窗口初始化失败")
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.setup_ui()
        self.setup_connections()
        
        self.updata_window_show_.connect(self.updata_window_show)

        # 启动后台线程检查更新
        if self.settings_ui._get_set("update_check", True, bool):
            self.start_auto_update_check()

    def start_auto_update_check(self):
        """启动后台线程进行自动更新检查"""
        def update_check_thread():
            try:
                # 检查更新
                update_available, index, vname, gxjs, down_url = checkupdate()
                if update_available:
                    # 使用信号机制将结果显示到主线程
                    self.updata_window_show_.emit(index, vname, gxjs, is_frozen, down_url)
            except Exception as e:
                logger.error(f"自动更新检查失败: {str(e)}")
    
        # 创建并启动线程
        threading.Thread(target=update_check_thread, daemon=True).start()
        
    def setup_ui(self):
        self.setWindowTitle(f"心率监测设置 -[{self.version}]")
        self.setFixedSize(700, 500)
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

        self.setWindowIcon(self.settings_ui.app_icon)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.float_ui, 2)
        right_layout.addWidget(self.settings_ui, 1)

        setting_layout.addLayout(self.device_ui, stretch=2)
        setting_layout.addLayout(right_layout, stretch=1)

        main_layout.addWidget(self.status_label)

    def setup_connections(self):
        # 连接各模块之间的信号和槽
        self.device_ui.heart_rate_updated.connect(self.float_ui.update_heart_rate)
        self.device_ui.status_changed.connect(self.status_label.setText)
        self.settings_ui.quit_application.connect(self.close_application)
        self.settings_ui.show_settings.connect(self.show_window)

    def show_window(self):
        """显示设置窗口"""
        self.show()
        self.activateWindow()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.settings_ui.tray_icon and self.settings_ui.tray_icon.isVisible():
            # 如果启用了托盘图标，则隐藏窗口而不是退出
            self.hide()
            event.ignore()
        else:
            # 否则正常退出
            if self.device_ui.ble_monitor.client and self.device_ui.ble_monitor.client.is_connected:
                reply = QMessageBox.question(
                    self, '确认',
                    "当前已连接设备，确定要退出吗?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    self.close_application()
                    event.accept()
                else:
                    event.ignore()
            else:
                self.close_application()
                event.accept()

    def verylarge_error(self, error_message: str):
        QMessageBox.critical(self, "严重错误", error_message, QMessageBox.Ok)
        self.close_application()

    def close_application(self):
        """执行退出程序的操作"""
        if self.settings_ui.tray_icon:
            self.settings_ui.tray_icon.hide()
        self.float_ui.floating_window.close()
        QApplication.quit()

    def updata_window_show(self, index, vname, gxjs, is_frozen, down_url):
        self.updmsg_box = QMessageBox(self)
        logger.debug(f"开启了更新提示窗口(-1/-2)")
        self.updmsg_box.setWindowTitle('提示')
        self.updmsg_box.setText(f'版本-{vname} 已更新:\n {gxjs}')
        self.updmsg_box.addButton("查看新版本", QMessageBox.YesRole)
        btn_no = self.updmsg_box.addButton("取消", QMessageBox.NoRole)
        self.updmsg_box.setDefaultButton(btn_no)
        logger.debug(f"窗口正常加载 -1")
        reply = self.updmsg_box.exec()
        logger.debug(f"reply: {reply} -2")
        if reply == 0:
            updwin = DownloadWindow(self)
            updwin.set_url(down_url)
            updwin.show()

# 应用设置UI类
class AppSettingsUI(QWidget):
    quit_application = pyqtSignal()
    show_settings = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_tray_icon()

    def setup_ui(self):
        pixmap = QPixmap()
        pixmap.loadFromData(heart_rate_png)
        self.app_icon = QIcon(pixmap)

        layout = QVBoxLayout()
        
        settings_group = QGroupBox("软件设置")
        settings_layout = QVBoxLayout()
        
        CheackBox_(
             "启用托盘图标"
            ,settings_layout
            ,self._get_set("tray_icon", True, bool)
            ,self.toggle_tray_icon
        )

        CheackBox_(
             "启动时检查更新"
            ,settings_layout
            ,self._get_set("update_check", True, bool)
            ,lambda state: self._up_set("update_check", state==Qt.Checked)
        )

        # 添加手动检查更新按钮
        self.check_update_btn = QPushButton("手动检查更新(未实现)")
        self.check_update_btn.clicked.connect(self.check_for_updates)
        
        settings_layout.addWidget(self.check_update_btn)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        self.setLayout(layout)


    def setup_tray_icon(self):
        """设置系统托盘图标"""

        if QSystemTrayIcon.isSystemTrayAvailable():

            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.app_icon)

            tray_menu = QMenu()

            # 添加菜单项
            show_settings_action = tray_menu.addAction("打开设置")
            show_settings_action.triggered.connect(self.show_settings.emit)

            tray_menu.addSeparator()

            quit_action = tray_menu.addAction("退出程序")
            quit_action.triggered.connect(self.quit_application.emit)

            self.tray_icon.setContextMenu(tray_menu)
            if self._get_set('tray_icon', True, bool):
                self.tray_icon.show()
            self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.Trigger:  # 单击
            # 显示托盘菜单
            self.tray_icon.contextMenu().popup(self.tray_icon.geometry().center())

    def toggle_tray_icon(self, state):
        """切换托盘图标显示"""
        if self.tray_icon:
            if state == Qt.Checked:
                self.tray_icon.show()
                self._up_set('tray_icon', True)
            else:
                self.tray_icon.hide()
                self._up_set('tray_icon', False)

    def _up_set(self, option: str, value):
        ups('GUI', option, value, debugn="GUI")

    def _get_set(self, option: str, default, type_ = None):
        return gs('GUI', option, default, type_ , debugn="GUI")

    def check_for_updates(self):pass