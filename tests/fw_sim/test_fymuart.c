/*
 * FymUART 固件“离机”逻辑自测
 * 把真实固件源码 FymUART.c 编译进本测试单元，用桩寄存器驱动，
 * 验证：接收中断断帧 -> Uart_Receive_String 分支 -> LED 电平 -> 回传字符串。
 * 编译：gcc -std=c99 -I mock -o test_fymuart.exe test_fymuart.c mock_state.c
 */
#include <stdio.h>
#include <string.h>
#include "mock_state.h"

/* 将固件源码纳入本编译单元（重命名其 main，避免与测试 main 冲突） */
#define main firmware_main_unused
#include "../../FymUART/FymUART.c"
#undef main

static int g_fail = 0;
static int g_total = 0;

static void check(const char *name, int cond)
{
    g_total++;
    printf("  [%s] %s\n", cond ? "PASS" : "FAIL", name);
    if (!cond) g_fail++;
}

/* 模拟“串口收到一个字节”：进入中断上下文并触发接收 ISR */
static void feed(unsigned char c)
{
    sim_set_in_isr(1);
    sim_set_rx(c);
    UART0_RX_ISR();
    sim_set_in_isr(0);
}

static void reset_case(void)
{
    sim_tx_reset();
    sim_led_reset();
    RxIndex = 0;
    CmdReady = 0;
    memset(RxBuf, 0, CMD_BUF_LEN);
}

int main(void)
{
    printf("==== FymUART 离机逻辑自测 ====\n");

    InitLed();
    initUART0();
    check("InitLed 后 YLED 初始为灭(P1_0=1)", P1_0 == 1);
    check("InitLed 后 BLED 初始为灭(P1_1=1)", P1_1 == 1);
    check("UART0 已进入 UART 方式(U0CSR bit7=1)", (U0CSR & 0x80) != 0);
    check("UART0 允许接收(U0CSR bit6=1)", (U0CSR & 0x40) != 0);
    check("波特率寄存器 U0GCR=9 / U0BAUD=59 (19200)", (U0GCR == 9) && (U0BAUD == 59));
    check("使能总中断+UART0接收中断 IEN0 bit7/bit2 = 1,1",
          ((IEN0 & 0x80) != 0) && ((IEN0 & 0x04) != 0));

    /* 用例1：指令 '1' -> 开灯 */
    reset_case(); feed('1'); Uart_Receive_String();
    printf("    -> 收到'1'  回传=\"%s\" YLED=%d BLED=%d\n", sim_tx_str(), P1_0, P1_1);
    check("'1' 使 YLED 点亮(P1_0=0)", P1_0 == 0);
    check("'1' 回传 \"led on\\r\\n\"", strcmp(sim_tx_str(), "led on\r\n") == 0);

    /* 用例2：指令 '0' -> 关灯 */
    reset_case(); feed('0'); Uart_Receive_String();
    printf("    -> 收到'0'  回传=\"%s\" YLED=%d\n", sim_tx_str(), P1_0);
    check("'0' 使 YLED 熄灭(P1_0=1)", P1_0 == 1);
    check("'0' 回传 \"led off\\r\\n\"", strcmp(sim_tx_str(), "led off\r\n") == 0);

    /* 用例3：指令 '2' -> 蓝灯开 */
    reset_case(); feed('2'); Uart_Receive_String();
    check("'2' 使 BLED 点亮(P1_1=0)", P1_1 == 0);
    check("'2' 回传 \"led2 on\\r\\n\"", strcmp(sim_tx_str(), "led2 on\r\n") == 0);

    /* 用例4：指令 '3' -> 蓝灯关 */
    reset_case(); feed('3'); Uart_Receive_String();
    check("'3' 使 BLED 熄灭(P1_1=1)", P1_1 == 1);
    check("'3' 回传 \"led2 off\\r\\n\"", strcmp(sim_tx_str(), "led2 off\r\n") == 0);

    /* 用例5：非法指令（非指令字符需以换行结束才成帧） */
    reset_case();
    feed('x'); Uart_Receive_String();
    check("无换行的非指令字符不成帧(不回传)", sim_tx_len() == 0);
    feed('\n'); Uart_Receive_String();
    check("整行非指令 \"x\\n\" 回传 \"unknown\\r\\n\"", strcmp(sim_tx_str(), "unknown\r\n") == 0);

    /* 用例6：带换行结尾的整行指令 "1\r\n" */
    reset_case();
    feed('1'); feed('\r'); feed('\n');
    Uart_Receive_String();
    check("整行 \"1\\r\\n\" 也能正确开灯并回传", (P1_0 == 0) && (strcmp(sim_tx_str(), "led on\r\n") == 0));

    /* 用例7：连续多条指令状态保持/切换 */
    reset_case();
    feed('1'); Uart_Receive_String();   /* 开 */
    feed('0'); Uart_Receive_String();   /* 关 */
    check("连续 '1''0' 后灯灭且回传=led off", (P1_0 == 1) && (strcmp(sim_tx_str(), "led on\r\nled off\r\n") == 0));

    printf("\n==== 结果: %d/%d 通过 ====\n", g_total - g_fail, g_total);
    return g_fail == 0 ? 0 : 1;
}
