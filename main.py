import soundcard as sc
import numpy as np
import serial
from time import time
from threading import Thread

SAMPLERATE = 41000

devices = [x for x in sc.all_microphones() if x.id.startswith("bluez_source")]

if devices.__len__() == 0:
    print("No devices found")
    exit(1)

device = devices[0]

port = serial.Serial("/dev/ttyACM0", baudrate=115200)


def limit(n, mn, mx):
    if n > mx:
        return mx
    if n < mn:
        return mn
    return n


# Creates a new color from pitch and brightness readings
# int p         analogRead(pitch) representing the voltage between 0 and 5 volts
# double b      analogRead(brightness) representing volume of music for LED brightness
# returns Color structure with rgb values, which appear synced to the music

def pitchConv(p):
    c = (0, 0, 0)

    if p < 40:
        c = (255, 0, 0)
    elif p >= 40 and p <= 77:
        b = (p - 40) * (255/37.0000)
        c = (255, 0, b)
    elif p > 77 and p <= 205:
        r = 255 - ((p - 78) * 2)
        c = (r, 0, 255)
    elif p >= 206 and p <= 238:
        g = (p - 206) * (255/32.0000)
        c = (0, g, 255)
    elif p <= 239 and p <= 250:
        r = (p - 239) * (255/11.0000)
        c = (r, 255, 255)
    elif p >= 251 and p <= 270:
        c = (255, 255, 255)
    elif p >= 271 and p <= 398:
        rb = 255-((p-271)*2)
        c = (rb, 255, rb)
    elif p >= 398 and p <= 653:
        c = (0, 255-(p-398), (p-398))
    else:
        c = (255, 0, 0)
    return c

def normal_distribution(w):
    width = w+1
    weights = np.exp(-np.square([2*x/width for x in range(width)]))
    weights = np.pad(weights, (width-1, 0), 'reflect')
    weights = weights/np.sum(weights)
    return weights


def detect_pitch(int_data):
    WIND = 10
    CYCLE = 400
    weights = normal_distribution(WIND)
    smooth_data = np.convolve(int_data, weights, mode='valid')
    smooth_pitches = [0]+[np.mean(smooth_data[:-delay] - smooth_data[delay:]) for delay in range(1, CYCLE)]

    dips = [x for x in range(
        WIND, CYCLE-WIND) if smooth_pitches[x] == np.min(smooth_pitches[x-WIND:x+WIND])]
    
    if len(dips) > 1:
        av_dip = np.mean(np.ediff1d(dips))
        cheq_freq = SAMPLERATE / av_dip
        return cheq_freq

prevpit = 0

frames = 0
last = time()
rate = 0

buffer = []

step = 0.1

c = [0, 0, 0]

def read():
    global buffer
    # read audio
    data = device.record(samplerate=SAMPLERATE, numframes=int(SAMPLERATE/100), channels=2)
    buffer = data

t = Thread(target=read)
t.start()

# clear serial buffer
port.read_all()

def limit(v):
    if v > 255:
        return 255
    if v < 0:
        return 0
    return int(v)


while True:
    frames += 1

    if time() - last > 1:
        rate = frames
        frames = 0
        last = time()

    t.join()

    t = Thread(target=read)
    t.start()

    data = buffer

    # calculate volume
    vol = np.linalg.norm(data) / 6
    pit = detect_pitch([x[0] for x in data])
    if pit is None:
        pit = prevpit / 3
    else:
        prevpit = pit / 3
        pit = pit / 3

    r = pitchConv(int(pit))
    print(f"{rate} FPS   vol {str(int(vol*100)).rjust(3,'0')}    pit {str(int(pit)).rjust(4,'0')}    RGB({int(r[0])},{int(r[1])},{int(r[2])})")

    # smooth fading
    c[0] += (r[0] - c[0]) * step
    c[1] += (r[1] - c[1]) * step
    c[2] += (r[2] - c[2]) * step

    # send color to microcontroller
    port.write(
        (limit(c[0] * vol), limit(c[1] * vol), limit(c[2] * vol))
    )

    port.flush()
