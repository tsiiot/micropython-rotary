# Copyright (c) 2023 GeekerBear
# Raspberry Pi Pico implementation
# Documentation:
#   https://github.com/tsiiot/micropython-rotary

from machine import Pin, Timer
from rotary import Rotary

IRQ_RISING_FALLING = Pin.IRQ_RISING | Pin.IRQ_FALLING


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
        if pull_up:
            self._pin_clk = Pin(pin_num_clk, Pin.IN, Pin.PULL_UP)
            self._pin_dt = Pin(pin_num_dt, Pin.IN, Pin.PULL_UP)
            self._pin_btn = Pin(pin_num_btn, Pin.IN, Pin.PULL_UP)
        else:
            self._pin_clk = Pin(pin_num_clk, Pin.IN)
            self._pin_dt = Pin(pin_num_dt, Pin.IN)
            self._pin_btn = Pin(pin_num_btn, Pin.IN)
            
        super().__init__(min_val, max_val, incr, reverse, range_mode, half_step, invert, rotary_id, self._pin_btn.value())
        self._counter_timer = Timer(-1)
        self._hal_enable_irq()

    def _enable_clk_irq(self):
        self._pin_clk.irq(self._process_rotary_pins, IRQ_RISING_FALLING)

    def _enable_dt_irq(self):
        self._pin_dt.irq(self._process_rotary_pins, IRQ_RISING_FALLING)
        
    def _enable_btn_irq(self):
        self._pin_btn.irq(self._process_button_pins, IRQ_RISING_FALLING)
        
    def _enable_counter_timer(self, callback=None):
        self._counter_timer.init(period=100, mode=Timer.PERIODIC, callback=callback)

    def _disable_clk_irq(self):
        self._pin_clk.irq(None, 0)

    def _disable_dt_irq(self):
        self._pin_dt.irq(None, 0)
        
    def _disable_btn_irq(self):
        self._pin_btn.irq(None, 0)
        
    def _disable_counter_timer(self):
        self._counter_timer.deinit()

    def _hal_get_clk_value(self):
        return self._pin_clk.value()

    def _hal_get_dt_value(self):
        return self._pin_dt.value()
    
    def _hal_get_btn_value(self):
        return self._pin_btn.value()

    def _hal_enable_irq(self):
        self._enable_clk_irq()
        self._enable_dt_irq()
        self._enable_btn_irq()
        self._enable_counter_timer(self._process_counter_timer)

    def _hal_disable_irq(self):
        self._disable_clk_irq()
        self._disable_dt_irq()
        self._disable_btn_irq()
        self._disable_counter_timer()

    def _hal_close(self):
        self._hal_disable_irq()
