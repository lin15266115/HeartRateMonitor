import asyncio
import sys
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QWidget, QTextEdit,
                             QSpinBox, QMessageBox, QCheckBox, QGroupBox, QFileDialog,
                             QSystemTrayIcon, QMenu, QSlider, QColorDialog)
from PyQt5.QtCore import QTimer, Qt, QPoint, QSize
from PyQt5.QtGui import QColor, QIcon
from qasync import QEventLoop, asyncSlot

from Blegetheartbeat import BLEHeartRateMonitor

class FloatingHeartRateWindow(QWidget):
    """浮动心率显示窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_color = QColor(255, 255, 255)  # 默认白色
        self.bg_color = QColor(0, 0, 0)
        self.bg_opacity = 150  # 默认透明度
        self.setup_ui()
        
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
        
        self.heart_rate_label = QLabel("-- BPM")
        self.heart_rate_label.setAlignment(Qt.AlignCenter)
        self.update_style()
        
        layout.addWidget(self.heart_rate_label)
        self.setMinimumSize(QSize(150, 100))
        
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
        self.heart_rate_label.setText(f"{rate} BPM")
        
        # 根据心率值改变背景颜色
        if rate > 100:
            self.bg_color = QColor(255, 0, 0)  # 红色
        elif rate < 60:
            self.bg_color = QColor(0, 0, 255)  # 蓝色
        else:
            self.bg_color = QColor(0, 255, 0)  # 绿色
            
        self.update_style()
    
    def update_style(self):
        """更新样式表"""
        self.heart_rate_label.setStyleSheet(f"""
            QLabel {{
                font-size: 48px; 
                font-weight: bold;
                color: rgba({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()}, 255);
                background-color: rgba({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()}, {self.bg_opacity});
                border-radius: 10px;
                padding: 20px;
            }}
        """)
    
    def set_text_color(self, color):
        """设置文字颜色"""
        self.text_color = color
        self.update_style()
    
    def set_bg_opacity(self, opacity):
        """设置背景透明度"""
        self.bg_opacity = opacity
        self.update_style()

class HeartRateMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ble_monitor = BLEHeartRateMonitor()
        self.ble_monitor.heart_rate_callback = self.on_heart_rate_update
        self.floating_window = FloatingHeartRateWindow()
        self.tray_icon = None
        self.setup_ui()
        self.setup_tray_icon()
        # 修复异步方法调用方式
        QTimer.singleShot(500, lambda: self.scan_devices())  # 直接调用asyncSlot方法，无需create_task
        
    def setup_ui(self):
        """设置GUI界面"""
        self.setWindowTitle("心率监测设置")
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
        self.scan_button = QPushButton("扫描设备")
        self.scan_button.clicked.connect(self.scan_devices)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.scan_devices)
        
        btn_layout.addWidget(self.scan_button)
        btn_layout.addWidget(self.refresh_button)
        scan_layout.addLayout(btn_layout)
        
        self.device_list = QListWidget()
        scan_layout.addWidget(QLabel("可用的BLE设备:"))
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
        self.text_color_preview.setStyleSheet("background-color: white; border: 1px solid black;")
        
        color_layout.addWidget(QLabel("文字颜色:"))
        color_layout.addWidget(self.text_color_button)
        color_layout.addWidget(self.text_color_preview)
        color_layout.addStretch()
        float_layout.addLayout(color_layout)
        
        # 背景透明度设置
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(150)
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
            self.tray_icon.setIcon(QIcon("heart-rate.png"))

            tray_menu = QMenu()
            show_action = tray_menu.addAction("显示主窗口")
            show_action.triggered.connect(self.show)
            quit_action = tray_menu.addAction("退出")
            quit_action.triggered.connect(self.close)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
    
    def on_tray_icon_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
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
        if self.ble_monitor.client and self.ble_monitor.client.is_connected:
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.scan_button.setEnabled(False)
        else:
            self.status_label.setText("未连接")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.scan_button.setEnabled(True)
    
    def on_heart_rate_update(self, timestamp, heart_rate):
        """心率数据更新回调"""
        # 更新浮动窗口
        self.floating_window.update_heart_rate(heart_rate)
        
        # 更新数据显示区域
        self.heart_rate_display.append(f"[{timestamp}] 心率: {heart_rate} BPM")
    
    @asyncSlot()
    async def scan_devices(self):
        """扫描BLE设备"""
        self.device_list.clear()
        self.status_label.setText("正在扫描设备...")
        self.scan_button.setEnabled(False)
        
        try:
            devices = await self.ble_monitor.scan_devices()
            
            for device in devices:
                self.device_list.addItem(f"{device.name} ({device.address})")
            
            self.status_label.setText(f"找到 {len(devices)} 个设备")
        except Exception as e:
            self.status_label.setText(f"扫描错误: {str(e)}")
        finally:
            self.scan_button.setEnabled(True)
    
    @asyncSlot()
    async def connect_device(self):
        """连接选定的设备"""
        selected_item = self.device_list.currentItem()
        if not selected_item:
            self.status_label.setText("请先选择设备")
            return
            
        device_info = selected_item.text()
        device_address = device_info[device_info.find("(")+1:device_info.find(")")]
        
        self.status_label.setText(f"正在连接 {device_info}...")
        
        try:
            success = await self.ble_monitor.connect_device(device_address)
            if success:
                self.status_label.setText(f"已连接 {device_info}")
                self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已连接到设备")
                
                # 设置自动断开定时器（如果设置了时间）
                duration = self.duration_spin.value()
                if duration > 0:
                    QTimer.singleShot(duration * 1000, lambda: asyncio.create_task(self.disconnect_device()))
            
        except Exception as e:
            self.status_label.setText(f"连接错误: {str(e)}")
            self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 连接失败: {str(e)}")
    
    @asyncSlot()
    async def disconnect_device(self):
        """断开当前连接"""
        try:
            success = await self.ble_monitor.disconnect_device()
            if success:
                self.status_label.setText("已断开连接")
                self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已断开连接")
                
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
    
    def closeEvent(self, event):
        """窗口关闭时断开连接"""
        if self.ble_monitor.client and self.ble_monitor.client.is_connected:
            reply = QMessageBox.question(
                self, '确认',
                "当前已连接设备，确定要退出吗?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.disconnect_device()  # 直接调用即可
                self.floating_window.close()
                if self.tray_icon:
                    self.tray_icon.hide()
                event.accept()
            else:
                event.ignore()
        else:
            self.floating_window.close()
            if self.tray_icon:
                self.tray_icon.hide()
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置异步事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = HeartRateMonitorGUI()
    window.show()
    
    with loop:
        loop.run_forever()