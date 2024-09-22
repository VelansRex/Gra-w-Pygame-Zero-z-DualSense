from ctypes import *
from ctypes import c_char, c_ubyte
from timeit import default_timer as timer

from enum import IntEnum
import serial
import serial.tools.list_ports

from libraries.EduSense import General
from libraries.EduSense import Settings


UART_WAIT_TIME_FOR_ANSWER = (100 / 1000)  # [s] czas oczekiwania na odpowiedź z urządzenia
UART_DATA_SIZE_MAX = 200  # max. liczba danych w ramce do i z urządzenia

ASCII_STX = 0x02
ASCII_ETX = 0x03


class ButtonField(IntEnum):
    YELLOW = 0
    UP = 0
    GREEN = 1
    DOWN = 1
    BLUE = 2
    LEFT = 2
    RED = 3
    RIGHT = 3
    WHITE = 4
    OK = 4
    JOY = 5


class JoystickAxis(IntEnum):
    HORIZONTAL = 0
    X = 0
    VERTICAL = 1
    Y = 1

class ExpFunction(IntEnum):
    IN_PULLUP = 1
    IN_PULLDOWN = 2
    OUT = 3
    OUT_OD = 4
    ADC = 5
    DAC = 6
    DAC2 = 7
    I2C = 8
    SPI_CLK = 9
    SPI_DO = 10
    SPI_DI = 11
    ONEWIRE = 12
    RGB = 13
    PWM = 14
    UART_RX = 15
    UART_TX = 16


class RxTxDataStruct(Structure):
    _pack_ = 1
    _fields_ = [("STX", c_ubyte),
                ("frame_cnt", c_char * 2),
                ("cmd", c_char * 2),
                ("data", c_ubyte * (UART_DATA_SIZE_MAX - 1 - 2 - 2 - 1)),
                ("ETX", c_ubyte)]


class Frame(Union):
    _pack_ = 1
    _fields_ = [("row", c_ubyte * UART_DATA_SIZE_MAX),
                ("rx", RxTxDataStruct),
                ("tx", RxTxDataStruct)]


uart_cmd_list = [
    # COMMAND_NAME | COMMAND_NUMBER | DATA FORMAT TX | DATA FORMAT RX
    # c:char n:nibble(0-0xF)  b:byte(0-0xFF)  i:int(0-0xFFFF),
    # x(or X) for RX will ignore one char from frame, for TX will ignore one var passed to <send>
    # uppecase mean loop (up to end of data), to read i.e. row data for sound, pixels to turn on, etc.
    # SPACE: used for readability and to separate strings i.e. ccccc ccc will give two words: 5 and 3 chars long.
    # there is no need to write below (in DATA FORMAT RX) format for standard error replay (like E00)
    ["PAD_STATUS", 0x02, "", "cbbb"],
    ["LED_ON", 0x03, "nnNN", ""],
    ["LED_OFF", 0x04, "nnNN", ""],
    ["LED_MATRIX", 0x05, "bB", ""],
    ["LED_INTENSITY", 0x06, "b", ""],
    ["JOYSTICK_GET", 0x07, "", "cbb"],
    ["BUTTONS_GET", 0x08, "", "cnnnnnn"],
    ["SOUND_PLAY", 0x09, "bbBB", ""],

    ["VIRT_WRITE", 0x10, "bbbbnbB", ""],
    ["VIRT_ON", 0x11, "bbbbnbB", ""],
    ["VIRT_OFF", 0x12, "bbbbnbB", ""],
    ["VIRT_TOGGLE", 0x13, "bbbbnbB", ""],
    ["VIRT_FILL", 0x14, "n", ""],
    ["VIRT_SHOW", 0x15, "bbn", ""],

    ["EXP_FN_SET", 0x20, "nb", ""],
    ["EXP_PWR_SET", 0x21, "n", ""],
    ["EXP_PWR_STATUS", 0x22, "", "nn"],
    ["EXP_IO_IN_GET", 0x23, "n", "cn"],
    ["EXP_IO_OUT_SET", 0x24, "nn", ""],
    ["EXP_ADC_GET", 0x25, "n", "ci"],
    ["EXP_DAC_SET", 0x26, "ni", ""]
]


def uart_cmd(name):
    return [x[1] for x in uart_cmd_list if x[0] == name][0]


def uart_cmd_tx_format(name):
    return [x[2] for x in uart_cmd_list if x[0] == name]


def uart_cmd_rx_format(name):
    return [x[3] for x in uart_cmd_list if x[0] == name]


class Uart:
    def __init__(self):
        self._port = None
        self._frame_received = Frame()
        self._frame_to_send = Frame()
        self._frame_cnt = 0
        self.__last_rx_error = 0

    def open(self):
        # searching for USB device with VID/PID correspond to our pad designators.
        for port_search in serial.tools.list_ports.comports():
            if port_search.vid == Settings.USB_VID and port_search.pid == Settings.USB_PID:
                try:
                    self._port = serial.Serial(port_search.device)
                    print("Device connected to port:", port_search.device)
                    return True
                except:
                    print("Unable to open port:", port_search.device)
                    return False
        if self._port is None:
            print("Pad not found. Please, check USB connection")
            return False

    def close(self):
        self._port.close()

    def is_open(self):
        if self._port is None or not self._port.isOpen():
            return False
        else:
            return True

    def send(self, cmd_name, *dane_in):
        current_data_in_cnt = 0
        current_buffer_offset = 0

        datas = General.vars_to_list(*dane_in)

        self._frame_to_send.tx.STX = ASCII_STX
        self._frame_cnt = (self._frame_cnt + 1) % 256
        self._frame_to_send.tx.frame_cnt = "{:02X}".format(self._frame_cnt).encode("ascii")
        self._frame_to_send.tx.cmd = "{:02X}".format(uart_cmd(cmd_name)).encode("ascii")

        if self.is_open():
            self._port.reset_input_buffer()
            frame_format = ''.join(uart_cmd_tx_format(cmd_name))
            char_cnt = 0
            first_time = True

            while current_data_in_cnt < len(datas):
                for element in frame_format:

                    if current_data_in_cnt >= len(datas):
                        break

                    if first_time and element.isupper():
                        continue
                    if not first_time and element.islower():  # this is OK, because we have digits and special chars
                        continue

                    letter = element.upper()

                    if letter == 'C':
                        self._frame_to_send.tx.data[current_buffer_offset: current_buffer_offset + 1] = \
                            datas[current_data_in_cnt][char_cnt].encode('ascii')
                        char_cnt += 1
                        current_buffer_offset += 1
                        continue
                    else:
                        if char_cnt:
                            char_cnt = 0
                            current_data_in_cnt += 1
                            if current_data_in_cnt >= len(datas):
                                break

                    if letter == 'N':
                        self._frame_to_send.tx.data[current_buffer_offset: current_buffer_offset + 1] = \
                            "{:01X}".format(datas[current_data_in_cnt]).encode("ascii")
                        current_data_in_cnt += 1
                        current_buffer_offset += 1
                        continue

                    if letter == 'B':
                        self._frame_to_send.tx.data[current_buffer_offset: current_buffer_offset + 2] = \
                            "{:02X}".format(datas[current_data_in_cnt]).encode("ascii")
                        current_data_in_cnt += 1
                        current_buffer_offset += 2
                        continue

                    if letter == 'I':
                        self._frame_to_send.tx.data[current_buffer_offset: current_buffer_offset + 4] = \
                            "{:04X}".format(datas[current_data_in_cnt]).encode("ascii")
                        current_data_in_cnt += 1
                        current_buffer_offset += 4
                        continue

                    if letter == 'X':
                        current_data_in_cnt += 1
                        continue

                    if letter == ' ':
                        continue

                    current_data_in_cnt += 1

                first_time = False
            self._frame_to_send.tx.data[current_buffer_offset] = ASCII_ETX
            end_idx = bytes(self._frame_to_send.row).find(ASCII_ETX)
            if end_idx > -1:
                self._port.write(self._frame_to_send.row[:end_idx + 1])
                return self.__receive(cmd_name)
        return False, []

    def __receive(self, cmd_name):
        if self.is_open():
            received_cnt = 0
            time_start = timer()

            while timer() - time_start < UART_WAIT_TIME_FOR_ANSWER:
                if self._port.in_waiting:
                    received_char = self._port.read()
                    if received_char[0] == ASCII_STX:
                        received_cnt = 0
                    self._frame_received.row[received_cnt] = received_char[0]
                    received_cnt += 1
                    if self._frame_received.rx.STX == ASCII_STX and received_char[0] == ASCII_ETX:
                        if int(self._frame_received.rx.frame_cnt, 16) != self._frame_cnt:
                            print("Error: expected frame numer:{}, received:{}".format(
                                int(self._frame_received.rx.frame_cnt, 16), self._frame_cnt))
                            return False, []

                        # OK, we have correct frame. Now, we will analyze it and will do list with answers
                        return self.__receive_get_values(cmd_name)
        return False, []

    def __receive_get_values(self, cmd_name):
        results = []
        current_offset = 0

        end_offset = bytes(self._frame_received.rx.data).find(ASCII_ETX)
        if not end_offset > -1:  # end of frame not found
            return False, []

        frame_format = ''.join(uart_cmd_rx_format(cmd_name))
        first_time = True
        text = ''
        self.__last_rx_error = 0

        # the response with the error number may be in a different format than standard response (like button status)
        # therefore we have to analyze it separately.
        if self._frame_received.rx.data[0] == ord('E'):
            if end_offset == 3:  # error is always 3 chars long
                results.append('E')
                self.__last_rx_error = General.ascii_to_int(self._frame_received.rx.data[1: 1 + 2])
                results.append(self.__last_rx_error)
            else:
                return False, []
        else:
            while current_offset < end_offset:
                for element in frame_format:
                    if current_offset >= end_offset:
                        break

                    if first_time and element.isupper():
                        continue
                    if not first_time and element.islower():
                        continue
                    letter = element.upper()

                    if letter == 'C':
                        text += '%c' % (self._frame_received.rx.data[current_offset])
                        current_offset += 1
                        continue
                    else:
                        if len(text):
                            results.append(text)
                            text = ''

                    if letter == 'N':
                        value = General.ascii_to_int(
                            self._frame_received.rx.data[current_offset: current_offset + 1])
                        results.append(value)
                        current_offset += 1
                        continue

                    if letter == 'B':
                        value = General.ascii_to_int(
                            self._frame_received.rx.data[current_offset: current_offset + 2])
                        results.append(value)
                        current_offset += 2
                        continue

                    if letter == 'I':
                        value = General.ascii_to_int(
                            self._frame_received.rx.data[current_offset: current_offset + 4])
                        results.append(value)
                        current_offset += 4
                        continue

                    if letter == 'X':
                        current_offset += 1
                        continue

                    if letter == ' ':
                        continue

                    current_offset += 1
                first_time = False

        return True, results

    def last_error_get(self):
        return self.__last_rx_error

    # get firmware version
    def cmd_pad_status(self):
        is_ok, version = self.send("PAD_STATUS")
        if is_ok and self.__last_rx_error == 0:
            version.pop(0)
            return True, version
        else:
            return False, []

    # turn on LED on matrix
    def cmd_led_turn_on(self, x, y):
        if x >= Settings.MATRIX_X_SIZE | y >= Settings.MATRIX_Y_SIZE:
            print("Wrong coordinates of LED diode")
            return False
        is_ok, *_ = self.send("LED_ON", x, y)
        return is_ok and self.__last_rx_error == 0

    # turn off LED on matrix
    def cmd_led_turn_off(self, x, y):
        if x >= Settings.MATRIX_X_SIZE | y >= Settings.MATRIX_Y_SIZE:
            print("Wrong coordinates of LED diode")
            return False
        is_ok, *_ = self.send("LED_OFF", x, y)
        return is_ok and self.__last_rx_error == 0

    # store data on LED matrix column by column
    def cmd_matrix_by_columns(self, *data):
        is_ok, *_ = self.send("LED_MATRIX", *data)
        return is_ok and self.__last_rx_error == 0

    # store data on LED matrix row by row
    def cmd_matrix_by_rows(self, *data):
        matrix_v = [0] * 8
        matrix_h = General.vars_to_list(*data)
        bit_number = 0

        for row in matrix_h:
            for i in range(8):
                if row & (1 << i):
                    matrix_v[i] |= (1 << bit_number)
            bit_number += 1

        is_ok, *_ = self.send("LED_MATRIX", matrix_v)
        return is_ok and self.__last_rx_error == 0

    # set global LED matrix intensity
    def cmd_led_intensity(self, value):
        if value > Settings.MATRIX_INTENSITY_MAX:
            value = Settings.MATRIX_INTENSITY_MAX
        is_ok, *_ = self.send("LED_INTENSITY", value)
        return is_ok and self.__last_rx_error == 0

    # get position of joystick axes
    def cmd_joystick_get(self):
        results = []
        is_ok, results = self.send("JOYSTICK_GET")

        if is_ok and results[0] == 'D':
            direction_x = results[1] / 0xFF * 2 - 1
            if abs(direction_x) < Settings.JOYSTICK_DEAD_ZONE:
                direction_x = 0

            direction_y = results[2] / 0xFF * 2 - 1
            if abs(direction_y) < Settings.JOYSTICK_DEAD_ZONE:
                direction_y = 0
            return True, [direction_x, direction_y]
        else:
            return False, []

    # get status of all buttons on pad: UP, DOWN, LEFT, RIGHT, OK, JOY
    def cmd_buttons_get(self):
        results = []
        is_ok, results = self.send("BUTTONS_GET")

        if is_ok and results[0] == 'D':
            results.pop(0)
            return True, results
        else:
            return False, []

    # get status of one button on pad
    def cmd_button_get(self, color):
        results = []
        is_ok, results = self.send("BUTTONS_GET")

        if is_ok and results[0] == 'D':
            results.pop(0)
            return True, [results[color]]
        else:
            return False, []

    # set some tones to play by pad
    def cmd_sound_play(self, *data):
        is_ok, *_ = self.send("SOUND_PLAY", *data)
        return is_ok and self.__last_rx_error == 0

    def __cmd_virt_operation_sub(self, *data):
        param_list = General.vars_to_list(*data)
        # limit value for XY position
        if param_list[0] > Settings.VIRT_SCREEN_X_SIZE:
            param_list[0] = Settings.VIRT_SCREEN_X_SIZE
        if param_list[1] > Settings.VIRT_SCREEN_Y_SIZE:
            param_list[1] = Settings.VIRT_SCREEN_Y_SIZE
        # limit size of virt screen
        if param_list[2] > Settings.VIRT_SCREEN_X_SIZE:
            param_list[2] = Settings.VIRT_SCREEN_X_SIZE
        if param_list[3] > Settings.VIRT_SCREEN_Y_SIZE:
            param_list[3] = Settings.VIRT_SCREEN_Y_SIZE
        # limit parameter roll
        param_list[4] = int(param_list[4] != 0)
        # limit data with pixels
        for i in range(5, len(param_list)):
            param_list[i] &= 0xFF
        return param_list

    # write data (turn on and off) to virtual screen
    def cmd_virt_write(self, *data):
        param_list = self.__cmd_virt_operation_sub(*data)
        is_ok, *_ = self.send("VIRT_WRITE", param_list)
        return is_ok and self.__last_rx_error == 0

    # turn on (only) data to virtual screen
    def cmd_virt_on(self, *data):
        param_list = self.__cmd_virt_operation_sub(*data)
        is_ok, *_ = self.send("VIRT_ON", param_list)
        return is_ok and self.__last_rx_error == 0

    # turn off (only) data to virtual screen
    def cmd_virt_off(self, *data):
        param_list = self.__cmd_virt_operation_sub(*data)
        is_ok, *_ = self.send("VIRT_OFF", param_list)
        return is_ok and self.__last_rx_error == 0

    # toggle data on virtual screen
    def cmd_virt_toggle(self, *data):
        param_list = self.__cmd_virt_operation_sub(*data)
        is_ok, *_ = self.send("VIRT_TOGGLE", param_list)
        return is_ok and self.__last_rx_error == 0

    # fill (1) or clear (0) whole virtual screen
    def cmd_virt_fill(self, onoff):
        onoff = int(onoff != 0)
        is_ok, *_ = self.send("VIRT_FILL", onoff)
        return is_ok and self.__last_rx_error == 0

    # show part of virtual screen on LED matrix
    def cmd_virt_show(self, *data):
        param_list = General.vars_to_list(*data)
        # limit value of XY position
        if param_list[0] > Settings.VIRT_SCREEN_X_SIZE:
            param_list[0] = Settings.VIRT_SCREEN_X_SIZE
        if param_list[1] > Settings.VIRT_SCREEN_Y_SIZE:
            param_list[1] = Settings.VIRT_SCREEN_Y_SIZE
        # limit parameter roll
        param_list[2] = int(param_list[2] != 0)

        is_ok, *_ = self.send("VIRT_SHOW", param_list)
        return is_ok and self.__last_rx_error == 0

    # assign specific function to pin in expander
    def cmd_exp_fn_set(self, *data):
        if data[0] != 1 and data[0] != 2:
            print("Incorrect pin number")
            return False
        is_ok, *_ = self.send("EXP_FN_SET", *data)
        return is_ok and self.__last_rx_error == 0

    # turn on/off power (+5V) on expander
    def cmd_exp_pwr_set(self, onoff):
        onoff = int(onoff != 0)
        is_ok, *_ = self.send("EXP_PWR_SET", onoff)
        return is_ok and self.__last_rx_error == 0

    # get status of power pin on expander (on/off, overload)
    def cmd_exp_pwr_status(self):
        is_ok, result = self.send("EXP_PWR_STATUS")
        if is_ok and self.__last_rx_error == 0:
            result.pop(0)
            return True, result
        else:
            return False, []

    # get pin state used as digital input
    def cmd_exp_io_in_get(self, *data):
        if data[0] != 1 and data[0] != 2:
            print("Incorrect pin number")
            return False
        is_ok, result = self.send("EXP_IO_IN_GET", data[0])
        if is_ok and self.__last_rx_error == 0:
            result.pop(0)
            return True, result
        else:
            return False, []

    # set pin state used as digital output
    def cmd_exp_io_out_set(self, *data):
        param_list = General.vars_to_list(*data)
        if param_list[0] != 1 and param_list[0] != 2:
            print("Incorrect pin number")
            return False
        param_list[1] = int(param_list[1] != 0)

        is_ok, result = self.send("EXP_IO_OUT_SET", param_list)
        return is_ok and self.__last_rx_error == 0

    # get analog value (voltage in [mV]) on pin of expander
    def cmd_exp_adc_get(self, *data):
        if data[0] != 1 and data[0] != 2:
            print("Incorrect pin number")
            return False
        is_ok, result = self.send("EXP_ADC_GET", data[0])
        if is_ok and self.__last_rx_error == 0:
            result.pop(0)
            return True, result
        else:
            return False, []

    # set analog value (voltage in [mV]) on pin of expander
    def cmd_exp_dac_set(self, *data):
        param_list = General.vars_to_list(*data)
        if param_list[0] != 1 and param_list[0] != 2:
            print("Incorrect pin number")
            return False

        is_ok, *_ = self.send("EXP_DAC_SET", param_list)
        return is_ok and self.__last_rx_error == 0
