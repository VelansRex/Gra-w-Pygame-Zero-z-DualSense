import struct

def calcentries(fmt):  # calculate length of data after decompress, according template <fmt>
    return len(struct.unpack(fmt, bytearray(struct.calcsize(fmt))))


def ascii_to_int(data):  # convert str to int. Work also with 1 ASCII char (1/2 byte, value 0 - 0xF)
    value = 0
    for i in data:
        temp = i - 0x30
        if temp > 9:
            temp -= 0x41 - 0x30 - 10
        value *= 16
        value += temp
    return value

def vars_to_list(*data_in):
    datas = []

    if len(data_in):
        if isinstance(data_in[0], list):
            datas = list(*data_in)
        else:
            for i in range(len(data_in)):
                datas.append(data_in[i])
        return datas
    return []

def clamp_value(val, limit_min, limit_max):
    return max(limit_min, min(limit_max, val))


