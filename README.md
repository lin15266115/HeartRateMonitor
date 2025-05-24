### 效果展示：
[![视频](https://i1.hdslb.com/bfs/archive/3b60eb45c7b24938e62cdd3f3bc28e56ff5d8e2c.jpg@308w_174h)](https://www.bilibili.com/video/BV1VsEbzeE1N)

### 项目仓库：
[github](https://github.com/lin15266115/HeartRateMonitor)
[gitcode](https://gitcode.com/lin15266115/HeartBeat)

## 运行程序

**方法1**: 使用代码运行 -<u>**下载zip** 解压后根据python环境修改 [start.bat](start.bat) 后再双击 [start.bat](start.bat) 即可运行</u>

**方法2**: 使用exe程序运行 -<u>下载已经编译好的程序, 点击 *HeartRateMonitor.exe* 运行</u>

如果[方法1]直接运行出现安装依赖相关错误，可以通过命令行手动安装依赖库：

    pip install pyqt5
    pip install qasync
    pip install bleak

注: 推荐使用python3.12运行程序

## Q&A
1. 我的设备支持蓝牙且已经打开蓝牙, 运行程序时却扫描不到任何设备
	- 请检查手环是否开启心跳广播, 如果开启后仍然找不到, 可以尝试在点进系统的蓝牙设置页面后, 再尝试点击本程序设备处的刷新按钮

2. 暂时还没有更多
