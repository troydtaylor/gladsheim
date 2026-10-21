#!/usr/bin/env python3
"""Preview overworld tiles (each as a 3x3 patch, to check how they tile) from build/charset.bin."""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL = [(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),
       (139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
cs = open(os.path.join(ROOT, "build/charset.bin"), "rb").read()
colors = [5, 6, 5, 5, 2, 7, 5, 3, 5, 6]
bg = [0, 9, 15]
n = len(colors)
im = Image.new("RGB", (n * 56, 48), (30, 30, 30))
p = im.load()
for t in range(n):
    for ty in range(3):
        for tx in range(3):
            for q in range(4):
                code = 72 + t * 4 + q
                for r in range(8):
                    b = cs[code * 8 + r]
                    for i in range(4):
                        v = (b >> (6 - 2 * i)) & 3
                        c = PAL[colors[t] if v == 3 else bg[v]]
                        x = t * 56 + tx * 16 + (q & 1) * 8 + i * 2
                        y = ty * 16 + (q >> 1) * 8 + r
                        p[x, y] = c
                        p[x + 1, y] = c
im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(ROOT, "shots/tiles.png"))
