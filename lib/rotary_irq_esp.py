# Copyright (c) 2023 GeekerBear
# ESP8266/ESP32 implementation
# Documentation:
#   https://github.com/tsiiot/micropython-rotary

"""
ESP8266 GPIO 推荐引脚
    通用输入输出口4
    通用输入输出口5
    GPIO12
    GPIO13
    GPIO14
以下 ESP8266 GPIO 引脚应谨慎使用。CLK 和 DT 信号的状态可能会影响引导顺序。如果可能，请使用其他 GPIO 引脚。
    GPIO0 - 用于检测启动模式。Bootloader 在上电期间引脚为低电平时运行。
    GPIO2 - 用于检测启动模式。连接到上拉电阻。
    GPIO15 - 用于检测启动模式。连接到下拉电阻。
一个引脚不支持中断。
    GPIO16 - 不支持中断。

ESP32 GPIO 推荐引脚
    ESP32 的所有 GPIO 引脚都支持中断，但是慎使用以下 ESP32 GPIO strapping 引脚
    GPIO0 - 用于检测启动模式。Bootloader 在上电期间引脚为低电平时运行。内部上拉电阻。
    GPIO2 - 用于进入串行引导加载程序。内部下拉电阻。
    GPIO4 - 技术参考表明这是一个 strapping pin，但没有描述用法。内部下拉电阻。
    GPIO5 - 用于配置 SDIO Slave。内部上拉电阻。
    GPIO12 - 用于选择闪光电压。内部下拉电阻。
    GPIO15 - 用于配置引导消息的静音。内部上拉电阻。
"""

from machine import Pin, Timer
from rotary import Rotary
from sys import platform

_esp8266_deny_pins = [16]


class RotaryIRQ(Rotary):

    def __init__(
        self,
        pin_num_clk,
        pin_num_dt,
        pin_num_btn,
        min_val=0,
        max_val=10,
        incr=1,
        reverse=False,
        range_mode=Rotary.RANGE_UNBOUNDED,
        pull_up=True,
        half_step=False,
        invert=False,
        rotary_id = 0
    ):

        if platform == 'esp8266':
            if pin_num_clk in _esp8266_deny_pins:
                raise ValueError(
                    '%s: Pin %d not allowed. Not Available for Interrupt: %s' %
                    (platform, pin_num_clk, _esp8266_deny_pins))
            if pin_num_dt in _esp8266_deny_pins:
                raise ValueError(
                    '%s: Pin %d not allowed. Not Available for Interrupt: %s' %
                    (platform, pin_num_dt, _esp8266_deny_pins))
            if pin_num_btn in _esp8266_deny_pins:
                raise ValueError(
                    '%s: Pin %d not allowed. Not Available for Interrupt: %s' %
                    (platform, pin_num_btn, _esp8266_deny_pins))

        if pull_up == True:
            self._pin_clk = Pin(pin_num_clk, Pin.IN, Pin.PULL_UP)
            self._pin_dt = Pin(pin_num_dt, Pin.IN, Pin.PULL_UP)
            self._pin_btn = Pin(pin_num_btn, Pin.IN, Pin.PULL_UP)
        else:
            self._pin_clk = Pin(pin_num_clk, Pin.IN)
            self._pin_dt = Pin(pin_num_dt, Pin.IN)
            self._pin_btn = Pin(pin_num_btn, Pin.IN)
            
        super().__init__(min_val, max_val, incr, reverse, range_mode, half_step, invert, rotary_id, self._pin_btn.value())
        
        self._counter_timer = Timer(1)

        self._enable_clk_irq(self._process_rotary_pins)
        self._enable_dt_irq(self._process_rotary_pins)
        self._enable_btn_irq(self._process_button_pins)
        self._enable_counter_timer(self._process_counter_timer)

    def _enable_clk_irq(self, callback=None):
        self._pin_clk.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=callback)

    def _enable_dt_irq(self, callback=None):
        self._pin_dt.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=callback)
    
    def _enable_btn_irq(self, callback=None):
        self._pin_btn.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=callback)
    
    def _enable_counter_timer(self, callback=None):
        self._counter_timer.init(period=100, mode=Timer.PERIODIC, callback=callback)

    def _disable_clk_irq(self):
        self._pin_clk.irq(handler=None)

    def _disable_dt_irq(self):
        self._pin_dt.irq(handler=None)
        
    def _disable_btn_irq(self):
        self._pin_btn.irq(handler=None)
        
    def _disable_counter_timer(self):
        self._counter_timer.deinit()

    def _hal_get_clk_value(self):
        return self._pin_clk.value()

    def _hal_get_dt_value(self):
        return self._pin_dt.value()
    
    def _hal_get_btn_value(self):
        return self._pin_btn.value()

    def _hal_enable_irq(self):
        self._enable_clk_irq(self._process_rotary_pins)
        self._enable_dt_irq(self._process_rotary_pins)
        self._enable_btn_irq(self._process_button_pins)
        self._enable_counter_timer(self._process_counter_timer)

    def _hal_disable_irq(self):
        self._disable_clk_irq()
        self._disable_dt_irq()
        self._disable_btn_irq()
        self._disable_counter_timer()

    def _hal_close(self):
        self._hal_disable_irq()
