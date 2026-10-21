#!/usr/bin/env python3
"""Tile sheet: every overworld/town tile from build/charset.bin, each shown as a 3x3 patch."""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
B = lambda f: os.path.join(ROOT, "build", f)
cs, g = open(B('charset.bin'), 'rb').read(), open(B('gen.asm')).read()
tc = [int(v) for v in g.split('tile_char  !byte ')[1].split('\n')[0].split(',')]
tcol = [int(v) & 7 for v in g.split('tile_color !byte ')[1].split('\n')[0].split(',')]
bg = [0, 9, 15]
n = len(tc)
im = Image.new('RGB', (n * 28, 24), (40, 40, 40)); p = im.load()
for t in range(n):
    for ty in range(3):
        for tx in range(3):
            for r in range(8):
                b = cs[tc[t] * 8 + r]
                for i in range(4):
                    v = (b >> (6 - 2 * i)) & 3
                    c = PAL[tcol[t] if v == 3 else bg[v]]
                    x, y = t * 28 + tx * 8 + i * 2, ty * 8 + r
                    p[x, y] = c; p[x + 1, y] = c
os.makedirs(os.path.join(ROOT, 'shots'), exist_ok=True)
im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(ROOT, 'shots', 'tiles.png'))
