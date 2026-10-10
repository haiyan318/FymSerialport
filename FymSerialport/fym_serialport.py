# -*- coding: utf-8 -*-
"""
fym_serialport.py —— 第4-5周 任务2 上位机（XXXSerialport）

功能：甩掉串口调试助手，用本界面控制开发板 LED：
  * 自动枚举/刷新本机串口，串口号不写死
  * 选择串口 + 波特率(默认19200，与固件一致)后打开
  * 点击“开灯/关灯”按钮发送 '1'/'0'，异步接收开发板回传并显示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QComboBox,
                             QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QLabel, QMessageBox, QGroupBox)
from PyQt5.QtCore import QThread, pyqtSignal

import fym_protocol as P
from fym_client import LedSerialClient, list_ports

# ----------------------------------------------------------------------
# 界面字体：仅调整字号并统一应用到整个程序（不改动任何布局结构）
#   原程序未设置字体，使用系统默认字号（Windows 下约 9pt，其它平台可能为 12pt）。
#   UI_FONT_POINT_SIZE 为期望字号，数值可按需修改；实际应用时会保证
#   相对当前默认字号确实变大（见 apply_ui_font）。
# ----------------------------------------------------------------------
UI_FONT_POINT_SIZE = 14


class SerialReadThread(QThread):
    """后台线程：循环读取开发板回传，避免界面卡死。"""
    recv_signal = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        while self.running:
            try:
                text = self.client.read_reply()
                if text:
                    self.recv_signal.emit(text)
            except Exception:
                # 串口关闭/拔插时忽略异常，由界面逻辑处理
                pass

    def stop_thread(self):
        self.running = False
        self.wait(1000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FymSerialport —— CC2530 灯控上位机（第4-5周 任务2）")
        self.resize(560, 480)
        self.client = LedSerialClient()
        self.read_thread = None
        self._build_ui()
        self.refresh_port()

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- 连接区 ---
        box_conn = QGroupBox("串口连接")
        conn = QVBoxLayout(box_conn)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("串口："))
        self.combo_port = QComboBox()
        row1.addWidget(self.combo_port, 1)
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_port)
        row1.addWidget(self.btn_refresh)
        conn.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("波特率："))
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["19200", "115200", "9600", "38400", "57600"])
        self.combo_baud.setCurrentText(str(P.BAUDRATE))  # 默认 19200
        row2.addWidget(self.combo_baud)
        self.btn_open = QPushButton("打开串口")
        self.btn_open.clicked.connect(self.on_open_close)
        row2.addWidget(self.btn_open, 1)
        conn.addLayout(row2)
        layout.addWidget(box_conn)

        # --- 控制区 ---
        box_ctrl = QGroupBox("灯控制")
        ctrl = QHBoxLayout(box_ctrl)
        self.btn_on = QPushButton("开灯 (发送 '1')")
        self.btn_on.clicked.connect(lambda: self.send(P.CMD_LED_ON))
        self.btn_off = QPushButton("关灯 (发送 '0')")
        self.btn_off.clicked.connect(lambda: self.send(P.CMD_LED_OFF))
        self.btn_on2 = QPushButton("开灯2 ('2')")
        self.btn_on2.clicked.connect(lambda: self.send(P.CMD_LED2_ON))
        self.btn_off2 = QPushButton("关灯2 ('3')")
        self.btn_off2.clicked.connect(lambda: self.send(P.CMD_LED2_OFF))
        for b in (self.btn_on, self.btn_off, self.btn_on2, self.btn_off2):
            ctrl.addWidget(b)
        layout.addWidget(box_ctrl)

        # --- 日志区 ---
        layout.addWidget(QLabel("接收信息 / 运行日志："))
        self.text_recv = QTextEdit()
        self.text_recv.setReadOnly(True)
        layout.addWidget(self.text_recv, 1)

    # ------------------------------------------------------------------
    def refresh_port(self):
        self.combo_port.clear()
        ports = list_ports()
        if ports:
            self.combo_port.addItems(ports)
            self.log(f"检测到串口：{', '.join(ports)}")
        else:
            self.log("未检测到串口（请连接开发板并确认驱动已安装）")

    def on_open_close(self):
        if self.client.is_open():
            self.close_serial()
        else:
            self.open_serial()

    def open_serial(self):
        port = self.combo_port.currentText().strip()
        baud = int(self.combo_baud.currentText())
        try:
            # 注意：波特率必须在 open() 之前设置，pyserial 是在打开时生效的
            self.client.baudrate = baud
            used = self.client.open(port or None)
            self.btn_open.setText("关闭串口")
            self.log(f"已打开串口 {used} @ {baud} 8-{P.PARITY}-{P.STOPBITS}")
            self.read_thread = SerialReadThread(self.client)
            self.read_thread.recv_signal.connect(self.on_reply)
            self.read_thread.start()
        except Exception as e:
            self.log(f"打开失败：{e}")
            QMessageBox.warning(self, "打开失败", str(e))

    def close_serial(self):
        if self.read_thread:
            self.read_thread.stop_thread()
            self.read_thread = None
        self.client.close()
        self.btn_open.setText("打开串口")
        self.log("串口已关闭")

    def send(self, cmd: bytes):
        if not self.client.is_open():
            QMessageBox.information(self, "提示", "请先打开串口！")
            return
        try:
            self.client.send_command(cmd)
            self.log(f"已发送指令：{cmd.decode()}  ({P.COMMAND_LABEL.get(cmd, '')})")
        except Exception as e:
            self.log(f"发送失败：{e}")

    def on_reply(self, text):
        self.log(f"设备回复：{text}")

    def log(self, msg):
        self.text_recv.append(msg)

    def closeEvent(self, event):
        self.close_serial()
        event.accept()


def apply_ui_font(app):
    """把界面字号统一调大：沿用当前字体族与其它属性，仅修改字号。

    实际字号 = max(UI_FONT_POINT_SIZE, 当前默认字号 + 2)，
    以保证在任何平台/DPI 下都确实比默认更大。
    """
    font = app.font()
    base = font.pointSize()
    size = UI_FONT_POINT_SIZE
    if base > 0:
        size = max(size, base + 2)
    font.setPointSize(size)
    app.setFont(font)
    return app.font()


def main():
    app = QApplication(sys.argv)
    apply_ui_font(app)          # 在建窗口前设置，所有控件随之放大
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
