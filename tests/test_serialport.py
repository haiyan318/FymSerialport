# -*- coding: utf-8 -*-
"""
test_serialport.py —— 任务2 上位机自测（无需真实硬件）

  A. 协议一致性测试   : 指令/回传映射是否与固件 FymUART.c 一致
  B. 客户端收发测试   : 用模拟板卡串口注入 LedSerialClient，验证 开/关灯 收发回路
  C. 界面构建测试     : offscreen 模式构建 PyQt5 主窗口，验证控件与默认波特率

运行（docgui 环境，自动使用 offscreen，不会弹窗）：
    set QT_QPA_PLATFORM=offscreen
    D:\\apps\\anaconda3\\envs\\docgui\\python.exe test_serialport.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(os.path.dirname(HERE), "FymSerialport")
sys.path.insert(0, APP_DIR)

import fym_protocol as P                                   # noqa: E402
from fym_client import LedSerialClient, list_ports          # noqa: E402

FAIL = 0
TOTAL = 0


def check(name, cond):
    global FAIL, TOTAL
    TOTAL += 1
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    if not cond:
        FAIL += 1


class FakeBoardSerial:
    """模拟 CC2530 FymUART 固件的串口对象（字节 -> 回传 与固件一致）。"""

    REPLIES = {b"1": "led on", b"0": "led off",
               b"2": "led2 on", b"3": "led2 off"}

    def __init__(self, **kw):
        self.port = kw.get("port")
        self.baudrate = kw.get("baudrate")
        self.bytesize = kw.get("bytesize")
        self.stopbits = kw.get("stopbits")
        self.parity = kw.get("parity")
        self.timeout = kw.get("timeout")
        self.is_open = True
        self._rx = bytearray()
        self.tx_log = []

    def write(self, data: bytes):
        for b in data:
            c = bytes([b])
            if c in (b"\r", b"\n"):
                continue
            self.tx_log.append(c)
            self._rx += (self.REPLIES.get(c, "unknown") + "\r\n").encode()
        return len(data)

    def readline(self):
        i = self._rx.find(b"\n")
        if i < 0:
            return b""
        line = bytes(self._rx[:i + 1])
        del self._rx[:i + 1]
        return line

    def close(self):
        self.is_open = False


def test_protocol():
    print("A. 协议一致性")
    check("波特率 = 19200 (与固件一致)", P.BAUDRATE == 19200)
    check("数据位/停止位/校验 = 8/1/N", (P.BYTESIZE, P.STOPBITS, P.PARITY) == (8, 1, "N"))
    check("'1' 期望回传 'led on'", P.EXPECTED_REPLY[P.CMD_LED_ON] == "led on")
    check("'0' 期望回传 'led off'", P.EXPECTED_REPLY[P.CMD_LED_OFF] == "led off")
    check("normalize_reply 去换行", P.normalize_reply(b"led on\r\n") == "led on")


def test_client():
    print("B. 客户端收发回路（模拟板卡）")
    holder = {}

    def factory(**kw):
        holder["ser"] = FakeBoardSerial(**kw)
        return holder["ser"]

    client = LedSerialClient(port="FAKE", serial_factory=factory)
    used = client.open()
    check("打开串口返回端口名", used == "FAKE")
    check("串口 is_open", client.is_open())
    check("打开时参数正确(baud=19200,8N1)",
          (holder["ser"].baudrate == 19200 and holder["ser"].bytesize == 8
           and holder["ser"].stopbits == 1 and holder["ser"].parity == "N"))

    client.led_on()
    check("开灯指令回传 'led on'", client.read_reply() == "led on")

    client.led_off()
    check("关灯指令回传 'led off'", client.read_reply() == "led off")

    client.led2_on()
    check("开灯2 回传 'led2 on'", client.read_reply() == "led2 on")

    client.led2_off()
    check("关灯2 回传 'led2 off'", client.read_reply() == "led2 off")

    client.send_command(b"9")
    check("非法指令回传 'unknown'", client.read_reply() == "unknown")

    check("发送日志记录 b'1'/b'0' 等原样字节",
          holder["ser"].tx_log[:2] == [b"1", b"0"])

    client.close()
    check("关闭后 is_open 为 False", not client.is_open())


def test_ports():
    print("C. 串口枚举")
    ports = list_ports()
    check("list_ports 返回列表", isinstance(ports, list))
    print(f"     当前本机串口：{ports if ports else '(无)'}")


def test_gui():
    print("D. 界面构建（offscreen）")
    from PyQt5.QtWidgets import QApplication, QMessageBox
    import fym_serialport

    app = QApplication.instance() or QApplication(sys.argv)

    # 屏蔽模态弹窗（offscreen 下模态框会导致崩溃），只验证逻辑分支
    calls = {"n": 0}
    orig_info = QMessageBox.information

    def fake_info(*a, **k):
        calls["n"] += 1
        return QMessageBox.Ok
    QMessageBox.information = staticmethod(fake_info)

    try:
        win = fym_serialport.MainWindow()
        check("主窗口构建成功", win is not None)
        check("默认波特率为 19200", win.combo_baud.currentText() == "19200")
        check("存在 开灯/关灯 按钮", win.btn_on.text().startswith("开灯")
              and win.btn_off.text().startswith("关灯"))
        # 未打开串口时点击“开灯”：应提示(被拦截)且不崩溃
        win.send(P.CMD_LED_ON)
        check("未打开串口时点击按钮给出提示且不崩溃", calls["n"] == 1)
        # 打开串口(注入模拟板卡)后点击“开灯”，应真正写出发送指令
        from fym_client import LedSerialClient
        holder = {}

        def factory(**kw):
            holder["ser"] = FakeBoardSerial(**kw)
            return holder["ser"]
        win.client = LedSerialClient(port="FAKE", serial_factory=factory)
        win.client.open()
        win.send(P.CMD_LED_ON)
        check("打开串口后点击“开灯”实际发出 b'1'", holder["ser"].tx_log == [b"1"])
        win.close()
    finally:
        QMessageBox.information = orig_info


if __name__ == "__main__":
    print("==== FymSerialport 上位机自测 ====\n")
    test_protocol()
    test_client()
    test_ports()
    test_gui()
    print(f"\n==== 结果: {TOTAL - FAIL}/{TOTAL} 通过 ====")
    sys.exit(0 if FAIL == 0 else 1)
