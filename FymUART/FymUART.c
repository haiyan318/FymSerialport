/***************************************************************
 * 文件名   : FymUART.c
 * 功能     : CC2530 UART0 全双工收发 + LED 控制（第4-5周 任务1）
 * 说明     : 在原“CC2530UART控制”例程基础上改造：
 *            - 保留 board -> PC 的发送方向, 函数 Uart_Send_String()
 *            - 新增 PC -> board 的接收方向, 函数 Uart_Receive_String()
 *              通过串口接收中断逐个字符收进缓冲区, 主循环解析指令,
 *              控制开发板 LED, 并把执行结果回传给上位机。
 * 指令协议 : '1' -> YLED(P1_0/D2) 点亮, 回传 "led on"
 *            '0' -> YLED(P1_0/D2) 熄灭, 回传 "led off"
 *            '2' -> BLED(P1_1/D1) 点亮, 回传 "led2 on"
 *            '3' -> BLED(P1_1/D1) 熄灭, 回传 "led2 off"
 *            其它 -> 回传 "unknown"
 * 串口参数 : UART0, 备用位置1 (TX=P0_2 / RX=P0_3), 19200 8-N-1
 * 硬件     : CC2530 开发板, 晶振 32MHz
 ********************************************************************/

#include <ioCC2530.h>
#include <string.h>

#define uint  unsigned int
#define uchar unsigned char

/* ---------------- 板载 LED 定义（与第二周任务一致）---------------- */
#define YLED  P1_0    // 黄灯 D2
#define BLED  P1_1    // 蓝灯 D1

#define CMD_BUF_LEN  16           // 指令缓冲长度

/* ---------------- 全局变量 ---------------- */
uchar RxBuf[CMD_BUF_LEN];         // 接收缓冲
volatile uchar RxIndex  = 0;      // 当前写入位置
volatile uchar CmdReady = 0;      // 一条指令接收完成标志

/* 预定义回传字符串（放在数据区, 避免代码区取址问题）*/
uchar msgLedOn[]  = "led on\r\n";
uchar msgLedOff[] = "led off\r\n";
uchar msgLed2On[] = "led2 on\r\n";
uchar msgLed2Off[]= "led2 off\r\n";
uchar msgUnknown[]= "unknown\r\n";
uchar msgReady[]  = "CC2530 UART ready\r\n";

void initUART0(void);
void InitLed(void);
void Uart_Send_String(uchar *Data, int len);
void Uart_Receive_String(void);

/****************************************************************
 * 初始化 LED 控制 IO
 ****************************************************************/
void InitLed(void)
{
    P1DIR |= 0x03;      // P1_0、P1_1 设为输出
    YLED = 1;           // 低电平点亮, 初始化为灭
    BLED = 1;
}

/****************************************************************
 * 初始化串口0（UART0）
 *   PERCFG=0x00  -> UART0 使用备用位置1, 即 TX=P0_2, RX=P0_3
 *   P0SEL=0x0C   -> P0_2、P0_3 复用为外设功能
 *   U0GCR=9 / U0BAUD=59 -> 波特率 19200（32MHz 系统时钟）
 *   数据位8, 停止位1, 无校验（U0UCR 复位默认值）
 ****************************************************************/
void initUART0(void)
{
    CLKCONCMD &= ~0x40;             // 系统时钟源选 32MHz 晶振
    while(CLKCONSTA & 0x40);        // 等待晶振稳定
    CLKCONCMD &= ~0x47;             // 系统主时钟 32MHz

    PERCFG = 0x00;                  // UART0 备用位置1 (P0口)
    P0SEL  = 0x0C;                  // P0_2、P0_3 用作串口
    P2DIR &= ~0xC0;                 // P0 优先作为 UART0

    U0CSR |= 0x80;                  // UART 工作方式
    U0GCR |= 9;                     // 波特率设置, 见CC2530手册表
    U0BAUD |= 59;                   // 波特率 19200

    UTX0IF = 0;                     // 清发送中断标志
    U0CSR |= 0x40;                  // 允许接收
    URX0IF = 0;                     // 清接收中断标志
    IEN0  |= 0x84;                  // 开总中断 EA + 允许 UART0 接收中断 URX0IE
}

/****************************************************************
 * Uart_Send_String —— 发送字符串（方向: 开发板 -> PC）
 ****************************************************************/
void Uart_Send_String(uchar *Data, int len)
{
    int j;
    for(j = 0; j < len; j++)
    {
        U0DBUF = *Data++;           // 写入发送缓冲
        while(UTX0IF == 0);         // 等待发送完成
        UTX0IF = 0;                 // 清发送标志
    }
}

/****************************************************************
 * UART0 接收中断服务程序
 *   每收到一个字节触发一次, 把字节存入 RxBuf。
 *   收到换行/回车 或 收到单个指令字符时, 置 CmdReady 通知主循环。
 ****************************************************************/
#pragma vector = URX0_VECTOR
__interrupt void UART0_RX_ISR(void)
{
    uchar ch;
    URX0IF = 0;                     // 清接收中断标志
    ch = U0DBUF;                    // 读走接收到的字节

    if((ch == '\n') || (ch == '\r') || (ch == '\0'))
    {
        if(RxIndex > 0) CmdReady = 1;      // 一行结束
    }
    else
    {
        if(RxIndex < CMD_BUF_LEN - 1)
            RxBuf[RxIndex++] = ch;
        /* 串口助手常不带换行发送单个字符, 这里即时触发 */
        if((ch == '1') || (ch == '0') || (ch == '2') || (ch == '3'))
            CmdReady = 1;
    }
}

/****************************************************************
 * Uart_Receive_String —— 解析接收到的指令并执行（方向: PC -> 开发板）
 *   由主循环反复调用, 指令完成后控制 LED 并回传结果。
 ****************************************************************/
void Uart_Receive_String(void)
{
    uchar cmd;

    if(CmdReady == 0) return;       // 没有新指令
    cmd = RxBuf[0];                 // 取首字符作为指令

    switch(cmd)
    {
        case '1':                   // 开灯
            YLED = 0;
            Uart_Send_String(msgLedOn,  strlen((char *)msgLedOn));
            break;
        case '0':                   // 关灯
            YLED = 1;
            Uart_Send_String(msgLedOff, strlen((char *)msgLedOff));
            break;
        case '2':
            BLED = 0;
            Uart_Send_String(msgLed2On, strlen((char *)msgLed2On));
            break;
        case '3':
            BLED = 1;
            Uart_Send_String(msgLed2Off, strlen((char *)msgLed2Off));
            break;
        default:
            Uart_Send_String(msgUnknown, strlen((char *)msgUnknown));
            break;
    }

    RxIndex  = 0;                   // 清空缓冲, 准备下一条指令
    memset(RxBuf, 0, CMD_BUF_LEN);
    CmdReady = 0;
}

/****************************************************************
 * 主函数
 ****************************************************************/
void main(void)
{
    InitLed();                      // 初始化 LED
    initUART0();                    // 初始化串口0
    Uart_Send_String(msgReady, strlen((char *)msgReady));   // 上电提示

    while(1)
    {
        Uart_Receive_String();      // 轮询处理接收指令
    }
}
