__version__ = "1.1.0"
import logging
import os
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

logger.info(f'运行程序 -{__version__} -{__file__}')

try:
    import asyncio
    import sys
    import datetime
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QListWidget, QWidget, QTextEdit, QLineEdit,
        QSpinBox, QMessageBox, QCheckBox, QGroupBox, QFileDialog,
        QSystemTrayIcon, QMenu, QSlider, QColorDialog, QFontDialog)
    from PyQt5.QtCore import QTimer, Qt, QPoint, QSize
    from PyQt5.QtGui import QColor, QIcon, QFont
    from qasync import QEventLoop, asyncSlot

    from Blegetheartbeat import BLEHeartRateMonitor
except  ModuleNotFoundError as e:
    logger.error(f"缺少依赖包 {e.name}")

class FloatingHeartRateWindow(QWidget):
    """浮动心率显示窗口"""
    def __init__(self, parent=None):
        logger.info("初始化浮动心率显示窗口")
        try:
            super().__init__(parent)
            self.text_color = QColor(218, 63, 63)
            self.text_base = "心率: {rate}"
            self.bg_color = QColor(0, 0, 0)
            self.bg_opacity = 50  # 默认透明度
            self.font_size = 30  # 默认字体大小
            self.padding = 10  # 默认内边距
            self.setup_ui()
            logger.info("初始化完成")
        except Exception as e:
            logger.error("初始化失败: {}".format(e))

    def setup_ui(self):
        self.setWindowTitle("实时心率")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.heart_rate_label = QLabel(self.text_base.format(rate= "--"))
        self.heart_rate_label.setAlignment(Qt.AlignCenter)
        self.update_style()

        layout.addWidget(self.heart_rate_label)

        # 窗口拖动功能
        self.old_pos = self.pos()
        self.dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def update_heart_rate(self, rate):
        """更新心率显示"""
        self.heart_rate_label.setText(self.text_base.format(rate=rate))

        mc = 200
        
        # 根据心率值改变背景颜色
        if not isinstance(rate, int):
            self.bg_color = QColor(0, 0, 0)
        elif rate < 40:
            self.bg_color = QColor(0, 0, mc)
        elif rate < 55:
            rate_qz = (rate - 40)/15
            grean = int(mc * rate_qz)
            self.bg_color = QColor(0, grean, mc)
        elif rate < 70:
            rate_qz = 1- (rate - 55)/15
            blue = int(mc * rate_qz)
            self.bg_color = QColor(0, mc, blue)
        elif rate < 90:
            self.bg_color = QColor(0, mc, 0)
        elif rate < 105:
            rate_qz = (rate - 90)/15
            red = int(mc * rate_qz)
            self.bg_color = QColor(red, mc, 0)  # 红色
        elif rate < 120:
            rate_qz = 1 - (rate - 105)/15
            grean = int(mc * rate_qz)
            self.bg_color = QColor(mc, grean, 0)
        elif rate >= 120: 
            self.bg_color = QColor(255, 0, 0)

        self.update_style()

    def update_style(self):
        """更新样式表"""
        self.heart_rate_label.setStyleSheet(f"""
            QLabel {{
                font-size: {self.font_size}px; 
                font-weight: bold;
                color: rgba({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()}, 255);
                background-color: rgba({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()}, {self.bg_opacity});
                border-radius: 10px;
                padding: {self.padding}px;
            }}
        """)
        self.adjustSize()  # 调整窗口大小以适应新样式

    def set_text_color(self, color: QColor):
        """设置文字颜色"""
        self.text_color = color
        self.update_style()

    def set_bg_opacity(self, opacity: int):
        """设置背景透明度"""
        self.bg_opacity = opacity
        self.update_style()

    def set_font_size(self, size):
        """设置字体大小"""
        self.font_size = size
        self.update_style()

    def set_padding(self, padding):
        """设置内边距"""
        self.padding = padding
        self.update_style()

class HeartRateMonitorGUI(QMainWindow):
    def __init__(self):
        logger.info("初始化GUI")
        try:
            super().__init__()
            self.quit_setstadus = True
            self.ble_monitor = BLEHeartRateMonitor()
            self.ble_monitor.heart_rate_callback = self.on_heart_rate_update
            self.floating_window = FloatingHeartRateWindow()
            self.tray_icon = None
            self.linking = False
            self.noscanerror_win = False
            self.setup_ui()
            self.setup_tray_icon()
            QTimer.singleShot(500, lambda: self.scan_devices())
        except Exception as e:
            logger.error(f"GUI 初始化错误: {e}")

    def setup_ui(self):
        """设置GUI界面"""
        self.setWindowTitle(f"心率监测设置 -[{__version__}]")
        self.setGeometry(100, 100, 800, 600)

        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 左侧布局（设备管理和连接控制）
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, stretch=2)

        # 设备扫描区域
        scan_group = QGroupBox("设备管理")
        scan_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.scan_devices)

        arf_layout = QHBoxLayout()
        auto_refresh_Label = QLabel("自动刷新")
        self.auto_refresh_button = QCheckBox()
        self.auto_refresh_button.stateChanged.connect(self.auto_scan)
        self.auto_refresh_button.setChecked(True)
        arf_layout.addWidget(auto_refresh_Label)
        arf_layout.addWidget(self.auto_refresh_button)

        # 过滤无名设备
        fe_layout = QHBoxLayout()
        filter_empty_Label = QLabel("过滤无名设备")
        self.filter_empty_button = QCheckBox()
        self.filter_empty_button.stateChanged.connect(self.filter_empty)
        self.filter_empty_button.setChecked(True)
        fe_layout.addWidget(filter_empty_Label)
        fe_layout.addWidget(self.filter_empty_button)

        btn_layout.addWidget(self.refresh_button)
        btn_layout.addLayout(arf_layout)
        btn_layout.addLayout(fe_layout)
        scan_layout.addLayout(btn_layout)

        self.device_list = QListWidget()
        device_textlayout = QHBoxLayout()
        self.device_list_status = QLabel()

        device_textlayout.addWidget(QLabel("可用的BLE设备:"))
        device_textlayout.addWidget(self.device_list_status)
        scan_layout.addLayout(device_textlayout)
        scan_layout.addWidget(self.device_list)

        scan_group.setLayout(scan_layout)
        left_layout.addWidget(scan_group)

        # 连接控制区域
        control_group = QGroupBox("连接设置")
        control_layout = QVBoxLayout()

        duration_layout = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 86400)  # 0-24小时
        self.duration_spin.setValue(0)  # 0表示不自动断开
        self.duration_spin.setSuffix("秒 (0=持续连接)")

        duration_layout.addWidget(QLabel("自动断开时间:"))
        duration_layout.addWidget(self.duration_spin)
        control_layout.addLayout(duration_layout)

        btn_layout = QHBoxLayout()
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button = QPushButton("断开连接")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.disconnect_button.setEnabled(False)

        btn_layout.addWidget(self.connect_button)
        btn_layout.addWidget(self.disconnect_button)
        control_layout.addLayout(btn_layout)

        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)

        # 数据显示区域
        data_group = QGroupBox("心率数据记录")
        data_layout = QVBoxLayout()

        self.heart_rate_display = QTextEdit()
        self.heart_rate_display.setReadOnly(True)
        data_layout.addWidget(self.heart_rate_display)

        # 数据保存按钮
        self.save_button = QPushButton("保存数据到文件")
        self.save_button.clicked.connect(self.save_data)
        data_layout.addWidget(self.save_button)

        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)

        # 右侧布局（浮动窗口设置）
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, stretch=1)

        # 浮动窗口设置区域
        float_group = QGroupBox("浮动窗口设置")
        float_layout = QVBoxLayout()

        # 显示控制
        display_layout = QHBoxLayout()
        self.float_window_check = QCheckBox("显示浮动窗口")
        self.float_window_check.setChecked(True)
        self.float_window_check.stateChanged.connect(self.toggle_floating_window)

        self.click_through_check = QCheckBox("鼠标穿透")
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

        # 托盘图标设置
        tray_layout = QHBoxLayout()
        self.tray_check = QCheckBox("启用托盘图标")
        self.tray_check.setChecked(True)
        self.tray_check.stateChanged.connect(self.toggle_tray_icon)

        tray_layout.addWidget(self.tray_check)
        tray_layout.addStretch()
        float_layout.addLayout(tray_layout)

        float_group.setLayout(float_layout)
        right_layout.addWidget(float_group)

        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.status_label)

        # 定时器用于更新UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # 每秒更新一次

        # 显示浮动窗口
        self.floating_window.show()

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            if os.path.exists("heart-rate.png"):
                self.tray_icon.setIcon(QIcon("heart-rate.png"))
            else:
                # 默认图标
                self.tray_icon.setIcon(QIcon())
                logger.warning("未找到图标文件，将使用默认图标。")

            tray_menu = QMenu()

            # 添加菜单项
            show_settings_action = tray_menu.addAction("打开设置")
            show_settings_action.triggered.connect(self.show_settings)

            toggle_float_action = tray_menu.addAction("关闭浮窗")
            toggle_float_action.triggered.connect(self.toggle_float_window_via_tray)

            tray_menu.addSeparator()

            quit_action = tray_menu.addAction("退出程序")
            quit_action.triggered.connect(self.quit_application)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def show_settings(self):
        """显示设置窗口"""
        self.show()
        self.activateWindow()  # 激活窗口使其获得焦点

    def toggle_float_window_via_tray(self):
        """通过托盘菜单切换浮动窗口"""
        action = self.sender()
        if self.floating_window.isVisible():
            self.floating_window.hide()
            action.setText("显示浮窗")
        else:
            self.floating_window.show()
            action.setText("关闭浮窗")

    def quit_application(self):
        """退出应用程序"""
        if self.ble_monitor.client and self.ble_monitor.client.is_connected:
            reply = QMessageBox.question(
                self, '确认',
                "当前已连接设备，确定要退出吗?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.close_application()
        else:
            self.close_application()

    def close_application(self):
        """执行退出程序的操作"""
        if self.tray_icon:
            self.tray_icon.hide()
        self.floating_window.close()
        QApplication.quit()

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
            else:
                self.tray_icon.hide()

    def toggle_floating_window(self, state):
        """切换浮动窗口显示"""
        if state == Qt.Checked:
            self.floating_window.show()
        else:
            self.floating_window.hide()

    def toggle_click_through(self, state):
        """切换鼠标穿透"""
        if state == Qt.Checked:
            self.floating_window.setWindowFlags(
                self.floating_window.windowFlags() | 
                Qt.WindowTransparentForInput
            )
        else:
            self.floating_window.setWindowFlags(
                self.floating_window.windowFlags() & 
                ~Qt.WindowTransparentForInput
            )
        self.floating_window.show()

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
        else:
            self.text_edit.setText(self.floating_window.text_base)
            copybut = QMessageBox.Yes
            QMessageBox.warning(self, "警告", "请使用 {rate} 来表示心率", copybut | QMessageBox.Default)

    def set_padding(self, padding):
        """设置背景内边距"""
        self.floating_window.set_padding(padding)

    def set_bg_opacity(self, value):
        """设置背景透明度"""
        self.floating_window.set_bg_opacity(value)

    def save_data(self):
        """保存心率数据到文件"""
        if not self.ble_monitor.heart_rate_data:
            QMessageBox.warning(self, "警告", "没有可保存的数据")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存心率数据", "", "CSV文件 (*.csv);;所有文件 (*)")

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("时间,心率(BPM)\n")
                    for timestamp, hr in self.ble_monitor.heart_rate_data:
                        f.write(f"{timestamp},{hr}\n")
                QMessageBox.information(self, "成功", "数据已保存")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败: {str(e)}")

    def update_ui(self):
        """更新UI状态"""
        if (self.ble_monitor.client and self.ble_monitor.client.is_connected) or self.linking:
            self.quit_setstadus = False
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
        else:
            if self.quit_setstadus == False:
                self.status_label.setText("链接被断开")
                self.floating_window.update_heart_rate("--")
                self.quit_setstadus = True
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)

    def on_heart_rate_update(self, timestamp, heart_rate):
        """心率数据更新回调"""
        # 更新浮动窗口
        self.floating_window.update_heart_rate(heart_rate)
        
        # 更新数据显示区域
        self.heart_rate_display.append(f"[{timestamp}] 心率: {heart_rate} BPM")

    def filter_empty(self, state):
            self.ble_monitor.filter_empty = state

    @asyncSlot()
    async def scan_devices(self):
        """扫描BLE设备"""
        self.device_list_status.setText("正在扫描设备...")

        try:
            devices = await self.ble_monitor.scan_devices()

            self.device_list.clear()
            
            for device in devices:
                self.device_list.addItem(f"{device.name} ({device.address})")

            self.device_list_status.setText(f"找到 {len(devices)} 个设备")
            self.noscanerror_win = False
        except WindowsError as e:
            print(e.winerror)
            if e.winerror == -2147020577:
                self.device_list_status.setText("请打开蓝牙")
                logger.debug("蓝牙未开启")
                errortxt = "蓝牙未开启，请打开蓝牙"
            else:
                self.device_list_status.setText(f"未知错误: {e.winerror}")
                errortxt = f"-{e.strerror} [{e.winerror}] "
                logger.error(f"窗口错误: {errortxt}")

            if not self.noscanerror_win:
                QMessageBox.warning(self, "错误", errortxt)
                self.noscanerror_win = True

        except Exception as e:
            self.device_list_status.setText(f"扫描错误: {str(e)}")
            logger.error(f"扫描BLE设备错误: {e}")

    def auto_scan(self, state):
        """启停自动扫描设备"""
        if not hasattr(self, "scan_timer"):
            self.scan_timer = QTimer()
            self.scan_timer.timeout.connect(self.scan_devices)

        if state:
            self.scan_timer.start(5000)
        else:
            self.scan_timer.stop()

    @asyncSlot()
    async def connect_device(self):
        """连接选定的设备"""
        selected_item = self.device_list.currentItem()
        if not selected_item:
            self.status_label.setText("请先选择设备")
            return

        device_info = selected_item.text()
        findL = device_info.find("(")
        device_address = device_info[ findL+1 : device_info.find(")") ]
        device_name = device_info[:findL]

        self.status_label.setText(f"正在连接 {device_name}...")
        logger.info(f"尝试连接 {device_info}")

        try:
            self.linking = True
            success = await self.ble_monitor.connect_device(device_address)
            if success:
                self.status_label.setText(f"已连接 {device_name}")
                self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已连接到设备")

                # 设置自动断开定时器（如果设置了时间）
                duration = self.duration_spin.value()
                logger.info(f"已连接到 {device_name}, 设置自动断开时间 {duration} 秒(0表示不自动断开)")
                if duration > 0:
                    QTimer.singleShot(duration * 1000, lambda: asyncio.create_task(self.disconnect_device()))

        except Exception as e:
            self.status_label.setText(f"连接错误: {str(e)}")
            self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 连接失败: {str(e)}")
            logger.error(f"连接错误: {e}")
        self.linking = False

    @asyncSlot()
    async def disconnect_device(self):
        """断开当前连接"""
        try:
            self.disconnect_button.setEnabled(False)
            success = await self.ble_monitor.disconnect_device()
            if success:
                self.quit_setstadus = True
                self.status_label.setText("已断开连接")
                self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已断开连接")
                logger.info("已断开连接")

                # 显示收集的数据摘要
                stats = self.ble_monitor.get_heart_rate_stats()
                if stats:
                    self.heart_rate_display.append(
                        f"\n心率统计:\n"
                        f"最低: {stats['min']} BPM\n"
                        f"最高: {stats['max']} BPM\n"
                        f"平均: {stats['avg']:.1f} BPM\n"
                        f"共记录 {stats['count']} 条数据"
                    )

        except Exception as e:
            self.status_label.setText(f"断开连接错误: {str(e)}")
            logger.error(f"断开连接错误: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.tray_icon and self.tray_icon.isVisible():
            # 如果启用了托盘图标，则隐藏窗口而不是退出
            self.hide()
            event.ignore()
        else:
            # 否则正常退出
            if self.ble_monitor.client and self.ble_monitor.client.is_connected:
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

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        # 设置异步事件循环
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        window = HeartRateMonitorGUI()
        window.show()

        with loop:
            loop.run_forever()
    except Exception as e:
        logger.error(f"未标识的异常：{e}")
        window.close_application()
        sys.exit(1)