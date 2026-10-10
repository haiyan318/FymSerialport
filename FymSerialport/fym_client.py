# -*- coding: utf-8 -*-
"""
fym_client.py —— 与界面无关的串口通信客户端（可单独测试）

设计要点：
  * 串口号不写死：port=None 时自动枚举本机串口并选择第一个可用口。
  * 通过 serial_factory 注入串口对象，便于在无硬件时用模拟串口做单元测试。
"""
from __future__ import annotations

import serial
import serial.tools.list_ports

import fym_protocol as P


def list_ports():
    """枚举本机全部串口设备名，如 ['COM3', 'COM5']。"""
    return [p.device for p in serial.tools.list_ports.comports()]


def auto_detect_port():
    """自动选择第一个可用串口；无串口时返回 None。"""
    ports = list_ports()
    return ports[0] if ports else None


class LedSerialClient:
    """对 CC2530 开发板 LED 进行控制的上位机通信客户端。"""

    def __init__(self, port=None, baudrate=P.BAUDRATE, timeout=0.5,
                 serial_factory=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._factory = serial_factory or serial.Serial
        self.ser = None

    # ---------- 连接管理 ----------
    def open(self, port=None):
        """打开串口。port 为空时自动检测。返回实际使用的端口名。"""
        target = port or self.port or auto_detect_port()
        if not target:
            raise RuntimeError("未检测到任何可用串口，请检查开发板连接与驱动")
        self.ser = self._factory(
            port=target,
            baudrate=self.baudrate,
            bytesize=P.BYTESIZE,
            stopbits=P.STOPBITS,
            parity=P.PARITY,
            timeout=self.timeout,
        )
        self.port = target
        return target

    def is_open(self):
        if self.ser is None:
            return False
        return bool(getattr(self.ser, "is_open", True))

    def close(self):
        if self.ser is not None and self.is_open():
            self.ser.close()

    # ---------- 收发 ----------
    def send_command(self, cmd: bytes):
        """向开发板发送一条指令。"""
        if not self.is_open():
            raise RuntimeError("串口未打开")
        self.ser.write(cmd)

    def led_on(self):
        self.send_command(P.CMD_LED_ON)

    def led_off(self):
        self.send_command(P.CMD_LED_OFF)

    def led2_on(self):
        self.send_command(P.CMD_LED2_ON)

    def led2_off(self):
        self.send_command(P.CMD_LED2_OFF)

    def read_reply(self):
        """读取一行回传（以 \\n 结束），返回规整后的字符串；无数据返回 ''。"""
        if not self.is_open():
            return ""
        raw = self.ser.readline()
        return P.normalize_reply(raw)
