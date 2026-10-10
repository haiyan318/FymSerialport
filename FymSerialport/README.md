# FymSerialport —— 第4-5周 任务2（上位机控制开发板 LED）

## 文件
| 文件 | 说明 |
|---|---|
| `fym_protocol.py` | 应用层协议常量（19200 8N1、指令、回传），**与固件 FymUART.c 唯一对齐点** |
| `fym_client.py` | 与界面无关的串口客户端，`port=None` 自动枚举串口；可注入模拟串口便于测试 |
| `fym_serialport.py` | PyQt5 图形界面（入口） |
| `device_sim.py` | 开发板模拟器，无硬件时配合虚拟串口做联调 |
| `requirements.txt` | 依赖：pyserial、PyQt5 |
| `run.bat` | 用 docgui 环境启动界面 |

## 运行（docgui 环境，不新建/切换其它环境）
```bat
D:\apps\anaconda3\envs\docgui\python.exe fym_serialport.py
:: 或双击 run.bat
```
依赖安装（docgui）：
```bat
D:\apps\anaconda3\envs\docgui\python.exe -m pip install -r requirements.txt
```

## 使用
1. 连接开发板与 USB 转串口线，点【刷新】自动枚举串口（串口号不写死）。
2. 波特率保持 **19200**（与固件一致），点【打开串口】。
3. 点【开灯】发送 `'1'`、【关灯】发送 `'0'`；板卡回传 `led on/led off` 显示在下方日志区。

## 无硬件联调
有虚拟串口对（com0com 的 COM10<->COM11）时：
```bat
:: 终端A：模拟开发板
D:\apps\anaconda3\envs\docgui\python.exe device_sim.py COM11
:: 终端B：界面选 COM10 打开即可
D:\apps\anaconda3\envs\docgui\python.exe fym_serialport.py
```

## 自测
```bat
set QT_QPA_PLATFORM=offscreen
D:\apps\anaconda3\envs\docgui\python.exe ..\tests\test_serialport.py
```
