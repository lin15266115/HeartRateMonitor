import time
import webbrowser
from urllib import request
from urllib.error import HTTPError
from PyQt5.QtWidgets import (QDialog, QProgressBar, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal

from system_utils import logger, start_update_program, try_except

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self._is_running = True

    def run(self):
        try:
            # 打开URL连接
            with request.urlopen(self.url) as response:
                # 获取文件总大小
                total_size = int(response.getheader('Content-Length', 0))
                downloaded_size = 0

                # 以二进制写入模式打开本地文件
                with open(self.save_path, 'wb') as f:
                    # 每次读取8KB
                    chunk_size = 8192
                    while self._is_running:
                        print(time.time())
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        # 写入文件并更新下载大小
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 计算并发送进度百分比
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_signal.emit(progress)

                if self._is_running:
                    self.finished_signal.emit(True)
                else:
                    self.finished_signal.emit(False)

        except HTTPError as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(False)
            logger.error(f"下载文件时出错: {str(e)}")

        except Exception as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(False)
            logger.error(f"下载失败: {e}", exc_info=True)

    def stop(self):
        self._is_running = False
        self.wait()

class UpdWindow(QDialog):
    url = ""
    gitcodeurl = None
    githuburl = "https://github.com/lin1526615/HeartRateMonitor"
    @try_except("下载窗口初始化")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新版本更新")
        self.setGeometry(100, 100, 400, 150)
        
        # 创建UI元素
        self.url_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("准备下载")

        # 下载管理
        downloadlay = QHBoxLayout()

        self.download_btn = QPushButton("Gitcode源下载")
        downloadlay.addWidget(self.download_btn)
        self.download_btn.clicked.connect(self.start_download)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        downloadlay.addWidget(self.cancel_btn)
        self.cancel_btn.clicked.connect(self.cancel_download)

        # 访问相关网站
        self.website_layout = QHBoxLayout()

        self.website_btn_cc = QPushButton("到GitCode查看")
        self.website_btn_cc.clicked.connect(self.toGitCode)
        self.website_layout.addWidget(self.website_btn_cc)
        self.website_btn_cc.setEnabled(False)

        self.website_btn_ch = QPushButton("到GitHub查看")
        self.website_btn_ch.clicked.connect(self.toGitHub)
        self.website_layout.addWidget(self.website_btn_ch)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addLayout(downloadlay)
        layout.addLayout(self.website_layout)
        
        self.setLayout(layout)

        # 下载线程
        self.download_thread = None

    def set_url(self, url, gitcodeurl = None):
        self.url = url
        self.url_label.setText(f"下载地址: {url}")
        if  gitcodeurl:
            self.gitcodeurl = gitcodeurl
            self.website_btn_cc.setEnabled(True)

    def start_download(self):
        if not self.url:
            self.status_label.setText("错误: 没有设置下载URL")
            return

        logger.info("开始下载文件")

        save_path = "upd.exe"

        self.download_thread = DownloadThread(self.url, save_path)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.start()

        # 更新UI状态
        self.status_label.setText("下载中...")
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def download_finished(self, success):
        if success:
            self.status_label.setText("下载完成!")
            self.download_btn.setText("重启以应用更新")
            self.download_btn.clicked.connect(start_update_program)
            self.cancel_btn.setText("关闭")
            self.cancel_btn.clicked.connect(self.close)
        else:
            self.status_label.setText("下载已取消或失败")
            self.download_btn.setText("重新下载")
        
        self.download_btn.setEnabled(True)
        if self.download_thread:
            self.download_thread.quit()
            self.download_thread.wait()
            self.download_thread = None

    def show_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.status_label.setText("正在取消下载...")
            self.cancel_btn.setEnabled(False)
            self.download_thread.stop()

    def closeEvent(self, event):
        # 窗口关闭时停止下载线程
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait()
        event.accept()

    def toGitCode(self):
        if self.gitcodeurl:
            webbrowser.open(self.gitcodeurl)

    def toGitHub(self):
        webbrowser.open(self.githuburl)