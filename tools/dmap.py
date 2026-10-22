#!/usr/bin/env python3
"""Player map of dungeon floors, with the way to the important places.
usage: dmap.py out.png floor[,floor...] [title]"""
import os, sys
from collections import deque
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import content as C

def font(n, bold=False):
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf", n)
    except OSError:
        return ImageFont.load_default()

LAB = {'S': ("UP", (255, 255, 255), (70, 130, 200)), 'V': ("DOWN", (255, 255, 255), (160, 40, 160)),
       'K': ("KEY", (0, 0, 0), (250, 210, 60)), 'T': ("CHEST", (0, 0, 0), (230, 150, 40)),
       'D': ("DOOR", (255, 255, 255), (120, 70, 30)), 'Q': ("QUEST", (0, 0, 0), (255, 255, 255)),
       'I': ("SIGN", (255, 255, 255), (110, 110, 60)), 'P': ("RUNE", (0, 0, 0), (200, 200, 90)),
       '1': ("PULL1", (0, 0, 0), (120, 220, 220)), '2': ("PULL2", (0, 0, 0), (120, 220, 220)),
       '3': ("PULL3", (0, 0, 0), (120, 220, 220)), 'X': ("FAKE", (255, 255, 255), (60, 52, 90))}

def bfs(g, a, b):
    prev, q = {a: None}, deque([a])
    while q:
        x, y = q.popleft()
        if (x, y) == b:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in prev and g[n[1]][n[0]] != '#':
                prev[n] = (x, y); q.append(n)
    if b not in prev:
        return []
    p, c = [], b
    while c:
        p.append(c); c = prev[c]
    return p[::-1]

def floor_img(i, CS=34):
    f = C.FLOORS[i]
    g = f["map"]
    pos = lambda ch: [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c == ch]
    S = pos('S')[0]
    goals = pos('K') + pos('T') + pos('V')
    path = set()
    for t in goals:
        path |= set(bfs(g, S, t))
    guards = {k: m for k, (m, n) in f["guards"].items()}
    M, top = 30, 40
    rows = max(y for y, r in enumerate(g) if any(c != '#' for c in r)) + 2
    im = Image.new('RGB', (16 * CS + M + 8, top + rows * CS + 8), (24, 22, 30))
    d = ImageDraw.Draw(im)
    d.text((M, 6), f["name"].upper(), fill=(240, 220, 120), font=font(20, True))
    sm, tiny = font(12), font(10)
    for x in range(16):
        d.text((M + x * CS + CS // 2 - 6, top - 14), str(x), fill=(160, 160, 180), font=sm)
    for y in range(rows):
        d.text((4, top + y * CS + CS // 2 - 7), str(y), fill=(160, 160, 180), font=sm)
        for x in range(16):
            c = g[y][x]
            x0, y0 = M + x * CS, top + y * CS
            bg = (60, 52, 90) if c == '#' else (150, 150, 150)
            if c != '#' and (x, y) in path:
                bg = (120, 190, 120)
            label = None
            if c in LAB:
                label, fg, bg = LAB[c]
                if c == 'X':
                    bg = (150, 150, 150) if (x, y) not in path else (120, 190, 120)
                    fg = (90, 40, 140)
            elif c.islower():
                m = guards.get(c, "?")
                boss = C.MONSTERS[C.MON[m]][12] in ("the ", "")
                label, fg, bg = (m.split()[-1][:6].upper(), (255, 255, 255), (200, 30, 30) if boss else (150, 50, 50))
            d.rectangle([x0, y0, x0 + CS - 1, y0 + CS - 1], fill=bg, outline=(30, 30, 40))
            if label:
                f2 = tiny if len(label) > 4 else sm
                tw = d.textlength(label, font=f2)
                d.text((x0 + (CS - tw) / 2, y0 + CS // 2 - 7), label, fill=fg, font=f2)
    return im

if __name__ == "__main__":
    floors = [int(v) for v in sys.argv[2].split(',')]
    ims = [floor_img(i) for i in floors]
    W = max(900, sum(i.width for i in ims) + 16 * (len(ims) - 1))
    H = max(i.height for i in ims)
    legend = ["Green: the way from the stairs you arrive on to the key, the chest and the stairs down.",
              "X = column, Y = row, as in the side panel. North is up.  Red squares are guardians (bright red: the boss).",
              "QUEST = a side-quest item.  SIGN = an inscription.  RUNE = a rune plate (step on each).  FAKE = an illusory wall: walk through.",
              "PULL1-3 = levers: stand on each and press E, in that order."]
    out = Image.new('RGB', (W, H + 22 * len(legend) + 14), (24, 22, 30))
    x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width + 16
    d = ImageDraw.Draw(out)
    for k, t in enumerate(legend):
        d.text((30, H + 6 + k * 22), t, fill=(220, 220, 230), font=font(13))
    out.save(sys.argv[1])
