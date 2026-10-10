#ifndef MOCK_IOCC2530_H
#define MOCK_IOCC2530_H
/*
 * 离机自测用的 CC2530 寄存器“桩”头文件。
 * 仅用于在 PC 上用 gcc 编译/验证 FymUART.c 的控制逻辑，
 * 不代表真实寄存器地址，禁止用于真实烧录。
 */
#define URX0_VECTOR 2
#define __interrupt          /* 让 gcc 忽略 IAR 的 __interrupt 关键字 */

extern volatile unsigned char CLKCONCMD, CLKCONSTA;
extern volatile unsigned char PERCFG, P0SEL, P2DIR;
extern volatile unsigned char U0CSR, U0GCR, U0BAUD, U0UCR, IEN0, P1DIR;
extern volatile unsigned char URX0IF, UTX0IF;
extern volatile unsigned char P1_0, P1_1;   /* LED 位，用变量代替 SFRBIT */

/* 发送/接收缓冲：写=发送(捕获)，读(ISR)=取接收字节 */
extern volatile unsigned char *sim_dbuf_ptr(void);
#define U0DBUF (*(sim_dbuf_ptr()))

#endif /* MOCK_IOCC2530_H */
