# Copyright (c) 2023 GeekerBear
# Pyboard implementation
# Documentation:
#   https://github.com/tsiiot/micropython-rotary

#没有Pyboard板子，这个没有测试

import os
from pyb import Pin
from pyb import ExtInt
from rotary import Rotary


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
        pull_up=False,
        half_step=False,
        invert=False,
        rotary_id = 0
    ):
        if pull_up == True:
            self._pin_clk = Pin(pin_num_clk, Pin.IN, Pin.PULL_UP)
            self._pin_dt = Pin(pin_num_dt, Pin.IN, Pin.PULL_UP)
            self._pin_btn = Pin(pin_num_btn, Pin.IN, Pin.PULL_UP)
        else:
            self._pin_clk = Pin(pin_num_clk, Pin.IN)
            self._pin_dt = Pin(pin_num_dt, Pin.IN)
            self._pin_btn = Pin(pin_num_btn, Pin.IN)
            
        super().__init__(min_val, max_val, incr, reverse, range_mode, half_step, invert, rotary_id, self._pin_btn.value())

        self._pin_clk_irq = ExtInt(
            pin_num_clk,
            ExtInt.IRQ_RISING_FALLING,
            Pin.PULL_NONE,
            self._process_rotary_pins)
        self._pin_dt_irq = ExtInt(
            pin_num_dt,
            ExtInt.IRQ_RISING_FALLING,
            Pin.PULL_NONE,
            self._process_rotary_pins)

        # turn on 3.3V output to power the rotary encoder (pyboard D only)
        if 'PYBD' in os.uname().machine:
            Pin('EN_3V3').value(1)

    def _enable_clk_irq(self):
        self._pin_clk_irq.enable()

    def _enable_dt_irq(self):
        self._pin_dt_irq.enable()

    def _disable_clk_irq(self):
        self._pin_clk_irq.disable()

    def _disable_dt_irq(self):
        self._pin_dt_irq.disable()

    def _hal_get_clk_value(self):
        return self._pin_clk.value()

    def _hal_get_dt_value(self):
        return self._pin_dt.value()

    def _hal_enable_irq(self):
        self._enable_clk_irq()
        self._enable_dt_irq()

    def _hal_disable_irq(self):
        self._disable_clk_irq()
        self._disable_dt_irq()

    def _hal_close(self):
        self._hal_disable_irq()
