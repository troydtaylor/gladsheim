#!/usr/bin/env python3
"""Tile sheet: every overworld/town tile (hires glyph + colours), each shown as a 3x3 patch."""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
B = lambda f: os.path.join(ROOT, "build", f)
glyphs, g = open(B('glyphs.bin'), 'rb').read(), open(B('gen.asm')).read()
tc = [int(v) for v in g.split('tile_char  !byte ')[1].split('\n')[0].split(',')]
gcol = [int(v) for v in g.split('gcol !byte ')[1].split('\n')[0].split(',')]
def cell(px, x0, y0, code):
    fg, bg = PAL[gcol[code] >> 4], PAL[gcol[code] & 15]
    for r in range(8):
        b = glyphs[code * 8 + r]
        for i in range(8):
            px[x0 + i, y0 + r] = fg if b & (0x80 >> i) else bg
n = len(tc)
im = Image.new('RGB', (n * 28, 24), (40, 40, 40)); px = im.load()
for t in range(n):
    for ty in range(3):
        for tx in range(3):
            cell(px, t * 28 + tx * 8, ty * 8, tc[t])
os.makedirs(os.path.join(ROOT, 'shots'), exist_ok=True)
im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(ROOT, 'shots', 'tiles.png'))
