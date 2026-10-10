# -*- coding: utf-8 -*-
"""
fym_protocol.py —— 上位机与 CC2530 之间的串口应用层协议

必须与开发板固件 FymUART.c 完全一致：
    串口参数 : 19200 8-N-1  （由 CC2530 U0GCR=9 / U0BAUD=59 决定，勿改）
    指令(PC -> 板) : '1' 开灯(YLED)   '0' 关灯(YLED)
                     '2' 开灯2(BLED)  '3' 关灯2(BLED)
    回传(板 -> PC) : led on / led off / led2 on / led2 off / unknown
                     每行以 \\r\\n 结束
"""

# ---- 串口参数（与固件一致，来源：CC2530 UART0 初始化代码）----
BAUDRATE = 19200
BYTESIZE = 8
STOPBITS = 1
PARITY = "N"

# ---- 指令 ----
CMD_LED_ON = b"1"
CMD_LED_OFF = b"0"
CMD_LED2_ON = b"2"
CMD_LED2_OFF = b"3"

# ---- 指令 -> 期望回传（用于界面提示与自检）----
COMMAND_LABEL = {
    CMD_LED_ON: "开灯",
    CMD_LED_OFF: "关灯",
    CMD_LED2_ON: "开灯2",
    CMD_LED2_OFF: "关灯2",
}
EXPECTED_REPLY = {
    CMD_LED_ON: "led on",
    CMD_LED_OFF: "led off",
    CMD_LED2_ON: "led2 on",
    CMD_LED2_OFF: "led2 off",
}


def normalize_reply(raw: bytes) -> str:
    """把开发板回传的原始字节规整成可读字符串（去掉首尾空白与换行）。"""
    if isinstance(raw, (bytes, bytearray)):
        text = raw.decode("utf-8", "ignore")
    else:
        text = str(raw)
    return text.strip()
