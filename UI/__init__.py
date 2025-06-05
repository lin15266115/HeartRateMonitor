from .fhrw import *
from .DevCtrl import *
from  config_manager import *
from . import heartratepng

import webbrowser


def import_PyQt5():
    from . import importpyqt
    for key, mode in importpyqt.import_PyQt5().items():
        globals()[key] = mode

# 触发IDE python类型提示
try:
    if nothing:from .importpyqt import * # type: ignore
except:pass

pip_install_models(import_PyQt5, "pyqt5")

# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle(f"心率监测设置 -[{self.version}]")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(self.width(), self.height())
        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        setting_widget = QWidget()
        setting_layout = QHBoxLayout()
        setting_widget.setLayout(setting_layout)
        main_layout.addWidget(setting_widget, stretch=2)

        # 添加各个模块
        self.device_ui = DeviceConnectionUI(self.status_label)
        self.float_ui = FloatingWindowSettingUI()
        self.settings_ui = AppSettingsUI()

        self.setWindowIcon(self.settings_ui.app_icon)

        right_layout = QVBoxLayout()
        right_widget = QWidget()
        right_layout.addWidget(self.float_ui)
        right_layout.addWidget(self.settings_ui)
        right_widget.setLayout(right_layout)

        setting_layout.addWidget(self.device_ui, stretch=2)
        setting_layout.addWidget(right_widget, stretch=1)

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

    def updata_window_show(self, index):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('提示')
        msg_box.setText('检测到有新版本可以更新')
        msg_box.addButton("前往查看", QMessageBox.YesRole)
        btn_no = msg_box.addButton("取消", QMessageBox.NoRole)
        msg_box.setDefaultButton(btn_no)
        reply = msg_box.exec_()
        if reply == 0:
            webbrowser.open(index)

# 浮动窗口UI类
class FloatingWindowSettingUI(QWidget):
    def __init__(self):
        super().__init__()
        self.floating_window = FloatingHeartRateWindow()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        float_group = QGroupBox("浮动窗口设置")
        float_layout = QVBoxLayout()

        # 显示控制
        display_layout = QHBoxLayout()
        self.float_window_check = QCheckBox("显示浮动窗口")

        # 鼠标穿透设置
        fwindow_canlook = self.floating_window._get_set('canlook', True, bool)
        self.float_window_check.setChecked(fwindow_canlook)
        self.float_window_check.stateChanged.connect(self.toggle_floating_window)

        self.click_through_check = QCheckBox("鼠标穿透")
        self.click_through_check.setChecked(self.floating_window._get_set('lock', False, bool))
        self.click_through_check.stateChanged.connect(self.toggle_click_through)

        display_layout.addWidget(self.float_window_check)
        display_layout.addWidget(self.click_through_check)
        float_layout.addLayout(display_layout)

        # 文字颜色设置
        color_layout = QHBoxLayout()
        self.text_color_button = QPushButton("文字颜色")
        self.text_color_button.clicked.connect(self.set_text_color)

        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(20, 20)
        self.text_color_preview.setStyleSheet(f"background-color: {self.floating_window.text_color.name()}; border: 1px solid black;")

        color_layout.addWidget(QLabel("文字颜色:"))
        color_layout.addWidget(self.text_color_button)
        color_layout.addWidget(self.text_color_preview)
        color_layout.addStretch()
        float_layout.addLayout(color_layout)

        # 字体大小设置
        font_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 100)
        self.font_size_spin.setValue(self.floating_window.font_size)
        self.font_size_spin.valueChanged.connect(self.set_font_size)

        font_layout.addWidget(QLabel("字体大小:"))
        font_layout.addWidget(self.font_size_spin)
        float_layout.addLayout(font_layout)

        # 文字内容设置
        text_layout = QHBoxLayout()
        self.text_edit = QLineEdit()
        self.text_edit.setText(self.floating_window.text_base)
        self.text_edit.textChanged.connect(self.set_text_base)
        text_layout.addWidget(QLabel("文字内容:"))
        text_layout.addWidget(self.text_edit)
        float_layout.addLayout(text_layout)

        # 背景内边距设置
        padding_layout = QHBoxLayout()
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 100)
        self.padding_spin.setValue(self.floating_window.padding)
        self.padding_spin.valueChanged.connect(self.set_padding)

        padding_layout.addWidget(QLabel("背景内边距:"))
        padding_layout.addWidget(self.padding_spin)
        float_layout.addLayout(padding_layout)

        # 背景透明度设置
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        bgop = self.floating_window.bg_opacity
        self.opacity_slider.setValue(bgop)
        self.opacity_slider.valueChanged.connect(self.set_bg_opacity)

        opacity_layout.addWidget(QLabel("背景透明度:"))
        opacity_layout.addWidget(self.opacity_slider)
        float_layout.addLayout(opacity_layout)

        # 注册为常规窗口
        register_layout = QHBoxLayout()
        self.register_window_check = QCheckBox("注册为常规窗口(OBS捕获)")
        register_window_check_state = self.floating_window._get_set('register_as_window', False, bool)
        self.register_window_check.setChecked(register_window_check_state)
        self.register_window_check.stateChanged.connect(self.toggle_register_as_window)
        register_layout.addWidget(self.register_window_check)
        float_layout.addLayout(register_layout)

        float_group.setLayout(float_layout)
        layout.addWidget(float_group)
        self.setLayout(layout)

        # 显示浮动窗口
        if fwindow_canlook:
            self.floating_window.show()
        else:
            self.floating_window.hide()

    def update_heart_rate(self, heart_rate=None):
        self.floating_window.update_heart_rate(heart_rate)

    def toggle_floating_window(self, state):
        """切换浮动窗口显示"""
        if state == Qt.Checked:
            self.floating_window.show()
            self.floating_window._up_set('canlook', True)
        else:
            self.floating_window.hide()
            self.floating_window._up_set('canlook', False)

    def toggle_click_through(self, state):
        """切换鼠标穿透"""
        if state == Qt.Checked:
            self.floating_window.setWindowFlags(
                self.floating_window.windowFlags() | 
                Qt.WindowTransparentForInput
            )
            self.floating_window._up_set('lock', True)
        else:
            self.floating_window.setWindowFlags(
                self.floating_window.windowFlags() & 
                ~Qt.WindowTransparentForInput
            )
            self.floating_window._up_set('lock', False) 
        self.floating_window.show()

    def toggle_register_as_window(self, state):
        """切换是否注册为常规窗口"""
        self.floating_window.set_register_as_window(state == Qt.Checked)

    def set_text_color(self):
        """设置文字颜色"""
        color = QColorDialog.getColor(self.floating_window.text_color, self)
        if color.isValid():
            self.floating_window.set_text_color(color)
            self.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

    def set_font_size(self, size):
        """设置字体大小"""
        self.floating_window.set_font_size(size)

    def set_text_base(self, base):
        """设置基础文字内容"""
        if "{rate}" in base:
            self.floating_window.text_base = base
            self.floating_window.update_heart_rate()
            self.floating_window._up_set("text_base", base)
        else:
            self.text_edit.setText(self.floating_window.text_base)
            copybut = QMessageBox.Yes
            QMessageBox.warning(self, "警告", "请使用 {rate} 来表示心率", copybut | QMessageBox.Default)

    def set_padding(self, padding):
        """设置背景内边距"""
        self.floating_window.set_padding(padding)

    def set_bg_opacity(self, value):
        """设置背景透明度"""
        self.floating_window.set_bg_opacity(value,self.save_opacity)
        self.save_opacity = False

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.save_opacity = True # 保存浮窗透明度

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
        pixmap.loadFromData(heartratepng.image)
        self.app_icon = QIcon(pixmap)

        layout = QVBoxLayout()
        
        settings_group = QGroupBox("软件设置")
        settings_layout = QVBoxLayout()
        
        # 托盘图标设置
        tray_layout = QHBoxLayout()
        self.tray_check = QCheckBox("启用托盘图标")
        self.tray_check.setChecked(self._get_set("tray_icon", True, bool))
        self.tray_check.stateChanged.connect(self.toggle_tray_icon)
        tray_layout.addWidget(self.tray_check)
        
        settings_layout.addLayout(tray_layout)
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