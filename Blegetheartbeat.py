from typing import List, Optional, Dict
import datetime
from bleak import BleakScanner, BleakClient

from importlib.metadata import version
# 心率服务UUID
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
# 心率测量特征UUID
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

if tuple(map(int,version("bleak").split('.'))) < (1, 0, 0):
    async def check_service(client: BleakClient):
        services = await client.get_services()
        return HEART_RATE_SERVICE_UUID in [ser.uuid for ser in services]
else:
    async def check_service(client: BleakClient):
        return any(ser.uuid == HEART_RATE_SERVICE_UUID for ser in client.services)

class BLEHeartRateMonitor:
    """BLE连接和心率数据处理类"""
    def __init__(self):
        self.client = None
        self.devices = []
        self.heart_rate_data = []
        self.heart_rate_callback = None

        self.filter_empty: bool = True

    async def scan_devices(self, timeout: float = 5.0) -> List:
        """
        扫描BLE设备

        Args:
            timeout: 扫描超时时间(秒)

        Returns:
            发现的设备列表
        """
        self.devices = await BleakScanner.discover()
        # 过滤掉名称为None的设备
        return [d for d in self.devices if d.name is not None] if self.filter_empty else self.devices

    async def connect_device(self, device_address: str) -> tuple[bool, str]:
        """
        连接设备

        Args:
            device_address: 要连接的设备地址

        Returns:
            连接是否成功
        """
        self.client = BleakClient(device_address)
        await self.client.connect()
        if await check_service(self.client):
            # 启用心率通知
            await self.client.start_notify(
                HEART_RATE_MEASUREMENT_UUID,
                self._notification_handler
            )
            return True, "已连接 {device_address}"
        else:
            await self.disconnect_device()
            return False, "{device_address} 不是支持心率服务的设备"

    async def disconnect_device(self):
        """断开设备连接"""
        if self.client and self.client.is_connected:
            await self.client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
            await self.client.disconnect()
            return True
        return False

    def _notification_handler(self, sender: str, data: bytearray):
        """
        处理心率通知数据
        
        Args:
            sender: 特征UUID
            data: 接收到的原始数据
        """
        heart_rate = self._parse_heart_rate(data)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 保存数据
        self.heart_rate_data.append((timestamp, heart_rate))

        # 调用回调函数通知UI更新
        if self.heart_rate_callback:
            self.heart_rate_callback(timestamp, heart_rate)

    def _parse_heart_rate(self, data: bytearray) -> int:
        """
        解析心率数据

        Args:
            data: 原始心率数据

        Returns:
            解析出的心率值
        """
        flags = data[0]
        heart_rate_value_format = (flags & 0x01) == 0x01

        if heart_rate_value_format:
            heart_rate = int.from_bytes(data[1:3], byteorder='little')
        else:
            heart_rate = int(data[1])

        return heart_rate

    def get_heart_rate_stats(self) -> Optional[Dict[str, float]]:
        """
        获取心率统计数据

        Returns:
            包含最小值、最大值、平均值和数据点数量的字典，如果没有数据则返回None
        """
        if not self.heart_rate_data:
            return None

        hrs = [hr for _, hr in self.heart_rate_data]
        return {
            'min': min(hrs),
            'max': max(hrs),
            'avg': round(sum(hrs) / len(hrs), 1),
            'count': len(hrs)
        }
