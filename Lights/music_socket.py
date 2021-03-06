import time
import board
import neopixel
import sys
from collections import deque
import socket
import numpy as np

pixel_pin = board.D12
num_pixels = 60
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False, pixel_order=ORDER)
pixels_deque = deque([[0,0,0] for i in range(num_pixels)], maxlen=num_pixels) # pix is the deque that holds rgb values for each light. The oldest value gets bumped out every frame.


GLOBAL_SCALE = 0.05 #0.009
FMAX = 2000 # max frequency at dlen=257
DLEN = 257

# python3 music.py lower upper s1 s2 s3 b1 b2 b3 mode

SECTIONS = [ [0, int(sys.argv[1])], [int(sys.argv[1])+1, int(sys.argv[2])], [int(sys.argv[2])+1, FMAX] ] 
SECTION_SIZES = [SECTIONS[i][1]-SECTIONS[i][0] for i in range(len(SECTIONS))]

SCALES = []
BIASES = []

prev = 0
for i in range(3):
    SCALES.append(float(sys.argv[i+3])/100)
    BIASES.append(float(sys.argv[i+6]))

MODE = int(sys.argv[-1])

print("sections: " + str(SECTIONS))
print("scales: " + str(SCALES))
print("biases: " + str(BIASES))
print("mode: " + str(MODE))
#sys.exit(0)

pixels.fill((1,1,1))
pixels.show()

def get_volumes(freqs):

        data = np.abs( np.fft.rfft(freqs) ) # [-1]
        avg = [0]*len(SECTIONS)

        for i in range(len(data)):

                f = (i/DLEN)*FMAX # guessed frequency
                for s in range(len(SECTIONS)):
                        if SECTIONS[s][0] <= f <= SECTIONS[s][1]:
                                avg[s] += int(data[i])
                                break

        return [int( avg[i]/SECTION_SIZES[i] ) for i in range(len(SECTIONS))]


socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind(('0.0.0.0', 50000))
SOCKET_SCALE = 63

while True:
    # freqs = r.get_frames()
    # if len(freqs) > 0:

    data, addr = socket.recvfrom(1024)
    volumes = get_volumes(list(data))

    vals = []
    for i in range(len(volumes)):
        a = (volumes[i]*SCALES[i]*GLOBAL_SCALE*SOCKET_SCALE) + BIASES[i]
        b = int( min(max(a,0), 255) )
        vals.append(b)
    #print(vals)

    if MODE == 0: # all of the lights are the same
        pixels.fill(tuple(vals)) # assumes 3 sections

    elif MODE == 1: # lights divided into physical sections for frequency sections
        for i in range(num_pixels):
            val_index = int((i/num_pixels)*len(SECTIONS))  
            val = vals[val_index]

            color = (0, 0, 0)
            if val_index == 0:
                color = (val, 0, 0)
            elif val_index == 1:
                color = (0, val, 0)
            elif val_index == 2:
                color = (0, 0, val)

            pixels[i] = color

    elif MODE == 2: # "bass history" mode
        pixels_deque.append( [vals[0], 0, 0] )
        for i in range(num_pixels):
            pixels[i] = tuple(pixels_deque[i])

    pixels.show()

    # else: # no frames available
    #     pass
