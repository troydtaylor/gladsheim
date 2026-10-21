#!/usr/bin/env python3
"""Render build/town<N>.bin with the real charset (whole-town preview).  usage: townview.py [town index]"""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
B = lambda f: os.path.join(ROOT, "build", f)
import sys
ti = int(sys.argv[1]) if len(sys.argv) > 1 else 0
cs, tb, g = open(B('charset.bin'),'rb').read(), open(B(f'town{ti}.bin'),'rb').read(), open(B('gen.asm')).read()
tc = [int(v) for v in g.split('tile_char  !byte ')[1].split('\n')[0].split(',')]
tcol = [int(v) & 7 for v in g.split('tile_color !byte ')[1].split('\n')[0].split(',')]
bg = [0, 9, 15]
im = Image.new('RGB', (32 * 16, 25 * 16)); p = im.load()
for ty in range(25):
    for tx in range(32):
        t = tb[ty * 32 + tx]
        for q in range(4):
            for r in range(8):
                b = cs[(tc[t] + q) * 8 + r]
                for i in range(4):
                    v = (b >> (6 - 2 * i)) & 3
                    c = PAL[tcol[t] if v == 3 else bg[v]]
                    x, y = tx * 16 + (q & 1) * 8 + i * 2, ty * 16 + (q >> 1) * 8 + r
                    p[x, y] = c; p[x + 1, y] = c
im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'shots', f'town{ti}_map.png'))
