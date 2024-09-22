from enum import Enum
from timeit import default_timer as timer

from libraries.EduSense import Settings


class Status(Enum):
    OFF = 0
    ON = 1
    BLINK = 2
    DUMMY = 3


class LedMatrix:
    def __init__(self, port):
        self._port = port
        self._matrix_now = [[Status.OFF] * Settings.MATRIX_Y_SIZE for i in range(Settings.MATRIX_X_SIZE)]
        self._matrix_todo = [[Status.OFF] * Settings.MATRIX_Y_SIZE for i in range(Settings.MATRIX_X_SIZE)]
        self._matrix_sequence = [[0] * Settings.MATRIX_Y_SIZE for i in range(Settings.MATRIX_X_SIZE)]
        self._matrix_step = [[0] * Settings.MATRIX_Y_SIZE for i in range(Settings.MATRIX_X_SIZE)]
        self._matrix_tick = [[timer()] * Settings.MATRIX_Y_SIZE for i in range(Settings.MATRIX_X_SIZE)]

    # run this function periodically to continuously update LED on matrix
    def update(self):
        # check for LEDs for update
        for x in range(Settings.MATRIX_X_SIZE):
            for y in range(Settings.MATRIX_Y_SIZE):
                if self._matrix_todo[x][y] != self._matrix_now[x][y]:
                    if self._matrix_todo[x][y] == Status.ON:
                        self._port.cmd_led_turn_on(x, y)
                        self._matrix_now[x][y] = Status.ON
                        continue

                    if self._matrix_todo[x][y] == Status.OFF:
                        self._port.cmd_led_turn_off(x, y)
                        self._matrix_now[x][y] = Status.OFF
                        continue

                    if self._matrix_todo[x][y] == Status.BLINK:
                        self._port.cmd_led_turn_on(x, y)
                        self._matrix_now[x][y] = Status.BLINK
                        self._matrix_step[x][y] = 0
                        self._matrix_tick[x][y] = timer()
                        continue

        # now, is necessary to check current steps of blinking
        for x in range(Settings.MATRIX_X_SIZE):
            for y in range(Settings.MATRIX_Y_SIZE):
                if self._matrix_now[x][y] == Status.BLINK:
                    try:
                        step = self._matrix_step[x][y]
                        if timer() - self._matrix_tick[x][y] > self._matrix_sequence[x][y][step]:
                            seq_qty = len(self._matrix_sequence[x][y])
                            self._matrix_step[x][y] = (self._matrix_step[x][y] + 1) % seq_qty
                            step = self._matrix_step[x][y]
                            if (step % 2) == 0:
                                self._port.cmd_led_turn_on(x, y)
                            else:
                                self._port.cmd_led_turn_off(x, y)
                            self._matrix_tick[x][y] = timer()
                    except:
                        self._matrix_todo[x][y] = Status.OFF
                        self._port.cmd_led_turn_off(x, y)
                        print("Error during blinking on Led matrix. Led will be off:", x, ":", y)
                        continue

    # set properties for LED on maxtrix
    def pixel_set(self, kind, x, y, *data):
        self._matrix_sequence[x][y] = [0, 0]
        self._matrix_todo[x][y] = kind
        self._matrix_now[x][y] = Status.DUMMY  # forcing LED refresh

        # add new sequence
        for element in data:
            self._matrix_sequence[x][y].append(element)

        data_qty = len(self._matrix_sequence[x][y])

        # check if is even number of sequences. If not, add time=OFF
        if (data_qty % 2) != 0:
            self._matrix_sequence[x][y].append(0)

        # remove protection against empty sequence
        if data_qty > 2:
            del (self._matrix_sequence[x][y])[0:2]

    # clear whole matrix
    def clear(self):
        for x in range(Settings.MATRIX_X_SIZE):
            for y in range(Settings.MATRIX_Y_SIZE):
                self._matrix_todo[x][y] = Status.OFF
                self._matrix_now[x][y] = Status.DUMMY



