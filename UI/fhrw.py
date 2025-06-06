from .importpyqt import QWidget, QColor, Qt, QVBoxLayout, QLabel, QPoint
from config_manager import logger, try_except, ups, gs, update_settings
__all__ = ["FloatingHeartRateWindow"]

class FloatingHeartRateWindow(QWidget):
    """浮动心率显示窗口"""
    @try_except("浮窗初始化失败")
    def __init__(self, parent=None, ICON=None):
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
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = QPoint(event.globalPos() - self.old_pos)
            x = self.x() + delta.x()
            y = self.y() + delta.y()
            self.move(
                 x if -10 < x else -10
                ,y if -10 < y else -10
                )
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self._up_xy()

    def update_heart_rate(self, rate=None):
        """更新心率显示"""
        self.heart_rate_label.setText(self.text_base.format(rate=rate if rate else '--'))

        mc = self.bg_brightness
        
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

    def set_bg_opacity(self, opacity = None, update_setting = True):
        """设置背景透明度"""
        self.bg_opacity = opacity or self.bg_opacity
        if update_setting:
            self._up_set('bg_opacity', opacity)
        self.update_style()

    def set_bg_brightness(self, brightness = None, update_setting = True):
        """设置背景亮度"""
        self.bg_brightness = brightness or self.bg_brightness
        if update_setting:
            self._up_set('bg_brightness', brightness)
        self.update_style()

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

    def _get_set(self, option: str, default, type_ = None):
        return gs('FloatingWindow', option, default, type_, "浮窗")

    def _up_set(self, option: str, value):
        ups('FloatingWindow', option, value, "浮窗")

    def _up_xy(self):
        update_settings(FloatingWindow={'x': self.x(), 'y': self.y()})