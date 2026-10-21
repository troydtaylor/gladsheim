#!/usr/bin/env python3
"""Preview overworld art straight from hires.py (TILES + VARIANTS), using the engine's variant hash.
usage: artpreview.py out.png [x0 y0 [w h]] ..."""
import os, sys, importlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import hires
from PIL import Image
PAL=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
g = open(os.path.join(ROOT, 'build', 'gen.asm')).read()
names = g.split('; TILE NAMES ')[1].split('\n')[0].split(',') if '; TILE NAMES ' in g else None
RND = [int(v) for v in g.split('rnd64 !byte ')[1].split('\n')[0].split(',')] if 'rnd64 !byte ' in g else None
def look(name, x, y):
    if name in hires.VARIANTS and RND:
        looks, slots = hires.VARIANTS[name]
        return looks[slots[RND[(x + y * 5) & 63]]]
    return hires.TILES[name]
def cell(px, x0, y0, art):
    fg, bg, rows = art
    for r in range(8):
        for i in range(8):
            px[x0 + i, y0 + r] = PAL[fg] if rows[r][i] == '#' else PAL[bg]
def render(owmap, x0, y0, w=26, h=18):
    im = Image.new('RGB', (w * 8, h * 8)); px = im.load()
    for y in range(h):
        for x in range(w):
            mx, my = x0 + x, y0 + y
            t = owmap[my * 64 + mx] if 0 <= mx < 64 and 0 <= my < 64 else 1
            cell(px, x * 8, y * 8, look(names[t], mx, my))
    return im
if __name__ == '__main__':
    owmap = open(os.path.join(ROOT, 'build', 'owmap.bin'), 'rb').read()
    args = [int(a) for a in sys.argv[2:]] or [20, 12]
    views = [args[i:i + 2] for i in range(0, len(args), 2)]
    ims = [render(owmap, *v) for v in views]
    out = Image.new('RGB', (sum(i.width for i in ims) + 8 * (len(ims) - 1), ims[0].height))
    x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width + 8
    out.resize((out.width * 3, out.height * 3), Image.NEAREST).save(sys.argv[1])
