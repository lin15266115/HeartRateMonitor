from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout, QCheckBox, QPushButton, QSpinBox, QLineEdit, QColorDialog, QMessageBox
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor
from .basicwidgets import *
from config_manager import logger, try_except, ups, gs, update_settings
__all__ = ["FloatingHeartRateWindow", "FloatingWindowSettingUI"]

class FloatingHeartRateWindow(QWidget):
    """浮动心率显示窗口"""
    @try_except("浮窗初始化失败")
    def __init__(self, parent=None, ICON=None):
        """初始化浮动窗口"""
        logger.info("初始化浮动心率显示窗口")
        super().__init__(parent)

        self.text_color = QColor(self._get_set("text_color", 4292502628, int))
        self.text_base = self._get_set('text_base', "心率: {rate}", str)
        self.bg_color = QColor(0, 0, 0)
        self.bg_opacity = self._get_set('bg_opacity', 50, int)
        self.font_size = self._get_set('font_size', 30, int)
        self.padding = self._get_set('padding', 10, int)
        self.bg_brightness = self._get_set('bg_brightness', 200, int)
        self.register_as_window = self._get_set('register_as_window', False, bool)

        self.setup_ui()
        if ICON:
            self.setWindowIcon(ICON)
        x = self._get_set('x', "default")
        y = self._get_set('y', "default")
        if not (x == "default" or y == "default"):
            self.move(*[int(i) for i in [x, y]]) # 化简为繁是吧
        logger.info("浮窗初始化完成")

    def setup_ui(self):
        """设置UI布局和组件"""
        self.setWindowTitle("实时心率")
        self.update_window_flags()
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

    def update_window_flags(self):
        """更新窗口标志"""
        if self.register_as_window:
            # 注册为常规窗口，OBS可以捕获
            self.setWindowFlags(
                 Qt.WindowStaysOnTopHint 
                |Qt.FramelessWindowHint 
                |Qt.WindowTitleHint
            )
        else:
            # 默认的浮动窗口模式
            self.setWindowFlags(
                 Qt.WindowStaysOnTopHint 
                |Qt.FramelessWindowHint 
                |Qt.Tool
            )

    def set_register_as_window(self, enabled):
        """设置是否注册为常规窗口"""
        self.register_as_window = enabled
        self._up_set('register_as_window', enabled)
        self.update_window_flags()
        self.show()  # 重新显示以应用新标志

    def mousePressEvent(self, event):
        """鼠标按下事件，开始拖动窗口"""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        """鼠标移动事件，处理窗口拖动"""
        if self.dragging:
            delta = QPoint(event.globalPos() - self.old_pos)
            x = self.x() + delta.x()
            y = self.y() + delta.y()
            # 限制窗口不会移出屏幕太远
            self.move(
                 x if -10 < x else -10
                ,y if -10 < y else -10
                )
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件，结束拖动并保存位置"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self._up_xy()

    def update_heart_rate(self, rate=None):
        """更新心率显示"""
        if (rate or -1) < 0:
            rate = None
        self.heart_rate_label.setText(self.text_base.format(rate=rate if rate else '--'))
        
        maxc = self.bg_brightness
        
        # 根据心率值动态改变背景颜色(使用HSB)
        if not isinstance(rate, int):
            self.bg_color = QColor.fromHsv(0, 0, 0)  # 黑色
        elif rate < 40:
            self.bg_color = QColor.fromHsv(240, 255, maxc)  # 蓝色
        elif rate < 55:
            hue = 240 - int((rate - 40) * (60/15))  # 从蓝色(240)过渡到青色(180)
            self.bg_color = QColor.fromHsv(hue, 255, maxc)
        elif rate < 70:
            hue = 180 - int((rate - 55) * (60/15))  # 从青色(180)过渡到绿色(120)
            self.bg_color = QColor.fromHsv(hue, 255, maxc)
        elif rate < 90:
            self.bg_color = QColor.fromHsv(120, 255, maxc)  # 绿色
        elif rate < 105:
            hue = 120 - int((rate - 90) * (60/15))  # 从绿色(120)过渡到黄色(60)
            self.bg_color = QColor.fromHsv(hue, 255, maxc)
        elif rate < 120:
            hue = 60 - int((rate - 105) * (60/15))  # 从黄色(60)过渡到红色(0)
            self.bg_color = QColor.fromHsv(hue, 255, maxc)
        elif rate >= 120:
            self.bg_color = QColor.fromHsv(0, 255, maxc)
    
            self.update_style()

        self.update_style()

    def update_style(self):
        """更新UI样式表"""
        style = f"""
            QLabel {{
                font-size: {self.font_size}px;
                font-weight: bold;
                color: rgba({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()}, 255);
                background-color: rgba({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()}, {self.bg_opacity});
                border-radius: 10px;
                padding: {self.padding}px;
            }}
        """
        self.heart_rate_label.setStyleSheet(style)
        self.adjustSize()  # 调整窗口大小以适应新样式

    def set_text_color(self, color: QColor):
        """设置文字颜色"""
        self.text_color = color
        self._up_set('text_color', color.rgb())
        self.update_style()

    def set_bg_opacity(self, opacity=None, update_setting=True):
        """设置背景透明度"""
        self.bg_opacity = opacity or self.bg_opacity
        if update_setting:
            self._up_set('bg_opacity', self.bg_opacity)
            self.update_heart_rate()
        else:
            self.update_heart_rate(105)

    def set_bg_brightness(self, brightness=None, update_setting=True):
        """设置背景亮度"""
        self.bg_brightness = brightness or self.bg_brightness
        if update_setting:
            self._up_set('bg_brightness', self.bg_brightness)
            self.update_heart_rate()
        else:
            self.update_heart_rate(105)

    def set_font_size(self, size):
        """设置字体大小"""
        self.font_size = size
        self._up_set('font-size', size)
        self.update_style()

    def set_padding(self, padding):
        """设置内边距"""
        self.padding = padding
        self._up_set('padding', padding)
        self.update_style()

    def _get_set(self, option: str, default, type_=None):
        """获取设置项"""
        return gs('FloatingWindow', option, default, type_, "浮窗")

    def _up_set(self, option: str, value):
        """更新设置项"""
        ups('FloatingWindow', option, value, "浮窗")

    def _up_xy(self):
        update_settings(FloatingWindow={'x': self.x(), 'y': self.y()})
        
class FloatingWindowSettingUI(QWidget):
    """浮动窗口设置界面类"""
    
    @try_except("浮动窗口设置界面初始化")
    def __init__(self):
        super().__init__()
        self.floating_window = FloatingHeartRateWindow()  # 创建浮动窗口实例
        self.save_ = {"bg_opacity": False, "bg_brightness": False}
        self.setup_ui()

    def setup_ui(self):
        """初始化设置界面UI"""
        layout = QVBoxLayout()

        # 浮动窗口设置分组框
        float_group = QGroupBox("浮动窗口设置")
        float_layout = QVBoxLayout()

        # 显示控制区域
        display_layout = QHBoxLayout()

        fwindow_canlook = self.floating_window._get_set('canlook', True, bool)
        CheackBox_("显示浮动窗口", display_layout, fwindow_canlook, self.toggle_floating_window)

        lock = self.floating_window._get_set('lock', False, bool)
        CheackBox_("鼠标穿透", display_layout, lock, self.toggle_click_through)

        float_layout.addLayout(display_layout)

        # 文字颜色设置区域
        color_layout = QHBoxLayout()
        self.text_color_button = QPushButton("文字颜色")
        self.text_color_button.clicked.connect(self.set_text_color)

        # 颜色预览标签
        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(20, 20)
        self.text_color_preview.setStyleSheet(f"background-color: {self.floating_window.text_color.name()}; border: 1px solid black;")

        color_layout.addWidget(QLabel("文字颜色:"))
        color_layout.addWidget(self.text_color_button)
        color_layout.addWidget(self.text_color_preview)
        color_layout.addStretch()
        float_layout.addLayout(color_layout)

        # 字体大小设置区域
        font_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 100)
        self.font_size_spin.setValue(self.floating_window.font_size)
        self.font_size_spin.valueChanged.connect(self.set_font_size)

        font_layout.addWidget(QLabel("字体大小:"))
        font_layout.addWidget(self.font_size_spin)
        float_layout.addLayout(font_layout)

        # 文字内容设置区域
        text_layout = QHBoxLayout()
        self.text_edit = QLineEdit()
        self.text_edit.setText(self.floating_window.text_base)
        self.text_edit.textChanged.connect(self.set_text_base)
        text_layout.addWidget(QLabel("文字内容:"))
        text_layout.addWidget(self.text_edit)
        float_layout.addLayout(text_layout)

        # 背景内边距设置区域
        padding_layout = QHBoxLayout()
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 100)
        self.padding_spin.setValue(self.floating_window.padding)
        self.padding_spin.valueChanged.connect(self.set_padding)

        padding_layout.addWidget(QLabel("背景内边距:"))
        padding_layout.addWidget(self.padding_spin)
        float_layout.addLayout(padding_layout)

        # 背景透明度设置区域
        opacity_layout = QHBoxLayout()
        bgop = self.floating_window.bg_opacity
        self.opacity_slider = Slider_(bgop, self.set_bg_opacity)

        opacity_layout.addWidget(QLabel("背景透明度:"))
        opacity_layout.addWidget(self.opacity_slider)
        float_layout.addLayout(opacity_layout)

        # 背景亮度设置区域
        brightness_layout = QHBoxLayout()
        bg_brightness = self.floating_window.bg_brightness
        self.brightness_slider = Slider_(bg_brightness, self.set_bg_brightness)

        brightness_layout.addWidget(QLabel("背景亮度:"))
        brightness_layout.addWidget(self.brightness_slider)
        float_layout.addLayout(brightness_layout)

        # 注册为常规窗口选项
        register_layout = QHBoxLayout()
        self.register_window_check = QCheckBox("注册为常规窗口(OBS捕获)")
        register_window_check_state = self.floating_window._get_set('register_as_window', False, bool)
        self.register_window_check.setChecked(register_window_check_state)
        self.register_window_check.stateChanged.connect(self.toggle_register_as_window)
        register_layout.addWidget(self.register_window_check)
        float_layout.addLayout(register_layout)

        # 完成布局设置
        float_group.setLayout(float_layout)
        layout.addWidget(float_group)
        self.setLayout(layout)

        # 根据初始设置显示或隐藏浮动窗口
        if fwindow_canlook:
            self.floating_window.show()
        else:
            self.floating_window.hide()
            
        # 根据初始设置启用或禁用鼠标穿透
        if lock:
            self.toggle_click_through(Qt.Checked)

    def update_heart_rate(self, heart_rate=None):
        """更新心率显示"""
        self.floating_window.update_heart_rate(heart_rate)

    def toggle_floating_window(self, state):
        """切换浮动窗口显示状态"""
        if state == Qt.Checked:
            self.floating_window.show()
            self.floating_window._up_set('canlook', True)
        else:
            self.floating_window.hide()
            self.floating_window._up_set('canlook', False)

    def toggle_click_through(self, state):
        """切换鼠标穿透状态"""
        if state == Qt.Checked:
            # 启用鼠标穿透
            self.floating_window.setWindowFlags(
                self.floating_window.windowFlags() | 
                Qt.WindowTransparentForInput
            )
            self.floating_window._up_set('lock', True)
        else:
            # 禁用鼠标穿透
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
        """打开颜色对话框设置文字颜色"""
        color = QColorDialog.getColor(self.floating_window.text_color, self)
        if color.isValid():
            self.floating_window.set_text_color(color)
            self.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

    def set_font_size(self, size):
        """设置字体大小"""
        self.floating_window.set_font_size(size)

    def set_text_base(self, base):
        """设置基础文字模板"""
        if "{rate}" in base:
            # 验证模板是否包含心率占位符
            self.floating_window.text_base = base
            self.floating_window.update_heart_rate()
            self.floating_window._up_set("text_base", base)
        else:
            # 无效模板，恢复原值并显示警告
            self.text_edit.setText(self.floating_window.text_base)
            copybut = QMessageBox.Yes
            QMessageBox.warning(self, "警告", "请使用 {rate} 来表示心率", copybut | QMessageBox.Default)

    def set_padding(self, padding):
        """设置内边距"""
        self.floating_window.set_padding(padding)

    def set_bg_opacity(self, value=None, ups_=None):
        """设置背景透明度"""
        self.floating_window.set_bg_opacity(value, ups_)

    def set_bg_brightness(self, value=None, ups_=True):
        """设置背景亮度"""
        self.floating_window.set_bg_brightness(value, ups_)