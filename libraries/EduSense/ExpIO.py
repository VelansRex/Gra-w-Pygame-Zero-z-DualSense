import math
from timeit import default_timer as timer

import pygame
from pgzero.builtins import Actor
from libraries.EduSense import General
from libraries.EduSense import Uart




def write_title(screen, title, picture, pos_x, pos_y):
    font = pygame.font.SysFont('default', 30)
    label = font.render(title, 1, (255, 255, 255))
    x = pos_x + (picture.width - label.get_width()) / 2
    y = pos_y + picture.height
    screen.blit(label, (x, y))


class Voltmeter:
    def __init__(self, screen, *port):
        self._screen = screen
        self._INT_RADIUS = 12
        self._EXT_RADIUS = 117
        self._CENTER_X = 153
        self._CENTER_Y = 150
        self._TEXT_X_OFFSET = 90
        self._TEXT_Y_OFFSET = 170
        self._VOLTAGE_AT_RATIO_1 = 4

        if len(port) == 1:
            self._port = port[0]
        else:
            self._port = None
        self._pin_number = None

        self.title = ""
        self._x = 0
        self._y = 0
        self._voltage = 0
        self.time_between_readings = 0.2
        self._last_read_tick = 0

        self._actor = Actor('voltmeter', anchor=('left', 'top'))
        self._topleft_set((0, 0))

    def _topleft_set(self, position):
        self._x, self._y = position
        self._actor.x = self._x
        self._actor.y = self._y

    def _topleft_get(self):
        return (self._x, self._y)

    topleft = property(_topleft_get, _topleft_set)

    @property
    def pin_number(self):
        return self._pin_number

    @pin_number.setter
    def pin_number(self, value):
        if value != 1 and value != 2:
            raise ValueError("Incorrect pin number")
        self._pin_number = value
        # Frankly, there is no need to set pin as ADC. We could do it, but without it, still reading will work
        # in many cases, is even better to not set it. In this way, we can i.e. read voltage on pin set as ANALOG OUT
        # if self._port and self._port.is_open():
        #     status = self._port.cmd_exp_fn_set(value, Uart.ExpFunction.ADC)
        #     if status:
        #         self._pin_number = value
        #     else:
        #         print("Error occure during pin setting.")
        # else:
        #     print("Port isn't ready. Can't set pin.")

    @property
    def voltage(self):
        if self._port and self._pin_number:
            if timer() - self._last_read_tick > self.time_between_readings:
                self._last_read_tick = timer()
                if self._port.is_open():
                    status, result = self._port.cmd_exp_adc_get(self._pin_number)
                    if status:
                        self.voltage = result[0] / 1000  # because we get value in [mV]
                    else:
                        print("Can't read pin.")
                else:
                    print("Port isn't ready. Therefore I can't get voltage from pin.")
            else:
                # print("I can't read so fast")
                pass

        return self._voltage

    @voltage.setter
    def voltage(self, value):
        self._voltage = General.clamp_value(value, 0, self._VOLTAGE_AT_RATIO_1)

    @property
    def ratio(self):
        return self._voltage / self._VOLTAGE_AT_RATIO_1

    @ratio.setter
    def ratio(self, value):
        self.voltage = General.clamp_value(value, 0, 1) * self._VOLTAGE_AT_RATIO_1 # it will do limit twice

    def update(self):
        _ = self.voltage

    def mouse_get_pos(self, pos):
        pass

    def mouse_get_click(self):
        pass

    def draw(self):
        # drawing picture of voltmeter
        self._actor.draw()

        # drawing pointer
        center_x = self._CENTER_X + self._x
        center_y = self._CENTER_Y + self._y
        angle = self._voltage / self._VOLTAGE_AT_RATIO_1 * math.pi - math.pi
        x2 = self._EXT_RADIUS * math.cos(angle) + center_x
        y2 = self._EXT_RADIUS * math.sin(angle) + center_y
        # drawing few lines to get thicker pointer
        for i in range(-3, 4):
            x1 = self._INT_RADIUS * math.cos(angle + i / 30) + center_x
            y1 = self._INT_RADIUS * math.sin(angle + i / 30) + center_y
            # screen.draw.line((x1, y1), (x2, y2), (255, 0, 0))
            pygame.draw.line(self._screen, (255, 0, 0), (x1, y1), (x2, y2))

        # writting digital representation of voltage
        text_x_offset = self._TEXT_X_OFFSET + self._x
        text_y_offset = self._TEXT_Y_OFFSET + self._y

        # screen.draw.text("{:1.3f}V".format(self._voltage), (text_x_offset, text_y_offset),
        #                  fontsize=64, color="red", anchor=(0, 0))
        font = pygame.font.SysFont('default', 64)
        label = font.render("{:1.3f}V".format(self._voltage), 1, (255, 0, 0))
        self._screen.blit(label, (text_x_offset, text_y_offset))
        # write title of this picture
        write_title(self._screen, self.title, self._actor, self._x, self._y)


class Potentiometer:
    def __init__(self, screen, *port):
        self._screen = screen
        self._SLIDER_X_0 = 19
        self._SLIDER_Y_0 = 200
        self._SLIDER_Y_100 = 20
        self._VOLTAGE_AT_RATIO_1 = 3.3

        if len(port) == 1:
            self._port = port[0]
        else:
            self._port = None
        self._pin_number = None
        self._x = 0
        self._y = 0
        self.title = ""
        self._ratio = 0
        self._last_read_tick  = 0
        self.time_between_readings = 0.1
        self._mouse_pos = (0, 0)

        self._actor_potentiometer = Actor('potentiometer', anchor=('left', 'top'))
        self._actor_slider = Actor('potentiometer-slider', anchor=('left', 'top'))
        self._topleft_set((0, 0))


    def _topleft_get(self):
        return (self._x, self._y)

    def _topleft_set(self, position):
        self._x, self._y = position
        self._actor_potentiometer.x = self._x
        self._actor_potentiometer.y = self._y

    topleft = property(_topleft_get, _topleft_set)

    @property
    def pin_number(self):
        return self._pin_number

    @pin_number.setter
    def pin_number(self, value):
        if value != 1 and value != 2:
            raise ValueError("Incorrect pin number")

        if self._port and self._port.is_open():
            status = self._port.cmd_exp_fn_set(value, Uart.ExpFunction.DAC)
            if status:
                self._pin_number = value
            else:
                print("Error occure during pin setting.")
        else:
            print("Port isn't ready. Can't set pin.")

    def __set_val_at_exp_pin(self):
        if self._port and self._pin_number:
            if timer() - self._last_read_tick > self.time_between_readings:
                self._last_read_tick = timer()
                if self._port.is_open():
                    status = self._port.cmd_exp_dac_set(self._pin_number, int(self._ratio * self._VOLTAGE_AT_RATIO_1 * 1000))
                    if status:
                        pass
                    else:
                        print("Error occured while setting voltage.")
                else:
                    print("Port isn't ready. Therefore I can't set voltage on pin.")
            else:
                # print("I can't do changes so fast")
                pass

    @property
    def ratio(self):
        return self._ratio

    @ratio.setter
    def ratio(self, value):
        self._ratio = General.clamp_value(value, 0, 1)
        self.__set_val_at_exp_pin()

    def voltage_get(self):
        return self._ratio * self._VOLTAGE_AT_RATIO_1

    def voltage_set(self, value):
        self._ratio = General.clamp_value(value, 0, self._VOLTAGE_AT_RATIO_1) / self._VOLTAGE_AT_RATIO_1
        self.__set_val_at_exp_pin()

    voltage = property(voltage_get, voltage_set)

    def update(self):
        pass

    def mouse_get_pos(self, pos):
        self._mouse_pos = pos

    def mouse_get_click(self):
        # now, when user click, we will calculate desired ratio of potentiometer
        if self._actor_potentiometer.collidepoint(self._mouse_pos):
            offset = self._mouse_pos[1] - self._y
            offset -= self._actor_slider.height / 2
            offset = General.clamp_value(offset, self._SLIDER_Y_100, self._SLIDER_Y_0)
            self.ratio = (offset - self._SLIDER_Y_0) / (self._SLIDER_Y_100 - self._SLIDER_Y_0)

    def draw(self):
        # drawing enclosure of potentiometer
        self._actor_potentiometer.draw()
        # drawing slider, according to set of voltage
        self._actor_slider.x = self._x + self._SLIDER_X_0
        offset = (self._SLIDER_Y_100 - self._SLIDER_Y_0) * self._ratio
        self._actor_slider.y = self._y + self._SLIDER_Y_0 + offset
        self._actor_slider.draw()
        # write title of this picture
        write_title(self._screen, self.title, self._actor_potentiometer, self._x, self._y)



class DigitalOutput:
    def __init__(self, screen, *port):
        self._screen = screen
        self._PIC_SWITCH_ON = "switch-on.png"
        self._PIC_SWITCH_OFF = "switch-off.png"
        if len(port) == 1:
            self._port = port[0]
        else:
            self._port = None
        self._pin_number = None
        self._x = 0
        self._y = 0
        self.title = ""
        self._last_read_tick  = 0
        self.time_between_readings = 0.1
        self._mouse_pos = (0, 0)

        self._state = 0
        self._actor_switch = Actor(self._PIC_SWITCH_OFF, anchor=('left', 'top'))
        self._OFFSET_Y_TO_TURN_ON = self._actor_switch.height / 2
        self._topleft_set((0, 0))


    def _topleft_get(self):
        return (self._x, self._y)

    def _topleft_set(self, position):
        self._x, self._y = position
        self._actor_switch.x = self._x
        self._actor_switch.y = self._y

    topleft = property(_topleft_get, _topleft_set)

    @property
    def pin_number(self):
        return self._pin_number

    @pin_number.setter
    def pin_number(self, value):
        if value != 1 and value != 2:
            raise ValueError("Incorrect pin number")

        if self._port and self._port.is_open():
            status = self._port.cmd_exp_fn_set(value, Uart.ExpFunction.OUT)
            if status:
                self._pin_number = value
            else:
                print("Error occure during pin setting.")
        else:
            print("Port isn't ready. Can't set pin.")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        val_candidate = int(General.clamp_value(value, 0, 1))

        if self._port and self._pin_number:
            if timer() - self._last_read_tick > self.time_between_readings:
                self._last_read_tick = timer()
                if self._port.is_open():
                    status = self._port.cmd_exp_io_out_set(self._pin_number, val_candidate)
                    if status:
                        self._state = val_candidate
                    else:
                        print("Error occured while setting pin.")
                else:
                    print("Port isn't ready. Therefore I can't set pin.")
            else:
                # print("I can't do changes so fast.")
                pass
        else:
            self._state = val_candidate

        if self._state:
            self._actor_switch.image = self._PIC_SWITCH_ON
        else:
            self._actor_switch.image = self._PIC_SWITCH_OFF

    def update(self):
        pass

    def mouse_get_pos(self, pos):
        self._mouse_pos = pos

    def mouse_get_click(self):
        # now, when user click, we will calculate desired ratio of potentiometer
        if self._actor_switch.collidepoint(self._mouse_pos):
            offset = self._mouse_pos[1] - self._y
            self.state = int(offset < self._OFFSET_Y_TO_TURN_ON)

    def draw(self):
        # drawing enclosure of switch
        self._actor_switch.draw()
        # write title of this switch
        write_title(self._screen, self.title, self._actor_switch, self._x, self._y)


class DigitalInput:
    def __init__(self, screen, *port):
        self._screen = screen
        self._PIC_LED_ON = "led-on.png"
        self._PIC_LED_OFF = "led-off.png"
        if len(port) == 1:
            self._port = port[0]
        else:
            self._port = None
        self._pin_number = None
        self._x = 0
        self._y = 0
        self.title = ""
        self._last_read_tick  = 0
        self.time_between_readings = 0.1

        self._state = 0
        self._actor_led = Actor(self._PIC_LED_OFF, anchor=('left', 'top'))
        self._topleft_set((0, 0))


    def _topleft_get(self):
        return (self._x, self._y)

    def _topleft_set(self, position):
        self._x, self._y = position
        self._actor_led.x = self._x
        self._actor_led.y = self._y

    topleft = property(_topleft_get, _topleft_set)

    @property
    def pin_number(self):
        return self._pin_number

    @pin_number.setter
    def pin_number(self, value):
        if value != 1 and value != 2:
            raise ValueError("Incorrect pin number")

        if self._port and self._port.is_open():
            status = self._port.cmd_exp_fn_set(value, Uart.ExpFunction.IN_PULLDOWN)
            if status:
                self._pin_number = value
            else:
                print("Error occure during pin setting.")
        else:
            print("Port isn't ready. Can't set pin.")

    @property
    def state(self):
        if self._port and self._pin_number:
            if timer() - self._last_read_tick > self.time_between_readings:
                self._last_read_tick = timer()
                if self._port.is_open():
                    status, result = self._port.cmd_exp_io_in_get(self._pin_number)
                    if status:
                        self._state = result[0]
                    else:
                        print("Can't read pin.")
                else:
                    print("Port isn't ready. Therefore I can't get state of pin.")
            else:
                # print("I can't do changes so fast")
                pass

        if self._state:
            self._actor_led.image = self._PIC_LED_ON
        else:
            self._actor_led.image = self._PIC_LED_OFF
        return self._state

    @state.setter
    def state(self, value):
        self._state = int(General.clamp_value(value, 0, 1))
        if self._state:
            self._actor_led.image = self._PIC_LED_ON
        else:
            self._actor_led.image = self._PIC_LED_OFF

    def update(self):
        _ = self.state

    def mouse_get_pos(self, pos):
        pass

    def mouse_get_click(self):
        pass

    def draw(self):
        self._actor_led.draw()
        # write title of this LED
        write_title(self._screen, self.title, self._actor_led, self._x, self._y)





class PowerSwitch:
    def __init__(self, screen, *port):
        self._screen = screen
        self._PIC_SWITCH_ON = "power-switch-on.png"
        self._PIC_SWITCH_OFF = "power-switch-off.png"
        if len(port) == 1:
            self._port = port[0]
        else:
            self._port = None
        self._x = 0
        self._y = 0
        self.title = ""
        self._last_read_tick  = 0
        self.time_between_readings = 0.2
        self._mouse_pos = (0, 0)

        self._state = 0
        self._actor_switch = Actor(self._PIC_SWITCH_OFF, anchor=('left', 'top'))
        self._OFFSET_Y_TO_TURN_ON = self._actor_switch.height / 2
        self._topleft_set((0, 0))

        self.state = self._state


    def _topleft_get(self):
        return (self._x, self._y)

    def _topleft_set(self, position):
        self._x, self._y = position
        self._actor_switch.x = self._x
        self._actor_switch.y = self._y

    topleft = property(_topleft_get, _topleft_set)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        val_candidate = int(General.clamp_value(value, 0, 1))

        if self._port:
            if timer() - self._last_read_tick > self.time_between_readings:
                self._last_read_tick = timer()
                if self._port.is_open():
                    status = self._port.cmd_exp_pwr_set(val_candidate)
                    if status:
                        self._state = val_candidate
                    else:
                        print("Error occured while setting power.")
                else:
                    print("Port isn't ready. Therefore I can't set power pin.")
            else:
                # print("I can't do changes so fast.")
                pass
        else:
            self._state = val_candidate

        if self._state:
            self._actor_switch.image = self._PIC_SWITCH_ON
        else:
            self._actor_switch.image = self._PIC_SWITCH_OFF

    def update(self):
        pass

    def mouse_get_pos(self, pos):
        self._mouse_pos = pos

    def mouse_get_click(self):
        # now, when user click, we will calculate desired ratio of potentiometer
        if self._actor_switch.collidepoint(self._mouse_pos):
            offset = self._mouse_pos[1] - self._y
            self.state = int(offset < self._OFFSET_Y_TO_TURN_ON)

    def draw(self):
        # drawing enclosure of switch
        self._actor_switch.draw()
        # write title of this switch
        write_title(self._screen, self.title, self._actor_switch, self._x, self._y)



