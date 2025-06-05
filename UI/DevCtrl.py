from .importpyqt import (QWidget, QVBoxLayout, QLabel, pyqtSignal
    ,QGroupBox, QHBoxLayout, QPushButton, QCheckBox, QListWidget
    ,QSpinBox, QTextEdit, QMessageBox, QTimer, QFileDialog)
from config_manager import logger, pip_install_models, try_except
from Blegetheartbeat import BLEHeartRateMonitor

import asyncio
import datetime

def import_qasync():
    global QEventLoop, asyncSlot
    from qasync import QEventLoop, asyncSlot

pip_install_models(import_qasync, "qasync")

class DeviceConnectionUI(QWidget):
    heart_rate_updated = pyqtSignal(int)
    status_changed = pyqtSignal(str)

    def __init__(self, status_label):
        super().__init__()
        self.ble_monitor = BLEHeartRateMonitor()
        self.ble_monitor.heart_rate_callback = self.on_heart_rate_update
        self.status_label = status_label
        self.linking = False
        self.quit_setstadus = True
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

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
        
        layout.addWidget(scan_group)
        layout.addWidget(control_group)
        layout.addWidget(data_group)
        self.setLayout(layout)

        # 定时器用于更新链接信息UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)
    
    def on_heart_rate_update(self, timestamp, heart_rate):
        self.heart_rate_display.append(f"[{timestamp}] 心率: {heart_rate} BPM")
        self.heart_rate_updated.emit(heart_rate)

    
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
            logger.error(f"扫描BLE设备错误: {e}", exc_info=True)

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
        device_address = device_info[findL+1 : device_info.find(")")]
        device_name = device_info[:findL-1]

        self.status_label.setText(f"正在连接 {device_name}...")
        logger.info(f"尝试连接 {device_info}")

        try:
            self.linking = True
            success, rtext = await self.ble_monitor.connect_device(device_address)
            self.status_label.setText(rtext.format(device_address=device_name))
            logger.info(rtext.format(device_address=device_info))
            if success:
                self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已连接到设备")

                # 设置自动断开定时器（如果设置了时间）
                duration = self.duration_spin.value()
                logger.info(f"自动断开时间 {duration} 秒(0表示不自动断开)")
                if duration > 0:
                    QTimer.singleShot(duration * 1000, lambda: asyncio.create_task(self.disconnect_device()))

        except Exception as e:
            self.status_label.setText(f"连接错误: {str(e)}")
            self.heart_rate_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 连接失败: {str(e)}")
            logger.error(f"连接设备时出错: {e}", exc_info=True)
        self.linking = False
    
    def disconnect_error(self, e):
            self.status_label.setText(f"断开连接错误: {str(e)}")

    @asyncSlot()
    @try_except('断开连接错误', disconnect_error)
    async def disconnect_device(self):
        """断开当前连接"""
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
                logger.error(f"保存数据时出错: {str(e)}")

    def update_ui(self):
        """更新UI状态"""
        if (self.ble_monitor.client and self.ble_monitor.client.is_connected) or self.linking:
            self.quit_setstadus = False
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
        else:
            if self.quit_setstadus == False:
                self.status_label.setText("链接被断开")
                self.quit_setstadus = True
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
