/* 离机自测：CC2530 寄存器桩实现 */
#include <string.h>
#include "ioCC2530.h"
#include "mock_state.h"

volatile unsigned char CLKCONCMD = 0, CLKCONSTA = 0;
volatile unsigned char PERCFG = 0, P0SEL = 0, P2DIR = 0;
volatile unsigned char U0CSR = 0, U0GCR = 0, U0BAUD = 0, U0UCR = 0, IEN0 = 0, P1DIR = 0;
volatile unsigned char URX0IF = 0, UTX0IF = 0;
volatile unsigned char P1_0 = 1, P1_1 = 1;   /* 低电平点亮，初始灭 */

static volatile unsigned char g_dbuf = 0;    /* “接收”字节 */
static unsigned char          g_tx[512];
static int                    g_txn = 0;
static int                    g_in_isr = 0;

volatile unsigned char *sim_dbuf_ptr(void)
{
    UTX0IF = 1;                 /* 任一次访问都视为发送完成，避免死等 */
    if (g_in_isr)
        return &g_dbuf;         /* ISR 读：返回接收到的字节 */
    return &g_tx[g_txn++];      /* 发送写：每个字符独占一个槽，精确捕获 */
}

void sim_set_in_isr(int v)         { g_in_isr = v; }
void sim_set_rx(unsigned char b)   { g_dbuf = b; }
void sim_tx_reset(void)            { g_txn = 0; memset(g_tx, 0, sizeof g_tx); }
int  sim_tx_len(void)              { return g_txn; }
const char *sim_tx_str(void)       { return (const char *)g_tx; }
void sim_led_reset(void)           { P1_0 = 1; P1_1 = 1; }
