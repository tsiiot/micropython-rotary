import sys
import os
from machine import Pin, I2C, SoftI2C, UART
import uasyncio as asyncio
import utime
from rotary_irq_esp import RotaryIRQ

rotary = RotaryIRQ(pin_num_clk=0, pin_num_dt=1, pin_num_btn=2, reverse=False, half_step=True)

async def heartbeat():
    while True:
        await asyncio.sleep_ms(10)

event = asyncio.Event()


@rotary.change
def change_callback(rotary_id, value, direction):
    """旋转编码器数字变化事件"""
    print('编码器ID: %d 值: %d -> 编码器动作: %s' % (rotary_id, value, '向左' if direction == -1 else '向右'))
    event.set()
    
@rotary.counter
def counter_callback(rotary_id, count):
    """旋转编码器按键连续按下事件"""
    print('编码器ID: %d 被连续按下 %d 次' % (rotary_id, count))
    event.set()

@rotary.click
def click_callback(rotary_id, state, time):
    """旋转编码器按键单击事件"""
    print('编码器ID: %d 动作类型: %s 持续时间: %d' % (rotary_id, ('释放' if state == 1 else '按下'), time))
    event.set()
    
@rotary.dbclick
def dbclick_callback(rotary_id):
    """旋转编码器按键双击事件"""
    print('编码器ID: %d 触发按键双击事件' % rotary_id)
    event.set()


async def main():
    asyncio.create_task(heartbeat())
    while True:
        await event.wait()
        #print('result = %s', '---')
        event.clear()

try:
    asyncio.run(main())
except (KeyboardInterrupt, Exception) as e:
    print('Exception {} {}\n'.format(type(e).__name__, e))
    rotary.close()
finally:
    ret = asyncio.new_event_loop()  # Clear retained uasyncio state