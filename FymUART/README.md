# FymUART —— 第4-5周 任务1（CC2530 UART 收发 + LED 控制）

## 1. 工程路径
```
D:\code_local\SmartHealthyLife\project_py\FymSerialport\FymUART\
├── FymUART.c          ← 完整固件源码（本次改造产物）
├── FymUART.ewp        ← IAR 工程
├── FymUART.ewd / .eww ← 调试/工作区配置
├── settings\          ← 调试器与断点配置
└── Debug\             ← 编译输出（Exe\FymUART.hex、Obj、List）
```

## 2. 编译工具链与命令
* 工具链：**IAR Embedded Workbench for 8051**（EW8051，支持 CC2530 的 8051 内核），
  编译器 `icc8051.exe`，链接器 `xlink.exe`（由 IAR 自动调用）。
* 命令行编译（无需打开 IDE）：
  ```bat
  "C:\Program Files (x86)\IAR Systems\Embedded Workbench 8.10\common\bin\IarBuild.exe" ^
      FymUART.ewp -build Debug
  ```
* 图形界面编译：打开 `FymUART.eww` → 选中工程 → **Project → Rebuild All**。
* 输出：`Debug\Exe\FymUART.hex`（Intel HEX）与 `FymUART.d51`（调试用）。

> 本机未安装 IAR，故未实际产出 .hex；源码已用 gcc + 桩寄存器完成“离机”逻辑验证
> （见 `..\tests\fw_sim\`）。真实固件需在装有 EW8051 的机器上编译。

## 3. 烧录工具与命令
* 硬件：CC2530 开发板 + **CC Debugger**（USB），插入板卡调试口。
* 方式一（推荐，IDE 内）：IAR → **Project → Download and Debug (Ctrl+D)** → 工具栏 **Go**。
* 方式二（命令行，需 CC Debugger 驱动）：
  ```bat
  "C:\Program Files (x86)\Texas Instruments\SmartRF Tools\Flash Programmer\bin\SmartRFProg.exe" ^
      -target CC2530
  ```
  图形版 **SmartRF Flash Programmer v1**：System-on-Chip 选 `CC2530`，
  Flash image 选 `Debug\Exe\FymUART.hex`，勾选 *Erase, program and verify* → Perform actions。
* 接线跳线：**S10 / S1 拨到正确位置**（见教材 3.5 节，具体档位以实验指导书为准）。

## 4. 串口通信参数（均来自 FymUART.c，非臆测）
| 项目 | 取值 | 代码依据 |
|---|---|---|
| 外设 | UART0 | `U0CSR |= 0x80` |
| 引脚 | TX = P0_2，RX = P0_3（备用位置1） | `PERCFG=0x00; P0SEL=0x0C` |
| 波特率 | **19200** | `U0GCR=9; U0BAUD=59`（32MHz） |
| 数据位 | 8 | 默认 |
| 停止位 | 1 | 默认 |
| 校验 | 无 (None) | `U0UCR` 复位默认 0x00 |
| 流控 | 无 | — |
| 端口号 | 由 USB 转串口枚举决定（如 COM3） | 系统枚举 |

PC 端接线：开发板 TX(P0_2) → PC 串口 RX；开发板 RX(P0_3) → PC 串口 TX；GND 共地。

## 5. 收发指令示例
| PC → 开发板 | 开发板现象 | 开发板 → PC 回传 |
|---|---|---|
| `1` | YLED(P1_0/D2) 亮 | `led on` |
| `0` | YLED(P1_0/D2) 灭 | `led off` |
| `2` | BLED(P1_1/D1) 亮 | `led2 on` |
| `3` | BLED(P1_1/D1) 灭 | `led2 off` |
| 其它 | 无动作 | `unknown` |

上电后开发板主动发送一行：`CC2530 UART ready`。
