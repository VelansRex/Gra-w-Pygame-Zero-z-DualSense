
from enum import IntEnum

TONES_QTY_MAX = 16          # how many tones will come into one UART command
TONES_TEMPO_COEF = 1        # sound tempo coef


class Note(IntEnum):   # duration (in 0,01s) of notes (note, half note, ...)
    N1 = 50
    N2 = 25
    N4 = 12

class Tones(IntEnum):  # in 0,01kHz
    XX = 0
    C3 = 13
    CS3 = 14
    D3 = 15
    DS3 = 16
    E3 = 17
    F3 = 18
    FS3 = 19
    G3 = 20
    GS3 = 21
    A3 = 22
    AS3 = 23
    B3 = 25
    C4 = 26
    CS4 = 28
    D4 = 29
    DS4 = 31
    E4 = 33
    F4 = 35
    FS4 = 37
    G4 = 39
    GS4 = 41
    A4 = 44
    AS4 = 47
    B4 = 49
    C5 = 52
    CS5 = 55
    D5 = 59
    DS5 = 62
    E5 = 66
    F5 = 70
    FS5 = 74
    G5 = 78
    GS5 = 83
    A5 = 88
    AS5 = 93
    B5 = 99
    C6 = 105
    CS6 = 111
    D6 = 118
    DS6 = 124
    E6 = 132
    F6 = 140
    FS6 = 148
    G6 = 157
    GS6 = 166
    A6 = 176
    AS6 = 186
    B6 = 198

MELODY_SAMPLE_INTRO = [
    Tones.C4, Note.N4,
    Tones.E4, Note.N4,
    Tones.F4, Note.N4,
    Tones.G4, Note.N1,
    Tones.XX, Note.N4,
    Tones.C4, Note.N4,
    Tones.E4, Note.N4,
    Tones.F4, Note.N4,
    Tones.G4, Note.N1,

    Tones.XX, Note.N4,
    Tones.C4, Note.N4,
    Tones.E4, Note.N4,
    Tones.F4, Note.N4,
    Tones.G4, Note.N2,
    Tones.E4, Note.N4,
    Tones.C4, Note.N4,
    Tones.E4, Note.N4,
    Tones.D4, Note.N1,
]

MELODY_SAMPLE_END_GAME = [
    Tones.C4, Note.N2,
    Tones.G3, Note.N4,
    Tones.G3, Note.N4,
    Tones.A3, Note.N2,
    Tones.G3, Note.N2,
    Tones.XX, Note.N2,
    Tones.B3, Note.N2,
    Tones.C4, Note.N2,
]

def play_tones(port, pause, *data):
    data_set = []
    tone_counter = 0
    data_list = list(*data)
    i = 0
    while i < (len(data_list) - 1):
        if tone_counter < TONES_QTY_MAX:
            data_set.append(data_list[i])
            data_set.append(int(data_list[i + 1] / TONES_TEMPO_COEF))
            i += 2
            tone_counter += 1

            if pause and tone_counter < TONES_QTY_MAX:
                data_set.append(0) # freq = 0 means silent
                data_set.append(pause)
                tone_counter += 1
        else:
            port.send("SOUND_PLAY", data_set)
            data_set = []
            tone_counter = 0
    # if remained any not sent data, do it now
    if len(data_set):
        port.send("SOUND_PLAY", data_set)



