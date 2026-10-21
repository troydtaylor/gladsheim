#!/usr/bin/env python3
"""Mock up the bitmap-mode screen in Python from hires.py art (real C64 palette and 2-colours-per-cell)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
import hires as H
PAL=[(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),(139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
im = Image.new("RGB", (320 + 64, 200 + 64), (0, 0, 0)); px = im.load()
def cell(cx, cy, rows, fg, bg):
    for y in range(8):
        for x in range(8):
            px[32 + cx * 8 + x, 32 + cy * 8 + y] = PAL[fg if rows[y][x] == '#' else bg]
def text(nx, cy, s, col):
    for i, ch in enumerate(s.upper()):
        g = H.FONT3.get(ch)
        x0 = 32 + (nx + i) * 4
        for y in range(8):
            for x in range(4):
                on = g is not None and y < 7 and x < 3 and g[y][x] == '#'
                if on:
                    px[x0 + x, 32 + cy * 8 + y] = PAL[col]
import random
r = random.Random(3)
names = ["GRASS"] * 6 + ["FOREST"] * 2
world = [[r.choice(names) for _ in range(28)] for _ in range(18)]
for y in range(18):
    for x in range(28):
        if x + y * 0.5 < 7: world[y][x] = "WATER"
        if 18 < x < 26 and 2 < y < 8 and (x + y) % 3: world[y][x] = "MOUNTAIN"
        if y == 10 or x == 14 and y > 10: world[y][x] = "ROAD"
        if x > 20 and y > 12: world[y][x] = "SNOW"
world[9][14] = "PLAYER"; world[11][14] = "ROAD"; world[10][20] = "TOWN"; world[12][6] = "DUNGEON"; world[8][13] = "CASTLE"
world[10][3] = "BRIDGE"; world[10][2] = "BRIDGE"
for y in range(18):
    for x in range(28):
        fg, bg, rows = H.TILES[world[y][x]]
        cell(1 + x, 1 + y, rows, fg, bg)
fg, bg = H.FRAMECOL
for x in range(1, 29):
    cell(x, 0, H.FRAME[64], fg, bg); cell(x, 19, H.FRAME[64], fg, bg)
for y in range(1, 19):
    cell(0, y, H.FRAME[65], fg, bg); cell(29, y, H.FRAME[65], fg, bg)
cell(0, 0, H.FRAME[66], fg, bg); cell(29, 0, H.FRAME[67], fg, bg); cell(0, 19, H.FRAME[68], fg, bg); cell(29, 19, H.FRAME[69], fg, bg)
for x in range(30, 40):
    cell(x, 2, H.FRAME[64], fg, bg)
P = 61
text(P + 3, 1, "GLADSHEIM", 7)
text(P, 4, "PARTY   HP SP LV", 3)
for i, l in enumerate(["ARDEN   28  9  1", "MIRA    16 12  1", "TORVIK  34     1", "SELA    20  8  1"]):
    text(P, 5 + i, l, 1)
text(P, 9, "GOLD", 3); text(P + 11, 9, "   60", 7)
text(P, 10, "LOCATION", 3); text(P, 11, "GLADSHEIM", 1); text(P, 12, "X:30 Y:34", 1)
text(P, 15, "KEYS", 3)
for i, l in enumerate(["WASD/CRSR MOVE", "E  ENTER PLACE", "C SHEET  H HEAL", "V SAVE  L LOAD"]):
    text(P, 16 + i, l, 1)
for i, l in enumerate(["NORTH", "EAST", "WELCOME TO GLADSHEIM, HEROES!", "A CRYPT LIES NEAR. THORNBURY, EAST.", "C SHEET  V SAVE  L LOAD SAVED GAME"]):
    text(2, 20 + i, l, 7 if i == 4 else 1)
out = sys.argv[1] if len(sys.argv) > 1 else "shots/mockup_bitmap.png"
im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(out)
print(out)
