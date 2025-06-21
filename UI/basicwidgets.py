from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider, QCheckBox, QBoxLayout

class Slider_(QSlider):
    def __init__(self, initial_value, value_changed_callback, Range = (0, 255)):
        super().__init__(Qt.Horizontal)
        self.value_changed_callback = value_changed_callback

        self.setRange(*Range)
        self.setValue(initial_value)

        # 连接信号和槽
        self.valueChanged.connect(
            lambda value: self.value_changed_callback(value, ups_=False)
        )
    
    def mouseReleaseEvent(self, ev):
        self.value_changed_callback(ups_=True)
        return super().mouseReleaseEvent(ev)

class CheackBox_(QCheckBox):
    def __init__(self, text:str, f_layout:QBoxLayout, setC:bool, Ch_slot):
        super().__init__(text)
        self.setChecked(setC)
        self.stateChanged.connect(Ch_slot)
        f_layout.addWidget(self)