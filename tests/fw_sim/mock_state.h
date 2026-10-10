#ifndef MOCK_STATE_H
#define MOCK_STATE_H
/* 离机自测辅助接口 */
void          sim_set_in_isr(int v);   /* 标记当前是否在中断上下文中 */
void          sim_set_rx(unsigned char b); /* 预置“收到”的字节 */
void          sim_tx_reset(void);      /* 清空发送捕获缓冲 */
int           sim_tx_len(void);        /* 已发送字节数 */
const char   *sim_tx_str(void);        /* 已发送内容(字符串视图) */
void          sim_led_reset(void);     /* 复位 LED 电平 */
#endif
