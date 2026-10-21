#!/usr/bin/env python3
"""Render build/town<N>.bin with the hires tiles (whole-town preview).  usage: townview.py [town index]"""
import os, sys
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
ti = int(sys.argv[1]) if len(sys.argv) > 1 else 0
tb = open(B(f'town{ti}.bin'), 'rb').read()
im = Image.new('RGB', (32 * 8, 25 * 8)); px = im.load()
for ty in range(25):
    for tx in range(32):
        cell(px, tx * 8, ty * 8, tc[tb[ty * 32 + tx]])
os.makedirs(os.path.join(ROOT, 'shots'), exist_ok=True)
im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(ROOT, 'shots', f'town{ti}_map.png'))
