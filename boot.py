import sys
import os
from machine import Pin, I2C, SoftI2C, UART
import uasyncio as asyncio
import utime
from rotary_irq_esp import RotaryIRQ

rotary = RotaryIRQ(pin_num_clk=0, pin_num_dt=1, pin_num_btn=2, reverse=False, half_step=True)

@rotary.counter
def counter_callback(count):
    """旋转编码器按键连续按下事件"""
    print('连续按下 %d 次' % count)

@rotary.change
def change_callback(value, direction):
    """旋转编码器数字变化事件"""
    print('值: %d -> 编码器动作: %s' % (value, '向左' if direction == -1 else '向右'))

@rotary.click
def click_callback(state, time):
    """旋转编码器按键单击事件"""
    print('类型: %s 持续时间: %d' % (('释放' if state == 1 else '按下'), time))
    
@rotary.dbclick
def dbclick_callback():
    """旋转编码器按键双击事件"""
    print('按键双击事件触发')

async def heartbeat():
    while True:
        await asyncio.sleep_ms(10)

event = asyncio.Event()
async def main():
    asyncio.create_task(heartbeat())
    while True:
        await event.wait()
        #print('result =', r.value())
        event.clear()

try:
    asyncio.run(main())
except (KeyboardInterrupt, Exception) as e:
    print('Exception {} {}\n'.format(type(e).__name__, e))
    rotary.close()
finally:
    ret = asyncio.new_event_loop()  # Clear retained uasyncio state

