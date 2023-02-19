# Copyright (c) 2023 GeekerBear
# Platform-independent MicroPython code for the rotary encoder module
# Documentation:
#   https://github.com/tsiiot/micropython-rotary

import micropython
import utime

_DIR_CW = const(0x10)  # Clockwise step
_DIR_CCW = const(0x20)  # Counter-clockwise step

# Rotary Encoder States
_R_START = const(0x0)
_R_CW_1 = const(0x1)
_R_CW_2 = const(0x2)
_R_CW_3 = const(0x3)
_R_CCW_1 = const(0x4)
_R_CCW_2 = const(0x5)
_R_CCW_3 = const(0x6)
_R_ILLEGAL = const(0x7)

_transition_table = [

    # |------------- NEXT STATE -------------|            |CURRENT STATE|
    # CLK/DT    CLK/DT     CLK/DT    CLK/DT
    #   00        01         10        11
    [_R_START, _R_CCW_1, _R_CW_1,  _R_START],             # _R_START
    [_R_CW_2,  _R_START, _R_CW_1,  _R_START],             # _R_CW_1
    [_R_CW_2,  _R_CW_3,  _R_CW_1,  _R_START],             # _R_CW_2
    [_R_CW_2,  _R_CW_3,  _R_START, _R_START | _DIR_CW],   # _R_CW_3
    [_R_CCW_2, _R_CCW_1, _R_START, _R_START],             # _R_CCW_1
    [_R_CCW_2, _R_CCW_1, _R_CCW_3, _R_START],             # _R_CCW_2
    [_R_CCW_2, _R_START, _R_CCW_3, _R_START | _DIR_CCW],  # _R_CCW_3
    [_R_START, _R_START, _R_START, _R_START]]             # _R_ILLEGAL

_transition_table_half_step = [
    [_R_CW_3,            _R_CW_2,  _R_CW_1,  _R_START],
    [_R_CW_3 | _DIR_CCW, _R_START, _R_CW_1,  _R_START],
    [_R_CW_3 | _DIR_CW,  _R_CW_2,  _R_START, _R_START],
    [_R_CW_3,            _R_CCW_2, _R_CCW_1, _R_START],
    [_R_CW_3,            _R_CW_2,  _R_CCW_1, _R_START | _DIR_CW],
    [_R_CW_3,            _R_CCW_2, _R_CW_3,  _R_START | _DIR_CCW],
    [_R_START,           _R_START, _R_START, _R_START],
    [_R_START,           _R_START, _R_START, _R_START]]

_STATE_MASK = const(0x07)
_DIR_MASK = const(0x30)


def _wrap(value, incr, lower_bound, upper_bound):
    range = upper_bound - lower_bound + 1
    value = value + incr

    if value < lower_bound:
        value += range * ((lower_bound - value) // range + 1)

    return lower_bound + (value - lower_bound) % range


def _bound(value, incr, lower_bound, upper_bound):
    return min(upper_bound, max(lower_bound, value + incr))


def _trigger(rotary_instance, value, direction):
    for listener in rotary_instance._listener:
        listener(value, direction)
        
def _trigger_button(rotary_instance, state, t):
    for listener in rotary_instance._button_listener:
        listener(state, t)
        
def _trigger_dbclick(rotary_instance):
    for listener in rotary_instance._dbclick_listener:
        listener()
       
def _trigger_counter(rotary_instance, count):
    for listener in rotary_instance._counter_listener:
        listener(count)


class Rotary(object):

    RANGE_UNBOUNDED = const(1) # 无边界
    RANGE_WRAP = const(2) # 范围包裹
    RANGE_BOUNDED = const(3) # 范围边界
    
    BUTTON_PRESS = const(0) # 按钮按下
    BUTTON_RELEASE = const(1) # 按钮释放

    def __init__(self, min_val, max_val, incr, reverse, range_mode, half_step, invert, btn_value):
        self._min_val = min_val
        self._max_val = max_val
        self._incr = incr
        self._reverse = -1 if reverse else 1
        self._range_mode = range_mode
        self._value = min_val
        self._direction = 0
        self._state = _R_START
        self._half_step = half_step
        self._invert = invert
        self._listener = []
        self._btn_value = btn_value
        self._btn_press_time = 0
        self._btn_press_count = 0
        self._button_listener = []
        self._dbclick_listener = []
        self._counter_listener = []
        

    def set(self, value=None, min_val=None, incr=None,
            max_val=None, reverse=None, range_mode=None):
        # disable DT and CLK pin interrupts
        """设置参数"""
        self._hal_disable_irq()

        if value is not None:
            self._value = value
        if min_val is not None:
            self._min_val = min_val
        if max_val is not None:
            self._max_val = max_val
        if incr is not None:
            self._incr = incr
        if reverse is not None:
            self._reverse = -1 if reverse else 1
        if range_mode is not None:
            self._range_mode = range_mode
        self._state = _R_START

        # enable DT and CLK pin interrupts
        self._hal_enable_irq()

    def value(self):
        """当前值"""
        return self._value
    
    def direction(self):
        """旋钮方向"""
        return self._direction

    def reset(self):
        """重置当前值"""
        self._value = 0

    def close(self):
        """关闭"""
        self._hal_close()

    def add_listener(self, l):
        self._listener.append(l)

    def remove_listener(self, l):
        if l not in self._listener:
            raise ValueError('{} is not an installed listener'.format(l))
        self._listener.remove(l)
    
    def add_button_listener(self, l):
        self._button_listener.append(l)
        
    def remove_button_listener(self, l):
        if l not in self._button_listener:
            raise ValueError('{} is not an installed button_listener'.format(l))
        self._button_listener.remove(l)
        
    def add_counter_listener(self, l):
        self._counter_listener.append(l)
        
    def remove_counter_listener(self, l):
        if l not in self._counter_listener:
            raise ValueError('{} is not an installed counter_listener'.format(l))
        self._counter_listener.remove(l)
        
    def add_dbclick_listener(self, l):
        self._dbclick_listener.append(l)
        
    def remove_dbclick_listener(self, l):
        if l not in self._dbclick_listener:
            raise ValueError('{} is not an installed dbclick_listener'.format(l))
        self._dbclick_listener.remove(l)
        
    def _process_rotary_pins(self, pin):
        """处理编码器"""
        old_value = self._value
        clk_dt_pins = (self._hal_get_clk_value() <<
                       1) | self._hal_get_dt_value()
        
                       
        if self._invert:
            clk_dt_pins = ~clk_dt_pins & 0x03
            
        # Determine next state
        
        if self._half_step:
            self._state = _transition_table_half_step[self._state &
                                                      _STATE_MASK][clk_dt_pins]
        else:
            self._state = _transition_table[self._state &
                                            _STATE_MASK][clk_dt_pins]
        direction = self._state & _DIR_MASK
        

        incr = 0
        if direction == _DIR_CW:
            incr = self._incr
        elif direction == _DIR_CCW:
            incr = -self._incr

        incr *= self._reverse

        if self._range_mode == self.RANGE_WRAP:
            self._value = _wrap(
                self._value,
                incr,
                self._min_val,
                self._max_val)
        elif self._range_mode == self.RANGE_BOUNDED:
            self._value = _bound(
                self._value,
                incr,
                self._min_val,
                self._max_val)
        else:
            self._value = self._value + incr
            
        self._direction = incr

        try:
            if old_value != self._value and len(self._listener) != 0:
                _trigger(self, self.value(), self.direction())
                
            if old_value != self._value and 'change_callback_func' in dir(self):
                self.change_callback_func(self.value(), self.direction())
        except:
            pass
        
    def change(self, func):
        """
        编码器数值改变回调,@rotary.change
        """
        self.change_callback_func = func
        
    def _process_button_pins(self, pin):
        """处理编码器按钮"""
        old_value = self._btn_value
        self._btn_value = self._hal_get_btn_value()
        
        try:
            if old_value != self._btn_value:
                if self._btn_value == BUTTON_PRESS: #按下
                    self._btn_press_time = utime.ticks_ms() #按下的时间
                    self._btn_press_count = self._btn_press_count + 1 #按下计数器累加
                    
                    if len(self._button_listener) != 0:
                        _trigger_button(self, BUTTON_PRESS, 0)
                        
                    if 'click_callback_func' in dir(self):
                        self.click_callback_func(BUTTON_PRESS, 0)
                        
                elif self._btn_value == BUTTON_RELEASE: #释放
                    diff_time = utime.ticks_ms() - self._btn_press_time
                    
                    if len(self._button_listener) != 0:
                        _trigger_button(self, BUTTON_RELEASE, diff_time)
                    
                    if 'click_callback_func' in dir(self):
                        self.click_callback_func(BUTTON_RELEASE, diff_time)
                else:
                    print('按钮: 未知')
        except:
            pass
        
        #print('_process_button_pins -> None')
        
    def click(self, func):
        """
        编码器按键单击,在方法上添加@rotary.click
        """
        self.click_callback_func = func
        
    def _process_counter_timer(self, t):
        """处理编码器按键连续按下计数器"""
        try:
            if self._btn_press_count > 1 and (utime.ticks_ms() - self._btn_press_time) >= 250:
                if self._btn_press_count > 2 and len(self._counter_listener) != 0:
                    _trigger_counter(self, self._btn_press_count)
                    
                if self._btn_press_count > 2 and 'counter_callback_func' in dir(self):
                    self.counter_callback_func(self._btn_press_count)
                
                if self._btn_press_count == 2 and len(self._dbclick_listener) != 0:
                    _trigger_dbclick(self)
                    
                if self._btn_press_count == 2 and 'dbclick_callback_func' in dir(self):
                    self.dbclick_callback_func()
                
                self._btn_press_count = 0
        except:
            pass
        
        # 如果计数一次,并且两次按键时间大于200毫秒,将不做连续按键处理
        if self._btn_press_count == 1 and (utime.ticks_ms() - self._btn_press_time) >= 230:
            self._btn_press_count = 0
        
    def counter(self, func):
        """
        编码器按键连续按下计数器@rotary.counter
        """
        self.counter_callback_func = func
    
    def dbclick(self, func):
        """
        编码器按键双击,在方法上添加@rotary.dbclick
        """
        self.dbclick_callback_func = func
