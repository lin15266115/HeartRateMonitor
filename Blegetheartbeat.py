from bleak import BleakScanner, BleakClient
import datetime

# 心率服务UUID
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
# 心率测量特征UUID
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

class BLEHeartRateMonitor:
    """BLE连接和心率数据处理类"""
    def __init__(self):
        self.client = None
        self.devices = []
        self.heart_rate_data = []
        self.heart_rate_callback = None
        
    async def scan_devices(self):
        """扫描BLE设备"""
        self.devices = await BleakScanner.discover()
        # 过滤掉名称为None的设备
        return [d for d in self.devices if d.name is not None]
    
    async def connect_device(self, device_address):
        """连接设备"""
        self.client = BleakClient(device_address)
        await self.client.connect()
        
        # 启用心率通知
        await self.client.start_notify(
            HEART_RATE_MEASUREMENT_UUID,
            self._notification_handler
        )
        return True
    
    async def disconnect_device(self):
        """断开设备连接"""
        if self.client and self.client.is_connected:
            await self.client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
            await self.client.disconnect()
            return True
        return False
    
    def _notification_handler(self, sender, data):
        """处理心率通知数据"""
        heart_rate = self._parse_heart_rate(data)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存数据
        self.heart_rate_data.append((timestamp, heart_rate))
        
        # 调用回调函数通知UI更新
        if self.heart_rate_callback:
            self.heart_rate_callback(timestamp, heart_rate)
    
    def _parse_heart_rate(self, data):
        """解析心率数据"""
        flags = data[0]
        heart_rate_value_format = (flags & 0x01) == 0x01
        
        if heart_rate_value_format:
            heart_rate = int.from_bytes(data[1:3], byteorder='little')
        else:
            heart_rate = data[1]
            
        return heart_rate
    
    def get_heart_rate_stats(self):
        """获取心率统计数据"""
        if not self.heart_rate_data:
            return None
            
        hrs = [hr for _, hr in self.heart_rate_data]
        return {
            'min': min(hrs),
            'max': max(hrs),
            'avg': sum(hrs) / len(hrs),
            'count': len(hrs)
        }
