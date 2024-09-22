
import pygame
from enum import IntEnum
from libraries.EduSense import Settings


class PadKey(IntEnum):
    YELLOW = 3
    UP = 3
    BLUE = 2
    LEFT = 2
    WHITE = 9
    OK = 9
    RED = 1
    RIGHT = 1
    GREEN = 0
    DOWN = 0
    JOY = 10


class  PadAxis(IntEnum):
    X = 0
    Y = 1


class Joystick:
    def __init__(self):
        self._buttons_qty = None
        self._axes_qty = None
        self._guid = None
        self._name = None
        pygame.joystick.init()

    def open(self):
        # Get count of joysticks.
        joystick_count = pygame.joystick.get_count()

        for i in range(joystick_count):
            self._joystick = pygame.joystick.Joystick(i)
            self._joystick.init()

            try:
                self._joy_id = self._joystick.get_instance_id()
            except AttributeError:
                # get_instance_id() is an SDL2 method
                self._joy_id = self._joystick.get_id()

            # Get the name from the OS for the controller/joystick.
            self._name = self._joystick.get_name()
            if Settings.USB_NAME in self._name:
                print("Gamepad found")
                try:
                    self._guid = self._joystick.get_guid()
                except AttributeError:
                    # get_guid() is an SDL2 method
                    pass

                # Usually axis run in pairs, up/down for one, and left/right for the other.
                self._axes_qty = self._joystick.get_numaxes()

                self._buttons_qty = self._joystick.get_numbuttons()

                # hats = self._joystick.get_numhats()
                # for i in range(hats):
                #     hat = self._joystick.get_hat(i)

                return  # our joystick was found
        print("Gamepad not found")
        self._name = ''

    # check if pad can be used as regular joystick
    def is_open(self):
        if self._name:
            return True
        else:
            return False

    # get status of one button
    def button_get(self, button_name):
        if self.is_open():
            if button_name < self._buttons_qty:
                return self._joystick.get_button(button_name)
        else:
            # print("Can't read button. Gamepad not found.")
            pass
        return 0

    # get status of all buttons in following order: UP, DOWN, LEFT, RIGHT, OK, JOY
    def buttons_get(self):
        if self.is_open():
            buttons = []
            for i in (PadKey.UP, PadKey.DOWN, PadKey.LEFT, PadKey.RIGHT, PadKey.OK, PadKey.JOY):
                buttons.append(self._joystick.get_button(i))
            return buttons
        else:
            # print("Can't read buttons. Gamepad not found.")
            return [0, 0, 0, 0, 0, 0]


    def __axis_adjust(self, value):
        if abs(value) < Settings.JOYSTICK_DEAD_ZONE:
            return 0
        else:
            return value

    # get value of one axis
    def axis_get(self, axis):
        if self.is_open():
            if axis < self._axes_qty:
                return self.__axis_adjust(self._joystick.get_axis(axis))
        else:
            # print("Can't read axis. Gamepad not found.")
            pass
        return 0

    # get value of all axis in folliwing order: X Y
    def axes_get(self):
        if self.is_open():
            axes = []
            for i in (PadAxis.X, PadAxis.Y):
                axes.append(self.__axis_adjust(self._joystick.get_axis(i)))
            return axes
        else:
            # print("Can't read axes. Gamepad not found.")
            return 0, 0


