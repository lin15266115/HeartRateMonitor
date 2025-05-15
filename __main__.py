import asyncio
import sys
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QWidget, QTextEdit,
                             QSpinBox, QMessageBox, QCheckBox, QGroupBox, QFileDialog)
from PyQt5.QtCore import QTimer, Qt, QPoint, QSize
from PyQt5.QtGui import QColor
from qasync import QEventLoop, asyncSlot

# 心率服务UUID
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
# 心率测量特征UUID
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

class FloatingHeartRateWindow(QWidget):
    """浮动心率显示窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.heart_rate_label.setStyleSheet("""
            QLabel {
                font-size: 48px; 
                font-weight: bold;
                color: white;
                background-color: rgba(0, 0, 0, 150);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
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
        
        # 根据心率值改变颜色
        if rate > 100:
            color = QColor(255, 0, 0)  # 红色
        elif rate < 60:
            color = QColor(0, 0, 255)  # 蓝色
        else:
            color = QColor(0, 255, 0)  # 绿色
            
        # 更新样式表
        self.heart_rate_label.setStyleSheet(f"""
            QLabel {{
                font-size: 48px; 
                font-weight: bold;
                color: white;
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 150);
                border-radius: 10px;
                padding: 20px;
            }}
        """)

class HeartRateMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = None
        self.devices = []
        self.heart_rate_data = []
        self.floating_window = FloatingHeartRateWindow()
        self.setup_ui()
        
    def setup_ui(self):
        """设置GUI界面"""
        self.setWindowTitle("心率监测设置")
        self.setGeometry(100, 100, 600, 500)
        
        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
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
        main_layout.addWidget(scan_group)
        
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
        
        # 浮动窗口设置
        float_layout = QHBoxLayout()
        self.float_window_check = QCheckBox("显示浮动窗口")
        self.float_window_check.setChecked(True)
        self.float_window_check.stateChanged.connect(self.toggle_floating_window)
        
        self.click_through_check = QCheckBox("鼠标穿透")
        self.click_through_check.stateChanged.connect(self.toggle_click_through)
        
        float_layout.addWidget(self.float_window_check)
        float_layout.addWidget(self.click_through_check)
        control_layout.addLayout(float_layout)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
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
        main_layout.addWidget(data_group)
        
        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # 定时器用于更新UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 显示浮动窗口
        self.floating_window.show()
    
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
    
    def save_data(self):
        """保存心率数据到文件"""
        if not self.heart_rate_data:
            QMessageBox.warning(self, "警告", "没有可保存的数据")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存心率数据", "", "CSV文件 (*.csv);;所有文件 (*)")
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("时间,心率(BPM)\n")
                    for timestamp, hr in self.heart_rate_data:
                        f.write(f"{timestamp},{hr}\n")
                QMessageBox.information(self, "成功", "数据已保存")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败: {str(e)}")
    
    def update_ui(self):
        """更新UI状态"""
        if self.client and self.client.is_connected:
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.scan_button.setEnabled(False)
        else:
            self.status_label.setText("未连接")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.scan_button.setEnabled(True)
    
    @asyncSlot()
    async def scan_devices(self):
        """扫描BLE设备"""
        self.device_list.clear()
        self.status_label.setText("正在扫描设备...")
        self.scan_button.setEnabled(False)
        
        try:
            self.devices = await BleakScanner.discover()
            # 过滤掉名称为None的设备
            filtered_devices = [d for d in self.devices if d.name is not None]
            
            for device in filtered_devices:
                self.device_list.addItem(f"{device.name} ({device.address})")
            
            self.status_label.setText(f"找到 {len(filtered_devices)} 个设备")
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
            self.client = BleakClient(device_address)
            await self.client.connect()
            
            # 启用心率通知
            await self.client.start_notify(
                HEART_RATE_MEASUREMENT_UUID,
                self.notification_handler
            )
            
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
        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
                await self.client.disconnect()
                self.status_label.setText("已断开连接")
                self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已断开连接")
                
                # 显示收集的数据摘要
                if self.heart_rate_data:
                    min_hr = min(hr for _, hr in self.heart_rate_data)
                    max_hr = max(hr for _, hr in self.heart_rate_data)
                    avg_hr = sum(hr for _, hr in self.heart_rate_data) / len(self.heart_rate_data)
                    self.heart_rate_display.append(
                        f"\n心率统计:\n"
                        f"最低: {min_hr} BPM\n"
                        f"最高: {max_hr} BPM\n"
                        f"平均: {avg_hr:.1f} BPM\n"
                        f"共记录 {len(self.heart_rate_data)} 条数据"
                    )
                
            except Exception as e:
                self.status_label.setText(f"断开连接错误: {str(e)}")
    
    def notification_handler(self, sender, data):
        """处理心率通知数据"""
        heart_rate = self._parse_heart_rate(data)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新UI
        self.floating_window.update_heart_rate(heart_rate)
        self.heart_rate_display.append(f"[{timestamp}] 心率: {heart_rate} BPM")
        
        # 保存数据
        self.heart_rate_data.append((timestamp, heart_rate))
    
    def _parse_heart_rate(self, data):
        """解析心率数据"""
        flags = data[0]
        heart_rate_value_format = (flags & 0x01) == 0x01
        
        if heart_rate_value_format:
            heart_rate = int.from_bytes(data[1:3], byteorder='little')
        else:
            heart_rate = data[1]
            
        return heart_rate
    
    def closeEvent(self, event):
        """窗口关闭时断开连接"""
        if self.client and self.client.is_connected:
            reply = QMessageBox.question(
                self, '确认',
                "当前已连接设备，确定要退出吗?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                asyncio.create_task(self.disconnect_device())
                self.floating_window.close()
                event.accept()
            else:
                event.ignore()
        else:
            self.floating_window.close()
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