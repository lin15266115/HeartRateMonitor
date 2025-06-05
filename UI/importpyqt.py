from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QWidget, QTextEdit, QLineEdit,
    QSpinBox, QMessageBox, QCheckBox, QGroupBox, QFileDialog,
    QSystemTrayIcon, QMenu, QSlider, QColorDialog, QFontDialog)
from PyQt5.QtCore import QTimer, Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QFont, QPixmap

def import_PyQt5():
    return globals()