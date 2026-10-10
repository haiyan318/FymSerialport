# -*- coding: utf-8 -*-
"""
device_sim.py —— 开发板模拟器（无硬件联调用）

在与上位机配对的另一个串口上运行，模拟 FymUART 固件的应答协议：
    收到 '1' -> 回 "led on"   收到 '0' -> 回 "led off"
    收到 '2' -> 回 "led2 on"  收到 '3' -> 回 "led2 off"
    其它     -> 回 "unknown"

用法（需先具备一对虚拟串口，如 com0com 的 COM10<->COM11）：
    开发板模拟器：  python device_sim.py COM11
    上位机界面  ：  选择 COM10 打开，即可完整体验收发回路
"""
import sys
import time

import serial

import fym_protocol as P

REPLY = {
    b"1": "led on",
    b"0": "led off",
    b"2": "led2 on",
    b"3": "led2 off",
}


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else None
    if not port:
        print("用法: python device_sim.py <串口号>  (如 COM11)")
        return 1

    ser = serial.Serial(port=port, baudrate=P.BAUDRATE, bytesize=P.BYTESIZE,
                        stopbits=P.STOPBITS, parity=P.PARITY, timeout=0.2)
    print(f"[device_sim] 已打开 {port} @ {P.BAUDRATE} 8-{P.PARITY}-{P.STOPBITS}，等待指令...")
    # 上电提示，与固件 main() 一致
    ser.write("CC2530 UART ready\r\n".encode())
    try:
        while True:
            ch = ser.read(1)
            if not ch:
                time.sleep(0.02)
                continue
            if ch in (b"\r", b"\n", b"\x00"):
                continue
            reply = REPLY.get(ch, "unknown")
            ser.write((reply + "\r\n").encode())
            print(f"[device_sim] 收到 {ch!r} -> 回传 {reply!r}")
    except KeyboardInterrupt:
        print("\n[device_sim] 退出")
    finally:
        ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
