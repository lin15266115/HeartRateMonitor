本项目是一个基于 Python 的蓝牙心率监测工具，支持通过 BLE 设备获取心率数据，并提供浮动窗口显示等功能。欢迎提出建议或参与改进！
#### 关于正式应用名称的命名意见征求:
作者希望为这个应用取一个好听的名称, 希望各位看到可以提出宝贵意见, 谢谢!

### 效果展示：
[![视频](https://i1.hdslb.com/bfs/archive/3b60eb45c7b24938e62cdd3f3bc28e56ff5d8e2c.jpg@308w_174h)bilibili视频](https://www.bilibili.com/video/BV1VsEbzeE1N)

### 项目仓库：
[github](https://github.com/lin15266115/HeartRateMonitor) |
[gitee](https://gitee.com/lin_1526615/HeartRateMonitor) |
[gitcode](https://gitcode.com/lin15266115/HeartBeat)

## 运行程序

**方法1**: (推荐)使用代码运行 -<u>**下载zip** 解压后根据python环境修改 [start.bat](start.bat) 后再双击 [start.bat](start.bat) 即可运行</u>
- 优点: 随时可以检查代码中有没有烂活, 可以随时依据自己的需求改代码
- 缺点: 运行环境需要自己配置

**方法2**: (推荐)使用exe程序运行 -<u>下载已经编译好的程序, 点击 *HRMLink.exe* 运行</u>
- 优点: 门槛较低, 单文件双击即可运行
- 缺点: 相对其它方法不太透明, 使用pyinstaller编译的exe程序可能较大

**方法3**: 自行编译运行 -<u>安装pyinstaller后使用[build.bat](build.bat)编译后运行</u> 
- 优点: 可以自行编译最新开发版~~, 不用担心作者偷偷在编译的程序中整烂活~~
- 缺点: 和方法2获得的程序基本一致, 门槛较高

**方法4**: (不推荐)自行编译运行2 -<u>安装nuitka后使用[build2.bat](build2.bat)编译后运行</u>
- 优点: 比较方法3, 编译包体较小, 运行速度较快
- 缺点: 此方法编译的包可能无法运行或功能缺失, 作者不一定会为此更新

如果[方法1]直接运行出现安装依赖相关错误，可以通过命令行手动安装依赖库：

    推荐使用python3.12运行程序

    pip install pyqt5
    pip install qasync
    pip install bleak


## Q&A
1. 我的设备支持蓝牙且已经打开蓝牙, 运行程序时却扫描不到任何设备
	- 请检查手环是否开启心跳广播, 如果开启后仍然找不到, 可以尝试在点进系统的蓝牙设置页面后, 再尝试点击本程序设备处的刷新按钮

2. 暂时还没有更多

## 关于序列帧播放(在写了)
1. ~~在新版本中新增了序列帧播放功能, 但目前任然处于开发测试阶段~~

2. ~~如果要使用序列帧, 请将图片文件放在./animations/test目录下, 注意图片的文件名是以名字排序的, 所以名称应该类似:~~ 
    - ~~01.png, 02.png, 03.png~~
    - ~~abc01.png, abc02.png, abc03.png~~