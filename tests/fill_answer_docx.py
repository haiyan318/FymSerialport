# -*- coding: utf-8 -*-
"""
fill_answer_docx.py —— 向任务书 docx 的两处作答区「仅添加」答案文字与核心代码。

原则：
  * 只新增段落、只往空段落里写内容，绝不删除任何原有文字、图片与段落。
  * 作答文字统一为黑色字体（任务书明确要求「字体颜色为黑色」）。
  * 优先使用作答区下方已有的空段落，不够时才新建段落。
"""
import copy
import os

from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "雨课堂提交", "2410120085_范一鸣_创新项目第_4-5_周任务.docx")

BLACK = RGBColor(0, 0, 0)
CN_FONT = "宋体"


# ---------------------------------------------------------------- 工具
def _style_run(run, kind):
    """按 kind 设置字体：正文/标题用宋体，代码用等宽字体；一律黑色。"""
    run.font.color.rgb = BLACK
    if kind == "code":
        run.font.name = "Consolas"
        run.font.size = Pt(9)
    else:
        run.font.name = CN_FONT
        run.font.size = Pt(10.5)
    run.font.bold = (kind == "head")
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:eastAsia"), CN_FONT)      # 中文字体
    rFonts.set(qn("w:ascii"), "Consolas" if kind == "code" else CN_FONT)
    rFonts.set(qn("w:hAnsi"), "Consolas" if kind == "code" else CN_FONT)


def _clear(p):
    for r in list(p.runs):
        r._r.getparent().remove(r._r)


def _write(p, text, kind):
    _clear(p)
    run = p.add_run(text if text else " ")      # 空行保留一个空格以维持行高
    _style_run(run, kind)
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0 if kind == "code" else 3)
    pf.line_spacing = 1.0


def _insert_after(prev):
    new_p = copy.deepcopy(prev._p)
    prev._p.addnext(new_p)
    return Paragraph(new_p, prev._parent)


def fill(anchor, blanks, lines):
    """在 anchor 段落之后依次写入 lines；优先复用 blanks 里的空段落。"""
    prev = anchor
    for i, (text, kind) in enumerate(lines):
        p = blanks[i] if i < len(blanks) else _insert_after(prev)
        _write(p, text, kind)
        prev = p
    return prev


# ---------------------------------------------------------------- 内容
TASK1 = [
    ("（1）下载、编译、烧写并运行，说明其实现的功能", "head"),
    ("已下载群文件“CC2530UART控制”源码。在 IAR Embedded Workbench for 8051 中打开该工程（芯片选择 CC2530），"
     "Rebuild All 生成 .hex 文件，再用 IAR 的 Download and Debug（或 SmartRF Flash Programmer）烧写到开发板并运行；"
     "连接时注意把 S10、S1 拨到正确位置（见教材 3.5 节）。", "text"),
    ("该程序实现的功能：初始化 CC2530 的 UART0（波特率 19200、8 位数据位、1 位停止位、无校验，TX=P0_2、RX=P0_3），"
     "在主循环中周期性调用 Uart_Send_String() 向串口调试助手发送字符串，实现“开发板 → PC”的单向串口发送，"
     "即图2中（3）所指方向；同时对开发板上的 LED（P1_0、P1_1）进行控制。", "text"),

    ("（2）UART 控制原理与 Uart_Send_String() 的方向", "head"),
    ("UART 是异步串行通信，收发双方必须约定完全相同的波特率、数据位、停止位和校验位，否则收到的是乱码。"
     "CC2530 的 USART0 关键配置如下：", "text"),
    (r"PERCFG = 0x00;              // USART0 使用备用位置1：TX=P0_2, RX=P0_3", "code"),
    (r"P0SEL  = 0x0C;              // 把 P0_2、P0_3 配置为外设功能", "code"),
    (r"U0CSR |= 0x80;              // 选择 UART 工作模式（非 SPI）", "code"),
    (r"U0GCR |= 9; U0BAUD |= 59;   // 32MHz 系统时钟下波特率为 19200", "code"),
    (r"U0CSR |= 0x40;              // 允许接收（RE=1）", "code"),
    ("下载的源码只实现了发送方向：Uart_Send_String() 把字符串逐字节写入发送寄存器 U0DBUF，再查询发送完成标志 UTX0IF "
     "等待该字节发完，方向是“开发板 → PC”，对应图2中（3）。原程序既没有开启接收中断，也没有接收函数，"
     "因此无法收到 PC 发来的任何指令，不能形成回路。", "text"),

    ("（3）增加 Uart_Receive_String() 函数，实现“PC → 开发板”", "head"),
    ("在原源码基础上新增接收方向（图2中（2））：开启 UART0 接收中断，在中断服务程序里把收到的字符存入缓冲区，"
     "主循环调用 Uart_Receive_String() 解析指令、控制 LED，并把执行结果回传给串口调试助手。关键代码：", "text"),
    (r"#define YLED  P1_0      // 黄灯 D2，低电平点亮", "code"),
    (r"#define BLED  P1_1      // 蓝灯 D1", "code"),
    ("", "code"),
    (r"uchar          RxBuf[16];", "code"),
    (r"volatile uchar RxIndex  = 0;    // 缓冲区写指针", "code"),
    (r"volatile uchar CmdReady = 0;    // 一条指令接收完成标志", "code"),
    ("", "code"),
    (r"/* UART0 接收中断：每收到一个字节触发一次 */", "code"),
    (r"#pragma vector = URX0_VECTOR", "code"),
    (r"__interrupt void UART0_RX_ISR(void)", "code"),
    (r"{", "code"),
    (r"    uchar ch;", "code"),
    (r"    URX0IF = 0;                  // 清接收中断标志", "code"),
    (r"    ch = U0DBUF;                 // 读走接收到的字节", "code"),
    (r"    if((ch=='\n')||(ch=='\r')||(ch=='\0')) {", "code"),
    (r"        if(RxIndex > 0) CmdReady = 1;        // 一行结束", "code"),
    (r"    } else {", "code"),
    (r"        if(RxIndex < 15) RxBuf[RxIndex++] = ch;", "code"),
    (r"        if((ch=='1')||(ch=='0')||(ch=='2')||(ch=='3'))", "code"),
    (r"            CmdReady = 1;        // 单个指令字符即时触发", "code"),
    (r"    }", "code"),
    (r"}", "code"),
    ("", "code"),
    (r"/* 解析并执行指令，再把结果回传给 PC */", "code"),
    (r"void Uart_Receive_String(void)", "code"),
    (r"{", "code"),
    (r"    uchar cmd;", "code"),
    (r"    if(CmdReady == 0) return;    // 没有新指令则直接返回", "code"),
    (r"    cmd = RxBuf[0];              // 取首字符作为指令", "code"),
    (r"    switch(cmd) {", "code"),
    (r"      case '1': YLED = 0; Uart_Send_String(msgLedOn, strlen(msgLedOn)); break;", "code"),
    (r"      case '0': YLED = 1; Uart_Send_String(msgLedOff, strlen(msgLedOff)); break;", "code"),
    (r"      case '2': BLED = 0; Uart_Send_String(msgLed2On, strlen(msgLed2On)); break;", "code"),
    (r"      case '3': BLED = 1; Uart_Send_String(msgLed2Off, strlen(msgLed2Off)); break;", "code"),
    (r"      default : Uart_Send_String(msgUnknown, strlen(msgUnknown)); break;", "code"),
    (r"    }", "code"),
    (r"    RxIndex = 0; CmdReady = 0;   // 清空缓冲，准备接收下一条指令", "code"),
    (r"}", "code"),
    ("", "code"),
    ("其中 msgLedOn、msgLedOff、msgLed2On、msgLed2Off、msgUnknown 分别是字符串 “led on\\r\\n”、“led off\\r\\n”、"
     "“led2 on\\r\\n”、“led2 off\\r\\n”、“unknown\\r\\n”。此外，需在 initUART0() 中开启接收中断："
     "IEN0 |= 0x84;（即开总中断 EA 与 UART0 接收中断 URX0IE），否则收不到 PC 发来的数据。", "text"),
    ("验证现象（串口调试助手设为 19200、8 位数据位、1 位停止位、无校验，且不要勾选“十六进制发送”）：", "text"),
    ("· 发送 1 → 开发板 D2 灯亮，串口调试助手收到 “led on”；", "text"),
    ("· 发送 0 → 开发板 D2 灯灭，串口调试助手收到 “led off”；", "text"),
    ("· 发送 2 / 3 → 控制 D1 灯亮 / 灭，分别收到 “led2 on” / “led2 off”；", "text"),
    ("· 发送其它字符 → 收到 “unknown”；复位开发板还会收到开机提示 “CC2530 UART ready”。", "text"),

    ("（4）图2中（2）（3）的回路实现与源码提交", "head"),
    ("（2）PC → 开发板：串口调试助手发送 '1' / '0' 等指令 → CC2530 的 URX0 接收中断把字符存入 RxBuf → "
     "主循环调用 Uart_Receive_String() 解析指令并控制 LED。", "text"),
    ("（3）开发板 → PC：Uart_Receive_String() 执行完动作后，立即调用原有的 Uart_Send_String() 把 “led on” / "
     "“led off” 等结果回传给串口调试助手显示。", "text"),
    ("两个方向一收一发，构成完整闭环：开发板由原来“只发不收”变成可交互控制，灯的状态变化与文本回显一一对应，"
     "即图2中（2）（3）的信息回路已打通。", "text"),
    ("源码文件夹已按要求命名为 FymUART（XXX = Fym，为本人姓名“范一鸣”拼音 FanYiming 的首字母缩写），"
     "内含 FymUART.c 及 IAR 工程文件（FymUART.eww / .ewp / .ewd / settings），已打包为 FymUART.zip 上传雨课堂，"
     "并在本地保存备份，供后期整体打包提交与后续开发继续使用。", "text"),
]

TASK2 = [
    ("（1）再次熟悉 SerialPort 的属性", "head"),
    ("第二周任务使用的是 C# 的 SerialPort 类；本任务我用 Python 的 pyserial（serial.Serial 对象）实现上位机，"
     "两者的核心属性一一对应。与开发板通信前必须保证这些参数与 CC2530 固件完全一致，否则收到的是乱码：", "text"),
    (r"port      —— 串口号，如 COM5（任务要求不写死，运行时自动枚举）", "code"),
    (r"baudrate  —— 波特率，本任务取 19200（与固件 U0GCR=9、U0BAUD=59 一致）", "code"),
    (r"bytesize  —— 数据位 8", "code"),
    (r"stopbits  —— 停止位 1", "code"),
    (r"parity    —— 校验位 N（无校验）", "code"),
    (r"timeout   —— 读超时，本程序设为 0.5 秒", "code"),
    ("此外，C# 中的 DataReceived 事件在本程序里用“后台线程循环调用 readline()”实现，作用相同："
     "收到一行就交给界面显示，且不会因为等待串口数据而卡住界面。", "text"),

    ("（2）自动获取连接的串口，串口号不写死", "head"),
    ("程序启动时以及点击“刷新”按钮时，调用 serial.tools.list_ports.comports() 枚举本机全部串口，"
     "把设备名填入界面下拉框，由用户选择后再打开；串口号没有写死在代码里。核心代码：", "text"),
    (r"import serial, serial.tools.list_ports", "code"),
    ("", "code"),
    (r"def list_ports():", "code"),
    (r"    '''枚举本机全部串口设备名，如 ['COM3', 'COM5']'''", "code"),
    (r"    return [p.device for p in serial.tools.list_ports.comports()]", "code"),
    ("", "code"),
    (r"def auto_detect_port():          # 自动选择第一个可用串口", "code"),
    (r"    ports = list_ports()", "code"),
    (r"    return ports[0] if ports else None", "code"),
    ("", "code"),
    (r"class LedSerialClient:", "code"),
    (r"    def open(self, port=None):   # port 为空时自动检测", "code"),
    (r"        target = port or self.port or auto_detect_port()", "code"),
    (r"        self.ser = serial.Serial(port=target, baudrate=self.baudrate,", "code"),
    (r"                                 bytesize=8, stopbits=1, parity='N',", "code"),
    (r"                                 timeout=self.timeout)", "code"),
    (r"        return target            # 返回实际使用的串口号", "code"),
    ("界面上的“串口”下拉框与“刷新”按钮即对应此功能；拔插开发板后点“刷新”就能看到新增或消失的串口号。"
     "若一个串口都没有检测到，界面会提示“未检测到串口（请连接开发板并确认驱动已安装）”。", "text"),

    ("（3）用界面上的开/关灯按钮控制开发板上的灯", "head"),
    ("任务1 的固件不需要改动——它已经具备“收指令、控灯、回传”的能力。本阶段要做的，是把“人在串口调试助手里手敲指令、"
     "肉眼看回显”换成程序自动完成：按钮一按就发送，收到回传自动解析并显示。关键代码：", "text"),
    (r"# ---- 与固件 FymUART.c 严格一致的协议 ----", "code"),
    (r"BAUDRATE = 19200;  BYTESIZE = 8;  STOPBITS = 1;  PARITY = 'N'", "code"),
    (r"CMD_LED_ON,  CMD_LED_OFF  = b'1', b'0'      # 控制 D2 灯", "code"),
    (r"CMD_LED2_ON, CMD_LED2_OFF = b'2', b'3'      # 控制 D1 灯", "code"),
    ("", "code"),
    (r"# ---- 按钮绑定：点击即发送指令 ----", "code"),
    (r"self.btn_on.clicked.connect(lambda: self.send(CMD_LED_ON))", "code"),
    (r"self.btn_off.clicked.connect(lambda: self.send(CMD_LED_OFF))", "code"),
    ("", "code"),
    (r"def send(self, cmd: bytes):", "code"),
    (r"    if not self.client.is_open():", "code"),
    (r"        QMessageBox.information(self, '提示', '请先打开串口！'); return", "code"),
    (r"    self.client.send_command(cmd)     # 等价于在串口助手里手动发送", "code"),
    ("", "code"),
    (r"# ---- 后台线程接收回传，避免界面卡死 ----", "code"),
    (r"class SerialReadThread(QThread):", "code"),
    (r"    recv_signal = pyqtSignal(str)", "code"),
    (r"    def run(self):", "code"),
    (r"        while self.running:", "code"),
    (r"            text = self.client.read_reply()   # 读一行，如 'led on'", "code"),
    (r"            if text:", "code"),
    (r"                self.recv_signal.emit(text)   # 交给界面显示", "code"),
    ("", "code"),
    ("这并不是“简单的替代”：串口助手依赖人工输入与人工观察，而本程序把发送、接收、解析、显示全部自动化，"
     "并把协议常量（19200 8-N-1、'1'/'0'、led on / led off）集中放在 fym_protocol.py 中，与固件 FymUART.c 一一对应，"
     "后期要扩展温湿度等其它交互信息时只需改这一处。", "text"),
    ("运行效果：在下拉框选择串口 → 点击“打开串口”（日志显示“已打开串口 COMx @ 19200 8-N-1”）→ 点击“开灯”，"
     "开发板 D2 灯亮，界面日志显示“设备回复：led on”；点击“关灯”，D2 灯灭，显示“设备回复：led off”；"
     "“开灯2 / 关灯2”以 '2' / '3' 控制 D1 灯，回传 “led2 on” / “led2 off”。此时开发板复位，"
     "界面还会收到上电提示 “CC2530 UART ready”，说明双向链路正常。", "text"),
    ("源码文件夹已按要求命名为 FymSerialport（XXX = Fym），已打包为 FymSerialport.zip 上传雨课堂，"
     "并在本地保存备份。本人已知悉本节任务需要现场演示并记录成绩，演示内容为：打开上位机 → 自动枚举并选择串口 → "
     "点击开灯/关灯按钮 → 开发板上的灯随之亮灭，且界面同步显示开发板回传的信息。", "text"),
]


# ---------------------------------------------------------------- 主流程
def main():
    d = Document(DOC)
    ps = d.paragraphs

    def find(exact):
        hits = [i for i, p in enumerate(ps) if p.text.strip() == exact]
        if not hits:
            raise SystemExit("未找到锚点段落：" + exact)
        return hits

    a1 = find("在此处作答，字体颜色为黑色：")[0]      # 任务1 作答区
    a2 = find("在此处作答，字体颜色为黑色：")[1]      # 任务2 作答区

    # 锚点之后连续的空段落，作为可复用的空位
    def blanks_after(anchor_idx, stop_text):
        out, i = [], anchor_idx + 1
        while i < len(ps) and ps[i].text.strip() == "":
            out.append(ps[i]); i += 1
        return out

    b1 = blanks_after(a1, "对应任务2")
    b2 = blanks_after(a2, None)

    print("任务1 锚点 idx=%s，可复用空段落 %d 个" % (a1, len(b1)))
    print("任务2 锚点 idx=%s，可复用空段落 %d 个" % (a2, len(b2)))

    fill(ps[a1], b1, TASK1)
    # 因插入后索引会变，重新定位第二个锚点
    ps2 = d.paragraphs
    a2_new = [i for i, p in enumerate(ps2) if p.text.strip() == "在此处作答，字体颜色为黑色："][1]
    b2_new = blanks_after(a2_new, None)
    fill(ps2[a2_new], b2_new, TASK2)

    d.save(DOC)
    print("已写入并保存：", DOC)


if __name__ == "__main__":
    main()
