import sys
import os
from machine import Pin, I2C, SoftI2C, UART
import uasyncio as asyncio
import utime
from rotary_irq_rp2 import RotaryIRQ

class Application1():
    def __init__(self, rotary1):
        self._rotary1 = rotary1
        self.myevent = asyncio.Event()
        asyncio.create_task(self.action())
        self._rotary1.add_listener(self.change_callback)
        self._rotary1.add_button_listener(self.click_callback)
        self._rotary1.add_dbclick_listener(self.dbclick_callback)
        self._rotary1.add_counter_listener(self.counter_callback)
    
    def change_callback(self, rotary_id, value, direction):
        """旋转编码器数字变化事件"""
        print('编码器ID: %d 值: %d -> 编码器动作: %s' % (rotary_id, value, '向左' if direction == -1 else '向右'))
        self.myevent.set()
    
    def counter_callback(self, rotary_id, count):
        """按键连续按下事件"""
        print('编码器ID: %d 被连续按下 %d 次' % (rotary_id, count))
        self.myevent.set()

    def click_callback(self, rotary_id, state, time):
        """按键单击事件"""
        print('编码器ID: %d 动作类型: %s 持续时间: %d' % (rotary_id, ('释放' if state == 1 else '按下'), time))
        self.myevent.set()
        
    def dbclick_callback(self, rotary_id):
        """按键双击事件"""
        print('编码器ID: %d 触发按键双击事件' % rotary_id)
        self.myevent.set()
    
    def close(self):
        self._rotary1.close()
    
    async def action(self):
        while True:
            await self.myevent.wait()
            #print('循环读取编码器值:  rotary 1 = {}, rotary 2 = {}'. format(
            #    self._rotary1.value(), '-'))
            # do something with the encoder results ...
            self.myevent.clear()
        
rotary_encoder_1 = None


async def heartbeat():
    while True:
        await asyncio.sleep_ms(10)

event = asyncio.Event()

async def main():
    global rotary_encoder_1
    rotary_encoder_1 = RotaryIRQ(rotary_id=0,
                                 pin_num_clk=20,
                                 pin_num_dt=21,
                                 pin_num_btn=22,
                                 min_val=0,
                                 max_val=5,
                                 reverse=False,
                                 half_step=True,
                                 range_mode=RotaryIRQ.RANGE_WRAP)
    app1 = Application1(rotary_encoder_1)
    asyncio.create_task(heartbeat())
    while True:
        await event.wait()
        #print('result =', r.value())
        event.clear()

try:
    asyncio.run(main())
except (KeyboardInterrupt, Exception) as e:
    print('Exception {} {}\n'.format(type(e).__name__, e))
    rotary_encoder_1.close()
finally:
    ret = asyncio.new_event_loop()  # Clear retained uasyncio state



