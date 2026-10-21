#!/usr/bin/env python3
"""
Data generator for the C64 overworld/dungeon prototype.

Produces:
  build/charset.bin   2 KB custom character set (font, frame, overworld tiles, dungeon wall chars)
  build/owmap.bin     64x64 overworld tile map
  build/dmap.bin      16x16 dungeon level
  build/gen.asm       constants, tile tables and the precomputed 3D draw lists
  build/owmap.png     preview of the overworld map (for checking generation)
"""
import os, random
from collections import deque

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
os.makedirs(OUT, exist_ok=True)

charset = bytearray(2048)

def put_hires(code, rows):
    for r, row in enumerate(rows):
        b = 0
        for i, ch in enumerate(row):
            if ch == '#':
                b |= 0x80 >> i
        charset[code * 8 + r] = b

def put_mc(code, rows):
    """rows: 8 strings of 4 fat pixels, values 0..3 ('.'=0)."""
    for r, row in enumerate(rows):
        b = 0
        for i, ch in enumerate(row):
            v = 0 if ch == '.' else int(ch)
            b |= v << (6 - 2 * i)
        charset[code * 8 + r] = b

# ---------------------------------------------------------------- font (screen codes)
FONT = {
 'A': [".###.","#...#","#...#","#####","#...#","#...#","#...#"],
 'B': ["####.","#...#","#...#","####.","#...#","#...#","####."],
 'C': [".###.","#...#","#....","#....","#....","#...#",".###."],
 'D': ["####.","#...#","#...#","#...#","#...#","#...#","####."],
 'E': ["#####","#....","#....","####.","#....","#....","#####"],
 'F': ["#####","#....","#....","####.","#....","#....","#...."],
 'G': [".###.","#...#","#....","#.###","#...#","#...#",".####"],
 'H': ["#...#","#...#","#...#","#####","#...#","#...#","#...#"],
 'I': [".###.","..#..","..#..","..#..","..#..","..#..",".###."],
 'J': ["..###","...#.","...#.","...#.","...#.","#..#.",".##.."],
 'K': ["#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"],
 'L': ["#....","#....","#....","#....","#....","#....","#####"],
 'M': ["#...#","##.##","#.#.#","#.#.#","#...#","#...#","#...#"],
 'N': ["#...#","#...#","##..#","#.#.#","#..##","#...#","#...#"],
 'O': [".###.","#...#","#...#","#...#","#...#","#...#",".###."],
 'P': ["####.","#...#","#...#","####.","#....","#....","#...."],
 'Q': [".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"],
 'R': ["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
 'S': [".###.","#...#","#....",".###.","....#","#...#",".###."],
 'T': ["#####","..#..","..#..","..#..","..#..","..#..","..#.."],
 'U': ["#...#","#...#","#...#","#...#","#...#","#...#",".###."],
 'V': ["#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."],
 'W': ["#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"],
 'X': ["#...#","#...#",".#.#.","..#..",".#.#.","#...#","#...#"],
 'Y': ["#...#","#...#",".#.#.","..#..","..#..","..#..","..#.."],
 'Z': ["#####","....#","...#.","..#..",".#...","#....","#####"],
 '0': [".###.","#...#","#..##","#.#.#","##..#","#...#",".###."],
 '1': ["..#..",".##..","..#..","..#..","..#..","..#..",".###."],
 '2': [".###.","#...#","....#","..##.",".#...","#....","#####"],
 '3': [".###.","#...#","....#","..##.","....#","#...#",".###."],
 '4': ["...#.","..##.",".#.#.","#..#.","#####","...#.","...#."],
 '5': ["#####","#....","####.","....#","....#","#...#",".###."],
 '6': ["..##.",".#...","#....","####.","#...#","#...#",".###."],
 '7': ["#####","....#","...#.","..#..",".#...",".#...",".#..."],
 '8': [".###.","#...#","#...#",".###.","#...#","#...#",".###."],
 '9': [".###.","#...#","#...#",".####","....#","...#.",".##.."],
 '.': [".....",".....",".....",".....",".....",".##..",".##.."],
 ',': [".....",".....",".....",".....",".##..",".##..",".#..."],
 '!': ["..#..","..#..","..#..","..#..","..#..",".....","..#.."],
 '?': [".###.","#...#","....#","..##.","..#..",".....","..#.."],
 ':': [".....",".##..",".##..",".....",".##..",".##..","....."],
 '-': [".....",".....",".....",".###.",".....",".....","....."],
 "'": ["..#..","..#..",".#...",".....",".....",".....","....."],
 '/': ["....#","...#.","...#.","..#..",".#...",".#...","#...."],
 '(': ["...#.","..#..",".#...",".#...",".#...","..#..","...#."],
 ')': [".#...","..#..","...#.","...#.","...#.","..#..",".#..."],
 '>': [".#...","..#..","...#.","....#","...#.","..#..",".#..."],
 '<': ["...#.","..#..",".#...","#....",".#...","..#..","...#."],
 '=': [".....",".....","#####",".....","#####",".....","....."],
 '+': [".....","..#..","..#..","#####","..#..","..#..","....."],
 '*': [".....","#.#.#",".###.","#####",".###.","#.#.#","....."],
 '#': ["#####","#####","#####","#####","#####","#####","#####"],
}

def screencode(ch):
    if 'A' <= ch <= 'Z':
        return ord(ch) - 64
    if ch == '@':
        return 0
    return ord(ch)  # 32..63 map straight across

for ch, rows in FONT.items():
    # bold like the stock C64 font: OR each row with itself shifted right one pixel
    out = []
    for row in rows:
        bits = [c == '#' for c in ("." + row + "..")[:8]]
        bold = [bits[i] or (i > 0 and bits[i - 1]) for i in range(8)]
        out.append("".join('#' if b else '.' for b in bold))
    out.append("........")
    put_hires(screencode(ch), out)

# ---------------------------------------------------------------- frame chars (hires)
CH_HLINE, CH_VLINE, CH_TL, CH_TR, CH_BL, CH_BR, CH_SOLID = 64, 65, 66, 67, 68, 69, 70
put_hires(CH_HLINE, ["........", "........", "########", "........", "########", "........", "........", "........"])
put_hires(CH_VLINE, ["..#.#...", "..#.#...", "..#.#...", "..#.#...", "..#.#...", "..#.#...", "..#.#...", "..#.#..."])
put_hires(CH_TL,    ["........", "........", "..######", "..#.....", "..#.####", "..#.#...", "..#.#...", "..#.#..."])
put_hires(CH_TR,    ["........", "........", "#####...", "....#...", "###.#...", "..#.#...", "..#.#...", "..#.#..."])
put_hires(CH_BL,    ["..#.#...", "..#.#...", "..#.####", "..#.....", "..######", "........", "........", "........"])
put_hires(CH_BR,    ["..#.#...", "..#.#...", "###.#...", "....#...", "#####...", "........", "........", "........"])
put_hires(CH_SOLID, ["########"] * 8)

# ---------------------------------------------------------------- overworld + town tiles (one multicolour char each)
# Each tile is one character: 4 fat pixels x 8 rows (fat pixels are 2 screen pixels wide, so
# a tile is a square 8x8 on screen).  Order matters: maps store tile numbers.
# fat-pixel legend: '.'=bg black  b=$D022 brown  w=$D023 light grey  c=colour RAM (per tile, 0-7)
TILE_BASE = 72
TILES = []  # (name, colorram 0-7, passable, 8 rows of 4 fat px)

def tile(name, color, passable, rows):
    assert len(rows) == 8 and all(len(r) == 4 for r in rows), name
    TILES.append((name, color, passable, rows))

tile("GRASS",    5, True,  ["cccc", "c.cc", "cccc", "ccc.", "cccc", ".ccc", "cccc", "cc.c"])
tile("WATER",    6, False, ["cccc", "wwcc", "cccc", "cccc", "cccc", "ccww", "cccc", "cccc"])
tile("FOREST",   5, True,  [".cc.", "cccc", "cccc", "cccc", ".cc.", ".bb.", ".bb.", "...."])
tile("MOUNTAIN", 5, False, ["cwcc", "wwbc", "wbbc", "wbbb", "bbbb", "bbb.", "bbbb", "cccc"])
tile("TOWN",     2, True,  [".cc.", "cccc", "cccc", "wwww", "wbww", "wbww", "wwww", "...."])
tile("CASTLE",   7, True,  ["c..c", "w..w", "wwww", "w.w.", "wwww", "wbbw", "wbbw", "...."])
tile("DUNGEON",  5, True,  ["cbbc", "bbbb", "bwwb", "w..w", "w..w", "w..w", "w..w", "cccc"])
tile("PLAYER",   3, True,  [".ww.", ".ww.", "cccc", "cccc", ".cc.", "c..c", "b..b", "...."])
tile("ROAD",     5, True,  ["bbbb", "bwbb", "bbbb", "bbbb", "bbwb", "bbbb", "wbbb", "bbbb"])
tile("BRIDGE",   6, True,  ["cccc", "wwww", "bbbb", "b.bb", "bbbb", "bb.b", "wwww", "cccc"])
# ---- towns -------------------------------------------------------------------
tile("COBBLE",   0, True,  ["....", ".b..", "...w", "....", "..b.", "....", "w...", "...."])
tile("WALL",     0, False, ["ww.w", "ww.w", "ww.w", "....", "w.ww", "w.ww", "w.ww", "...."])
tile("FLOOR",    0, True,  ["bbbb", "bb.b", "bbbb", "....", "b.bb", "bbbb", "bbbb", "...."])
tile("DOOR",     7, True,  ["wwww", "wbbw", "wbbw", "wbbw", "wbcw", "wbbw", "wbbw", "wbbw"])
tile("COUNTER",  2, False, ["bbbb", "bbbb", "wwww", "cccc", "c.c.", "cccc", "....", "...."])
tile("SIGN_W",   7, False, ["ww.w", "bbwb", "bbwb", "bbwb", "bccc", "bbcb", "bbbb", "...."])   # sword
tile("SIGN_A",   6, False, ["ww.w", "bccb", "cwwc", "cwwc", "bccb", "bccb", "bbbb", "...."])   # shield
tile("SIGN_P",   1, False, ["ww.w", "bccb", "cbbc", "bccb", "cccc", "bccb", "bccb", "...."])   # ankh
tile("SIGN_T",   7, False, ["ww.w", "wwwb", "cccb", "cccw", "cccb", "cccb", "bbbb", "...."])   # tankard
tile("SIGN_M",   4, False, ["ww.w", "bccb", "cwcc", "cccc", "bccb", "wwww", "bbbb", "...."])   # crystal ball
tile("GUARD",    6, False, ["...w", ".wwb", ".wwb", "cccb", ".ccb", "c.cb", "b.b.", "...."])
tile("FOLK",     4, False, [".bb.", ".ww.", "cccc", "cccc", ".cc.", "c..c", "b..b", "...."])
tile("FOLK2",    5, False, [".ww.", ".ww.", ".cc.", "cccc", "cccc", "cccc", "b..b", "...."])
tile("MERCHANT", 7, False, [".bb.", ".ww.", "cccc", "cccc", "cccc", ".cc.", "b..b", "...."])
tile("FOUNTAIN", 6, False, [".cc.", "c..c", ".ww.", "wwww", "wccw", "wccw", "wwww", "...."])
tile("TABLE",    2, False, ["....", "bbbb", "bcwb", "bbbb", "b..b", "b..b", "....", "...."])
tile("ALTAR",    7, False, ["c..c", "w..w", "wwww", "wccw", "wccw", "wwww", "w..w", "...."])
tile("BED",      2, False, ["bbbb", "bwwb", "bccb", "bccb", "bccb", "bccb", "bbbb", "b..b"])
tile("BARREL",   0, False, [".bb.", "bbbb", "wwww", "bbbb", "bbbb", "wwww", "bbbb", ".bb."])
# ---- regional terrain ----------------------------------------------------------
tile("SNOW",     1, True,  ["wwww", "wcww", "wwww", "wwwc", "wwww", "cwww", "wwww", "wwcw"])
tile("ASH",      2, True,  ["....", ".b..", "...c", "....", "b...", "....", "..b.", "c..."])
tile("DEADWOOD", 2, True,  ["b..b", ".bb.", "..b.", "b.b.", ".bb.", "..b.", "..b.", ".bbb"])
tile("FOLK_IN",  4, False, [".bb.", ".ww.", "cccc", "cccc", ".cc.", "c..c", "b..b", "...."])
tile("FOLK2_IN", 5, False, [".ww.", ".ww.", ".cc.", "cccc", "cccc", "cccc", "b..b", "...."])
tile("BARREL_IN", 0, False, [".bb.", "bbbb", "wwww", "bbbb", "bbbb", "wwww", "bbbb", ".bb."])
tile("HUT",      2, False, ["...b", ".bbb", "bbbb", "wwww", "w..w", "wbbw", "wbbw", "wwww"])

T = {name: i for i, (name, _, _, _) in enumerate(TILES)}
MCODE = {'.': '0', 'b': '1', 'w': '2', 'c': '3'}

def tile_base(t):
    return TILE_BASE + t

for t, (name, col, passable, rows) in enumerate(TILES):
    put_mc(tile_base(t), ["".join(MCODE[c] for c in r) for r in rows])
assert tile_base(len(TILES) - 1) < 128          # 128+ holds the dungeon wall pieces

# ---------------------------------------------------------------- dungeon chars (multicolor)
# dungeon palette: bg black = ceiling, $D022 dark grey = floor/mortar,
#                  $D023 light blue = lit stone, colour RAM blue = wall shade
D_CEIL, D_FLOOR, D_TOPL, D_BOTL, D_TOPR, D_BOTR = 128, 129, 130, 131, 132, 133
D_SIDE, D_SIDE_EL, D_SIDE_ER = 134, 135, 136
D_BRICK = {1: 137, 2: 138, 3: 139}
D_DARK = 140
D_FLOORLN = 141
D_DOOR, D_DOORTOP = 142, 143

def diag(fn):
    rows = []
    for r in range(8):
        y = (r + 0.5) / 8
        row = ""
        for i in range(4):
            x = (2 * i + 1) / 8
            row += fn(x, y)
        rows.append(row)
    return rows

put_mc(D_CEIL,  ["0000"] * 8)
put_mc(D_FLOOR, ["1111"] * 8)
put_mc(D_DARK,  ["0000"] * 8)
put_mc(D_FLOORLN, ["0000"] + ["1111"] * 7)
put_mc(D_DOOR, ["3313"] * 8)
put_mc(D_DOORTOP, ["1111", "1111"] + ["3313"] * 6)
put_mc(D_TOPL, diag(lambda x, y: '3' if y > x else '0'))
put_mc(D_BOTL, diag(lambda x, y: '3' if y < 1 - x else '1'))
put_mc(D_TOPR, diag(lambda x, y: '3' if y > 1 - x else '0'))
put_mc(D_BOTR, diag(lambda x, y: '3' if y < x else '1'))
put_mc(D_SIDE,    ["3333"] * 8)
put_mc(D_SIDE_EL, ["3331"] * 8)
put_mc(D_SIDE_ER, ["1333"] * 8)
put_mc(D_BRICK[1], ["1111", "1222", "1222", "1333", "1111", "2212", "2212", "3313"])
put_mc(D_BRICK[2], ["1111", "1222", "1222", "1222", "1111", "2212", "2212", "2212"])
put_mc(D_BRICK[3], ["1111", "1333", "1333", "1333", "1111", "3313", "3313", "3313"])

# ---------------------------------------------------------------- 3D view geometry
# A 26x18-cell window. Plane d (0 = the viewer, 3 = three cells ahead) spans rows IY[d] .. 18-IY[d]
# and columns IX[d] .. 26-IX[d]; lateral neighbours are offset by the plane's width W[d].
# Walls are rasterised at pixel level: cells a wall fully covers use texture glyphs, cells its
# slanted top/bottom edge crosses get generated glyphs (wall over ceiling, or wall over floor).
WIN_W, WIN_H = 26, 18
WIN = WIN_H
IY = [0, 3, 5, 7]
IX = [0, 4, 7, 10]
W = [WIN_W - 2 * x for x in IX]               # 26, 18, 12, 6
VSCR = 0x0400               # virtual graphics screen (40x25 glyph codes)
VIEW3D_X, VIEW3D_Y = 1, 1   # top-left cell of the dungeon view
PW_, PH_ = WIN_W * 8, WIN_H * 8
GEN_BASE = 144              # generated edge glyphs go here upwards
edge_glyphs = {}            # (bits tuple, fg, bg) -> code
WALL_C, CEIL_C, FLOOR_C = 6, 0, 11

def edge_code(bits, ground):
    key = (bits, WALL_C, ground)
    if key not in edge_glyphs:
        edge_glyphs[key] = GEN_BASE + len(edge_glyphs)
        assert edge_glyphs[key] < 255, "out of glyph codes for the 3D view"
    return edge_glyphs[key]

def side_poly(d, L):
    """pixel test for the corridor-facing side of the cell at depth d, lateral L (L != 0)"""
    if L < 0:
        xa, xb = (IX[d] + (L + 1) * W[d]) * 8, (IX[d + 1] + (L + 1) * W[d + 1]) * 8
    else:
        xa, xb = (IX[d] + L * W[d]) * 8, (IX[d + 1] + L * W[d + 1]) * 8
    ta, tb = IY[d] * 8, IY[d + 1] * 8
    ba, bb = (WIN_H - IY[d]) * 8, (WIN_H - IY[d + 1]) * 8
    lo, hi = min(xa, xb), max(xa, xb)
    def inside(px, py):
        x = px + 0.5
        if not (lo <= x < hi):
            return False
        t = (x - xa) / (xb - xa)
        top = ta + t * (tb - ta)
        bot = ba + t * (bb - ba)
        return top <= py + 0.5 < bot
    far_edge = xb                              # the light seam where this wall meets the next
    return inside, lo, hi, far_edge

def side_face(d, L):
    inside, lo, hi, far = side_poly(d, L)
    cells = []
    c0, c1 = max(0, lo // 8), min(WIN_W, (hi + 7) // 8)
    for c in range(c0, c1):
        for r in range(WIN_H):
            bits = tuple(sum(0x80 >> i for i in range(8) if inside(c * 8 + i, r * 8 + y)) for y in range(8))
            n = sum(bin(b).count("1") for b in bits)
            if n == 0:
                continue
            if n == 64:
                if L < 0 and (c + 1) * 8 == far:
                    code = D_SIDE_EL
                elif L > 0 and c * 8 == far:
                    code = D_SIDE_ER
                else:
                    code = D_SIDE
            else:
                code = edge_code(bits, CEIL_C if r < WIN_H // 2 else FLOOR_C)
            cells.append((r, c, code))
    return cells

def front_face(d, L, door=False):
    u0 = IX[d] + L * W[d]
    c0, c1 = max(u0, 0), min(u0 + W[d], WIN_W)
    if c0 >= c1:
        return None
    h = WIN_H - 2 * IY[d]
    dw, dh = max(2, W[d] // 3), (h * 3) // 4          # the door: a third as wide, 3/4 as tall
    dc0, dr0 = u0 + (W[d] - dw) // 2, IY[d] + h - dh
    cells = []
    for r in range(IY[d], WIN_H - IY[d]):
        for c in range(c0, c1):
            if door and dc0 <= c < dc0 + dw and r >= dr0:
                cells.append((r, c, D_DOORTOP if r == dr0 else D_DOOR))
            else:
                cells.append((r, c, D_BRICK[d]))
    return cells

elements = []   # (forward, lateral, cells, door cells)  -- in back-to-front drawing order
for d in (3, 2, 1):
    for L in (-3, 3, -2, 2, -1, 1, 0):
        cells = front_face(d, L)
        if cells:
            elements.append((d, L, cells, front_face(d, L, door=True)))
    for L in (-2, 2, -1, 1):
        sf = side_face(d - 1, L)
        if sf:
            elements.append((d - 1, L, sf, sf))

def runs(cells):
    """merge into horizontal runs -> bytes lo, hi, length, glyph ... 0,0"""
    grid = {(r, c): ch for r, c, ch in cells}
    out = bytearray()
    for r in range(WIN_H):
        c = 0
        while c < WIN_W:
            if (r, c) in grid:
                v = grid[(r, c)]
                c2 = c
                while c2 + 1 < WIN_W and grid.get((r, c2 + 1)) == v:
                    c2 += 1
                addr = VSCR + (VIEW3D_Y + r) * 40 + VIEW3D_X + c
                out += bytes([addr & 0xFF, addr >> 8, c2 - c + 1, v])
                c = c2 + 1
            else:
                c += 1
    out += b"\x00\x00"
    assert len(out) < 256, len(out)
    return out

FWD = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # N E S W
RIGHT = [(1, 0), (0, 1), (-1, 0), (0, -1)]

# ---------------------------------------------------------------- content
import content as C
import art
import hires

def check_chars(text, where):
    for ch in text.upper():
        assert ch == ' ' or ch in FONT, f"{where}: no glyph for {ch!r} in {text!r}"
    return text

# ---------------------------------------------------------------- dungeon floors
CELL = {'#': 1, '.': 0, 'S': 2, 'T': 3, 'D': 4, 'I': 5, '1': 6, '2': 7, '3': 8,
        'V': 9, 'K': 10, 'P': 11, 'X': 13, 'Q': 14}
GUARDS = []                 # (monster index, count)   cell value = $80 | index

def floor_check(f):
    rows = f["map"]
    name = f["name"]
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), name
    S = [(x, y) for y in range(16) for x in range(16) if rows[y][x] == 'S']
    assert len(S) == 1, f"{name}: needs exactly one S"
    def reach(door_open):
        seen, q = {S[0]}, deque([S[0]])
        while q:
            x, y = q.popleft()
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + ddx, y + ddy)
                c = rows[n[1]][n[0]]
                if n in seen or c == '#' or (c == 'D' and not door_open):
                    continue
                seen.add(n); q.append(n)
        return seen
    closed, opened = reach(False), reach(True)
    pos = lambda ch: [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ch]
    assert len(pos('Q')) == (f["index"] in C.QITEMS), f"{name}: quest item mismatch"
    for ch in "I123KPQ":
        for p in pos(ch):
            assert p in closed, f"{name}: {ch} at {p} unreachable before the door"
    if pos('D'):
        behind = [p for p in pos('T') + pos('V') if p not in closed]
        assert behind, f"{name}: door guards nothing"
        assert all(p in opened for p in behind)
    for p in pos('T') + pos('V'):
        assert p in opened, f"{name}: {p} unreachable"
    if f["puzzle"] == C.P_LEVER:
        assert sorted(ch for r in rows for ch in r if ch in "123") == ['1', '2', '3'], name
    if f["puzzle"] == C.P_PLATES:
        assert pos('P'), name
    for ch in set(c for r in rows for c in r if c.islower()):
        assert ch in f["guards"], f"{name}: undeclared guardian {ch}"
    # a boss must stand on the only way to its treasure
    bosses = [k for k, (m, _) in f["guards"].items() if C.MONSTERS[C.MON[m]][12] in ("the ", "")]
    if bosses and pos('T'):
        seen, q = {S[0]}, deque([S[0]])
        while q:
            x, y = q.popleft()
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + ddx, y + ddy)
                c = rows[n[1]][n[0]]
                if n in seen or c == '#' or c in bosses:
                    continue
                seen.add(n); q.append(n)
        assert not any(p in seen for p in pos('T')), f"{name}: the boss can be walked around"

levels_bin = []
for i, f in enumerate(C.FLOORS):
    f["index"] = i
    floor_check(f)
    gidx = {}
    for letter, (mname, count) in f["guards"].items():
        GUARDS.append((C.MON[mname], count))
        gidx[letter] = len(GUARDS) - 1
    b = bytearray()
    for r in f["map"]:
        for ch in r:
            b.append(0x80 | gidx[ch] if ch.islower() else CELL[ch])
    levels_bin.append(b)
assert len(GUARDS) < 128

# a key in a dungeon must sit above (or on) a floor that needs it
for d, (dname, _, floors, _) in enumerate(C.DUNGEONS):
    keyf = [i for i in floors if any('K' in r for r in C.FLOORS[i]["map"])]
    needf = [i for i in floors if C.FLOORS[i]["puzzle"] == C.P_KEY]
    for n in needf:
        assert keyf and min(keyf) <= n, f"{dname}: key door without a key above it"

# ---------------------------------------------------------------- overworld map
rng = random.Random(1984)
N = 64

def value_noise(cells, seed):
    r = random.Random(seed)
    g = [[r.random() for _ in range(cells + 1)] for _ in range(cells + 1)]
    out = [[0.0] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            fx, fy = x / N * cells, y / N * cells
            ix, iy = int(fx), int(fy)
            tx, ty = fx - ix, fy - iy
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[iy][ix] * (1 - tx) + g[iy][ix + 1] * tx
            b = g[iy + 1][ix] * (1 - tx) + g[iy + 1][ix + 1] * tx
            out[y][x] = a * (1 - ty) + b * ty
    return out

h1, h2, h3 = value_noise(6, 11), value_noise(13, 12), value_noise(9, 13)
world = [[0] * N for _ in range(N)]
CX, CY = 30, 33                                          # heart of the home lands
for y in range(N):
    for x in range(N):
        e = 0.6 * h1[y][x] + 0.4 * h2[y][x]
        dxc, dyc = (x - 31.5) / 32, (y - 31.5) / 32
        e -= 0.42 * (dxc * dxc + dyc * dyc) ** 2         # land almost to the edges
        e += 0.08 * max(0.0, 1 - ((x - CX) ** 2 + (y - CY) ** 2) / 150)   # solid ground at home
        m = h3[y][x] + (0.12 if (x < 28 and y > 34) else 0)              # thick south-west woods
        if e < 0.30:
            t = T["WATER"]
        elif e > 0.64:
            t = T["MOUNTAIN"]
        elif m > 0.58:
            t = T["FOREST"]
        else:
            t = T["GRASS"]
        world[y][x] = t
for i in range(N):  # ocean rim
    for j in (0, 1, N - 2, N - 1):
        world[i][j] = world[j][i] = T["WATER"]

def walkable(t):
    return TILES[t][2]

def bfs_ow(start, ok):
    dist, prev = {start: 0}, {}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + ddx, y + ddy
            if 0 <= nx < N and 0 <= ny < N and (nx, ny) not in dist and ok(world[ny][nx]):
                dist[(nx, ny)] = dist[(x, y)] + 1
                prev[(nx, ny)] = (x, y)
                q.append((nx, ny))
    return dist, prev

grass = [(x, y) for y in range(N) for x in range(N) if world[y][x] == T["GRASS"]]
best = None
for g0 in sorted(grass, key=lambda p: (p[0] - CX) ** 2 + (p[1] - CY) ** 2)[:40]:
    n = len(bfs_ow(g0, walkable)[0])
    if best is None or n > best[0]:
        best = (n, g0)
castle = best[1]
dist, _ = bfs_ow(castle, walkable)
far = max(dist.values())

world[castle[1]][castle[0]] = T["CASTLE"]

def near(x, y, tile_name, r=1):
    return any(0 <= x + i < N and 0 <= y + j < N and world[y + j][x + i] == T[tile_name]
               for i in range(-r, r + 1) for j in range(-r, r + 1))

taken = []
def pick(lo, hi, cond=lambda x, y: True, order="random"):
    """a grass site lo..hi steps from the castle, well away from other sites"""
    for spread in (12, 10, 8, 6):
        cands = sorted((x, y) for (x, y), d in dist.items()
                       if lo <= d <= hi and world[y][x] == T["GRASS"] and cond(x, y)
                       and all(abs(x - p) + abs(y - q) > spread for p, q in taken))
        if cands:
            break
    assert cands, f"no site {lo}-{hi}"
    c = max(cands, key=lambda p: dist[p]) if order == "far" else rng.choice(cands)
    taken.append(c)
    return c

f = far
sites = {}
sites["crypt"] = pick(5, 10, lambda x, y: near(x, y, "MOUNTAIN", 2))
sites["thornbury"] = pick(8, 14, lambda x, y: not near(x, y, "MOUNTAIN", 1))
sites["sunken"] = pick(int(f * .28), int(f * .42), lambda x, y: near(x, y, "WATER", 2))
sites["webwood"] = pick(int(f * .40), int(f * .55), lambda x, y: near(x, y, "FOREST", 1))
sites["frozen"] = pick(int(f * .55), int(f * .70), lambda x, y: near(x, y, "MOUNTAIN", 2))
sites["obsidian"] = pick(int(f * .75), int(f * .88))
sites["vaults"] = pick(int(f * .88), f, order="far")
ox, oy = sites["obsidian"]
sites["ravenmoor"] = pick(int(f * .50), int(f * .74),
                          lambda x, y: 8 < abs(x - ox) + abs(y - oy) < 22)
sites["hut"] = pick(int(f * .30), int(f * .50), lambda x, y: near(x, y, "FOREST", 1) and not near(x, y, "ROAD", 2))

def paint(center, radius, mapping):
    cx, cy = center
    for (x, y) in dist:
        if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius and world[y][x] in mapping:
            world[y][x] = mapping[world[y][x]]

paint(sites["frozen"], 8, {T["GRASS"]: T["SNOW"]})
dark = {T["GRASS"]: T["ASH"], T["FOREST"]: T["DEADWOOD"]}
paint(sites["obsidian"], 9, dark)
paint(sites["vaults"], 10, dark)
paint(sites["webwood"], 5, {T["GRASS"]: T["FOREST"]})
for k in ("frozen", "obsidian", "vaults", "webwood"):     # keep the doorstep clear
    x, y = sites[k]
    world[y][x] = T["GRASS"]

for k in ("crypt", "sunken", "webwood", "frozen", "obsidian", "vaults"):
    x, y = sites[k]
    world[y][x] = T["DUNGEON"]
for k in ("thornbury", "ravenmoor"):
    x, y = sites[k]
    world[y][x] = T["TOWN"]
world[sites["hut"][1]][sites["hut"][0]] = T["HUT"]

def lay_road(a, b):
    import heapq
    cost, prev, pq = {a: 0}, {}, [(0, a)]
    while pq:
        c, (x, y) = heapq.heappop(pq)
        if (x, y) == b:
            break
        if c > cost[(x, y)]:
            continue
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + ddx, y + ddy
            if not (2 <= nx < N - 2 and 2 <= ny < N - 2):
                continue
            t = world[ny][nx]
            step = {T["MOUNTAIN"]: None, T["WATER"]: 8, T["FOREST"]: 3, T["DEADWOOD"]: 3}.get(t, 1)
            if t == T["ROAD"]:
                step = 0.5
            if t == T["HUT"] or t in (T["DUNGEON"], T["TOWN"], T["CASTLE"]) and (nx, ny) != b:
                step = None
            if step is None:
                continue
            nc = c + step
            if nc < cost.get((nx, ny), 1e9):
                cost[(nx, ny)] = nc
                prev[(nx, ny)] = (x, y)
                heapq.heappush(pq, (nc, (nx, ny)))
    p = prev[b]
    while p != a:
        x, y = p
        if world[y][x] == T["WATER"]:
            world[y][x] = T["BRIDGE"]
        elif world[y][x] in (T["GRASS"], T["FOREST"], T["SNOW"], T["ASH"], T["DEADWOOD"]):
            world[y][x] = T["ROAD"]
        p = prev[p]

for a, b in (("castle", "thornbury"), ("castle", "crypt"), ("thornbury", "sunken"),
             ("castle", "webwood"), ("castle", "frozen"), ("thornbury", "ravenmoor"),
             ("ravenmoor", "obsidian")):
    lay_road(castle if a == "castle" else sites[a], sites[b])

start = None
for ddx, ddy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
    x, y = castle[0] + ddx, castle[1] + ddy
    if walkable(world[y][x]) and world[y][x] not in (T["DUNGEON"], T["TOWN"]):
        start = (x, y)
        break
assert start
d_all, _ = bfs_ow(start, walkable)
for k, p in sites.items():
    if k == "hut":                      # the hut is bumped into, from any side
        assert any((p[0] + a, p[1] + b) in d_all for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))), "hut"
    else:
        assert p in d_all, f"{k} unreachable on the overworld"
owmap = bytearray(world[y][x] for y in range(N) for x in range(N))

PLACES = [  # (site, kind 0 dungeon / 1 town, index)
    ("crypt", 0, 0), ("sunken", 0, 1), ("webwood", 0, 2), ("frozen", 0, 3),
    ("obsidian", 0, 4), ("vaults", 0, 5), ("thornbury", 1, 0), ("ravenmoor", 1, 1)]

# ---------------------------------------------------------------- towns
TW, TH = 32, 25

PEOPLE = {T[n] for n in ("GUARD", "FOLK", "FOLK2", "FOLK_IN", "FOLK2_IN")}

class Town:
    def __init__(self):
        self.m = [[T["COBBLE"]] * TW for _ in range(TH)]
        for x in range(TW):
            self.m[0][x] = self.m[TH - 1][x] = T["WALL"]
        for y in range(TH):
            self.m[y][0] = self.m[y][TW - 1] = T["WALL"]
        self.m[TH - 1][15] = self.m[TH - 1][16] = T["COBBLE"]
        self.shops, self.npcs, self.start = [], [], (15, 23)

    def put(self, x, y, name):
        if self.m[y][x] == T["FLOOR"] and f"{name}_IN" in T:
            name = f"{name}_IN"                 # drawn on wood instead of cobblestone
        self.m[y][x] = T[name]

    def building(self, x0, y0, x1, y1, door, sign_at, sign_tile):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.m[y][x] = T["WALL"] if x in (x0, x1) or y in (y0, y1) else T["FLOOR"]
        self.put(door[0], door[1], "DOOR")
        self.put(sign_at[0], sign_at[1], sign_tile)
        self.shops.append((x0, y0, x1, y1))

    def check(self, name):
        passable = lambda t: TILES[t][2]
        seen, q = {self.start}, deque([self.start])
        while q:
            x, y = q.popleft()
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ddx, y + ddy
                if 0 <= nx < TW and 0 <= ny < TH and (nx, ny) not in seen and passable(self.m[ny][nx]):
                    seen.add((nx, ny)); q.append((nx, ny))
        nb = lambda x, y: any((x + a, y + b) in seen for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        for i, (x0, y0, x1, y1) in enumerate(self.shops):
            assert any(self.m[y][x] in (T["COUNTER"], T["ALTAR"]) and nb(x, y)
                       for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)), f"{name}: shop {i} unreachable"
        for x, y in self.npcs:
            assert nb(x, y), f"{name}: npc at {(x, y)} unreachable"
            assert self.m[y][x] in PEOPLE, f"{name}: npc at {(x, y)} is not a person"
        assert (15, TH - 1) in seen, f"{name}: gate unreachable"

    def bin(self):
        b = bytearray(32 * 32)
        for y in range(32):
            for x in range(32):
                b[y * 32 + x] = self.m[y][x] if y < TH else T["GRASS"]
        return b

def thornbury(t, people):
    t.building(2, 2, 9, 7, (5, 7), (4, 7), "SIGN_W")
    for x in range(3, 9): t.put(x, 4, "COUNTER")
    t.put(5, 3, "MERCHANT"); t.put(8, 3, "BARREL")
    t.building(11, 2, 18, 7, (14, 7), (13, 7), "SIGN_A")
    for x in range(12, 18): t.put(x, 4, "COUNTER")
    t.put(14, 3, "MERCHANT"); t.put(12, 3, "BARREL")
    t.building(21, 2, 29, 8, (25, 8), (24, 8), "SIGN_P")
    for x in range(24, 27): t.put(x, 4, "ALTAR")
    t.put(25, 3, "MERCHANT")
    t.building(2, 15, 13, 22, (7, 15), (6, 15), "SIGN_T")
    for x in range(3, 7): t.put(x, 18, "COUNTER")
    t.put(4, 19, "MERCHANT"); t.put(3, 21, "BARREL"); t.put(6, 21, "BARREL")
    t.put(9, 18, "TABLE"); t.put(9, 21, "TABLE")
    for y in (17, 19, 21): t.put(12, y, "BED")
    t.building(19, 15, 27, 21, (23, 15), (22, 15), "SIGN_M")
    for x in range(20, 27): t.put(x, 18, "COUNTER")
    t.put(23, 19, "MERCHANT"); t.put(20, 20, "BARREL")
    t.put(15, 11, "FOUNTAIN")
    for x, y in ((1, 9), (30, 9), (1, 14), (10, 13), (20, 12), (30, 14), (30, 22), (29, 23), (1, 23)):
        t.put(x, y, "FOREST")
    for x, y in ((10, 9), (19, 9), (18, 13)):
        t.put(x, y, "BARREL")
    for (x, y), (tile_name, _) in zip([(14, 22), (17, 22), (13, 11), (19, 11), (25, 10), (8, 20),
                                       (24, 13), (7, 9), (10, 17)], people):
        t.put(x, y, tile_name); t.npcs.append((x, y))

def ravenmoor(t, people):
    # west row: doors face east onto the high street; east row: doors face west
    t.building(2, 2, 11, 7, (11, 4), (11, 5), "SIGN_W")
    for y in range(3, 7): t.put(5, y, "COUNTER")
    t.put(4, 4, "MERCHANT"); t.put(3, 6, "BARREL")
    t.building(2, 9, 11, 14, (11, 11), (11, 12), "SIGN_A")
    for y in range(10, 14): t.put(5, y, "COUNTER")
    t.put(4, 11, "MERCHANT"); t.put(3, 13, "BARREL")
    t.building(2, 16, 11, 22, (11, 18), (11, 19), "SIGN_T")
    for y in range(17, 21): t.put(5, y, "COUNTER")
    t.put(4, 18, "MERCHANT"); t.put(8, 21, "TABLE"); t.put(9, 17, "TABLE")
    t.put(3, 21, "BED"); t.put(4, 21, "BED")
    t.building(20, 2, 29, 8, (20, 5), (20, 6), "SIGN_P")
    for y in range(4, 7): t.put(26, y, "ALTAR")
    t.put(27, 5, "MERCHANT")
    t.building(20, 10, 29, 16, (20, 13), (20, 14), "SIGN_M")
    for y in range(11, 16): t.put(26, y, "COUNTER")
    t.put(27, 13, "MERCHANT"); t.put(28, 15, "BARREL")
    t.put(15, 11, "FOUNTAIN")
    for x, y in ((14, 3), (17, 3), (14, 7), (17, 7), (21, 19), (27, 19), (21, 22), (27, 22)):
        t.put(x, y, "DEADWOOD" if (x + y) % 2 else "FOREST")
    for x, y in ((13, 16), (18, 16), (24, 20)):
        t.put(x, y, "BARREL")
    for (x, y), (tile_name, _) in zip([(14, 22), (13, 12), (18, 9), (17, 16), (8, 19), (16, 4), (24, 19)],
                                      people):
        t.put(x, y, tile_name); t.npcs.append((x, y))

TOWNS = []
for spec in C.TOWNS:
    t = Town()
    {"thornbury": thornbury, "ravenmoor": ravenmoor}[spec["layout"]](t, spec["npcs"])
    assert len(t.shops) == 5 and len(t.npcs) == len(spec["npcs"]), spec["name"]
    t.check(spec["name"])
    TOWNS.append(t)
TOWN_PAGES = [0x50, 0x54]

# ---------------------------------------------------------------- monster sprites
sprites = bytearray()
SPV = {'.': 0, 'a': 1, 'c': 2, 'b': 3}
for img in art.IMAGES:
    assert len(img) == 42 and all(len(r) == 24 for r in img)
    for sy in (0, 1):
        for sx in (0, 1):
            blk = bytearray()
            for r in range(21):
                row = img[sy * 21 + r][sx * 12:(sx + 1) * 12]
                for byte in range(3):
                    v = 0
                    for i in range(4):
                        v |= SPV[row[byte * 4 + i]] << (6 - 2 * i)
                    blk.append(v)
            blk.append(0)
            sprites += blk

# ---------------------------------------------------------------- hires glyphs for the bitmap renderer
glyphs = bytearray(2048)
gcol = bytearray(256)                       # per glyph: fg << 4 | bg
def put_glyph(code, rows, fg, bg):
    assert len(rows) == 8 and all(len(r) == 8 for r in rows), code
    for r, row in enumerate(rows):
        glyphs[code * 8 + r] = sum(0x80 >> i for i, ch in enumerate(row) if ch == '#')
    gcol[code] = (fg << 4) | bg
for code, rows in hires.FRAME.items():
    put_glyph(code, rows, *hires.FRAMECOL)
for t, (name, _, _, _) in enumerate(TILES):
    fg, bg, rows = hires.TILES[name]
    put_glyph(tile_base(t), rows, fg, bg)
# terrain variants: look 0 replaces the tile's own glyph, the others go to codes 107-127.
# The engine picks vtab[tvar[t] + rnd64[(x + 5y) & 63]] for tiles whose tvar is not 0.
VAR_BASE = tile_base(len(TILES))
tvar = [0] * len(TILES)
vtab = [0] * 8                                # offset 0 = "no variants"
next_code = VAR_BASE
for name, (looks, slots) in hires.VARIANTS.items():
    t = T[name]
    bg0 = looks[0][1]
    codes = [tile_base(t)]
    for i, (fg, bg, rows) in enumerate(looks):
        assert bg == bg0, f"{name}: every look needs the same ground colour (the party stands on it)"
        if i:
            codes.append(next_code)
            next_code += 1
        put_glyph(codes[i], rows, fg, bg)
    assert len(slots) == 8
    tvar[t] = len(vtab)
    vtab += [codes[k] for k in slots]
assert next_code <= 128, f"terrain variants overflow into the dungeon glyphs ({next_code})"
_r = random.Random(64)
rnd64 = [_r.randrange(8) for _ in range(64)]
for code, (_, (fg, bg), rows) in hires.DUNGEON.items():
    put_glyph(code, rows, fg, bg)
for (bits, fg, bg), code in edge_glyphs.items():
    put_glyph(code, ["".join('#' if b & (0x80 >> i) else '.' for i in range(8)) for b in bits], fg, bg)
assert D_CEIL == 128 and D_DOORTOP == 143

for ch, rows in FONT.items():                # thin 5x7 letters, 1-pixel margin
    rows8 = ["." + r + ".." for r in rows] + ["........"]
    put_glyph(screencode(ch), rows8, 1, 0)

# ---------------------------------------------------------------- write binaries
open(os.path.join(OUT, "glyphs.bin"), "wb").write(glyphs)

open(os.path.join(OUT, "owmap.bin"), "wb").write(owmap)
open(os.path.join(OUT, "sprites.bin"), "wb").write(sprites)
for i, t in enumerate(TOWNS):
    open(os.path.join(OUT, f"town{i}.bin"), "wb").write(t.bin())

# ---------------------------------------------------------------- gen.asm
L = ["; generated by gen.py from content.py -- do not edit"]
def A(s):
    L.append(s)
def byts(label, vals):
    vals = list(vals)
    A(f"{label} !byte " + ",".join(str(v) for v in vals) if vals else f"{label}")
def ptrs(label, names):
    A(f"{label}_lo !byte " + ",".join("<" + n for n in names))
    A(f"{label}_hi !byte " + ",".join(">" + n for n in names))
STRS = {}
def S(text, width=38):
    """emit a $ff-terminated screen-code string once; returns its label"""
    check_chars(text, "text")
    assert len(text) <= width, f"too long ({len(text)}>{width}): {text!r}"
    if text not in STRS:
        STRS[text] = f"str{len(STRS)}"
    return STRS[text]
def pad16(text):
    return text + " " * (16 - len(text))

A(f"CH_HLINE = {CH_HLINE}\nCH_VLINE = {CH_VLINE}\nCH_TL = {CH_TL}\nCH_TR = {CH_TR}\nCH_BL = {CH_BL}\nCH_BR = {CH_BR}\nCH_SOLID = {CH_SOLID}")
A(f"D_CEIL = {D_CEIL}\nD_FLOOR = {D_FLOOR}\nD_DARK = {D_DARK}\nD_FLOORLN = {D_FLOORLN}")
A(f"WIN = {WIN}\nWIN_W = {WIN_W}\nWIN_H = {WIN_H}\nVIEW3D_X = {VIEW3D_X}\nVIEW3D_Y = {VIEW3D_Y}")
for name, t in T.items():
    A(f"T_{name} = {t}")
A(f"NUM_TILES = {len(TILES)}\nTILE_BASE = {TILE_BASE}")
A(f"START_X = {start[0]}\nSTART_Y = {start[1]}")
A(f"TOWN_H = {TH}\nNUM_TOWNS = {len(TOWNS)}\nNUM_PLACES = {len(PLACES)}")
A(f"NUM_DUNGEONS = {len(C.DUNGEONS)}\nNUM_LEVELS = {len(C.FLOORS)}\nNUM_MON = {len(C.MONSTERS)}")
A(f"P_NONE = {C.P_NONE}\nP_RIDDLE = {C.P_RIDDLE}\nP_LEVER = {C.P_LEVER}\nP_KEY = {C.P_KEY}\nP_PLATES = {C.P_PLATES}")
for k in ("E_WEAPON", "E_ARMOR", "E_ALE", "E_ROOM", "E_RAISE", "E_CURE", "E_TOME", "E_MANA", "E_BLESS"):
    A(f"{k} = {getattr(C, k)}")
A(f"CASTLE_X = {castle[0]}\nCASTLE_Y = {castle[1]}")
A("tile_char  !byte " + ",".join(str(tile_base(t)) for t in range(len(TILES))))
A("gcol !byte " + ",".join(str(v) for v in gcol))
A("tvar !byte " + ",".join(str(v) for v in tvar))
A("vtab !byte " + ",".join(str(v) for v in vtab))
A("rnd64 !byte " + ",".join(str(v) for v in rnd64))
A("; TILE NAMES " + ",".join(n for n, _, _, _ in TILES))
A("tile_pass  !byte " + ",".join("1" if p else "0" for _, _, p, _ in TILES))

# places
byts("place_x", (sites[s][0] for s, _, _ in PLACES))
byts("place_y", (sites[s][1] for s, _, _ in PLACES))
byts("place_kind", (k for _, k, _ in PLACES))
byts("place_idx", (i for _, _, i in PLACES))

# dungeons
byts("dg_first", (fl[0] for _, _, fl, _ in C.DUNGEONS))
byts("dg_need", (need for _, _, _, need in C.DUNGEONS))
ptrs("dg_msg", [S(msg) for _, msg, _, _ in C.DUNGEONS])

# levels
ptrs("lvl_src", [f"lvl_data{i}" for i in range(len(C.FLOORS))])
byts("lvl_save_hi", (0xB4 + i for i in range(len(C.FLOORS))))
dg_of = {}
for d, (_, _, fl, _) in enumerate(C.DUNGEONS):
    for i in fl:
        dg_of[i] = d
byts("lvl_dungeon", (dg_of[i] for i in range(len(C.FLOORS))))
byts("lvl_top", (1 if C.DUNGEONS[dg_of[i]][2][0] == i else 0 for i in range(len(C.FLOORS))))
ptrs("lvl_name", [S(pad16(f["name"]), 16) for f in C.FLOORS])
ptrs("lvl_short", [S(f["short"], 12) for f in C.FLOORS])
byts("lvl_rnd", (C.MON[m] for f in C.FLOORS for m in f["rnd"]))
byts("lvl_puzzle", (f["puzzle"] for f in C.FLOORS))
ptrs("lvl_ans", [S(f.get("answer") or "-", 10) for f in C.FLOORS])
byts("lvl_anslen", (len(f.get("answer", "")) for f in C.FLOORS))
ptrs("lvl_door1", [S(f["door"][0] or "a locked door.") for f in C.FLOORS])
ptrs("lvl_door2", [S(f["door"][1] or "it will not open.") for f in C.FLOORS])
ptrs("lvl_insc1", [S(f["insc"][0] or "-") for f in C.FLOORS])
ptrs("lvl_insc2", [S(f["insc"][1] or "-") for f in C.FLOORS])
byts("lvl_cgold_lo", (f["chest"][0] & 255 for f in C.FLOORS))
byts("lvl_cgold_hi", (f["chest"][0] >> 8 for f in C.FLOORS))
ptrs("lvl_chest1", [S(f["chest"][1] or "an empty chest.") for f in C.FLOORS])
ptrs("lvl_chest2", [S(f["chest"][2] or "-") for f in C.FLOORS])
byts("lvl_sigil", (f["chest"][3] for f in C.FLOORS))
byts("lvl_win", (f["chest"][4] for f in C.FLOORS))
byts("guard_type", (m for m, _ in GUARDS))
byts("guard_count", (n for _, n in GUARDS))

# monsters
M = C.MONSTERS
byts("mon_hp", (m[2] for m in M))
byts("mon_dmg", (m[3] for m in M))
byts("mon_hit", (m[4] for m in M))
byts("mon_gold_lo", (m[5] & 255 for m in M))
byts("mon_gold_hi", (m[5] >> 8 for m in M))
byts("mon_xp_lo", (m[6] & 255 for m in M))
byts("mon_xp_hi", (m[6] >> 8 for m in M))
byts("mon_img", (art.IMG[m[7]] for m in M))
byts("mon_col", (m[8] for m in M))
byts("mon_mc1", (m[9] for m in M))
byts("mon_mc2", (m[10] for m in M))
byts("mon_grp", (m[11] for m in M))
ptrs("mname", [S(m[0], 16) for m in M])
ptrs("mplur", [S(m[1], 16) for m in M])
ptrs("mart", [S(m[12] or "", 4) for m in M])
byts("mon_hits", (m[13] for m in M))
byts("mon_def", (m[14] for m in M))
byts("xp_lo", (v & 255 for v in C.XP_TABLE))
byts("xp_hi", (v >> 8 for v in C.XP_TABLE))

# towns
byts("town_page", TOWN_PAGES[:len(TOWNS)])
byts("town_sx", (t.start[0] for t in TOWNS))
byts("town_sy", (t.start[1] for t in TOWNS))
ptrs("town_name", [S(pad16(spec["name"]), 16) for spec in C.TOWNS])
ptrs("town_short", [S(spec["name"], 12) for spec in C.TOWNS])
ptrs("town_wel", [S(f"welcome to {spec['name']}!") for spec in C.TOWNS])
ptrs("town_ent", [S(f"the town of {spec['name']}. (e)nter?") for spec in C.TOWNS])
ptrs("town_bye", [S(f"you leave {spec['name']}.") for spec in C.TOWNS])
npc_first, allnpc = [], []
for ti, (t, spec) in enumerate(zip(TOWNS, C.TOWNS)):
    npc_first.append(len(allnpc))
    for (x, y), (_, pages) in zip(t.npcs, spec["npcs"]):
        allnpc.append((x, y, pages))
A(f"HERMIT_NPC = {len(allnpc)}\nHUT_X = {sites['hut'][0]}\nHUT_Y = {sites['hut'][1]}")
allnpc.append((sites["hut"][0], sites["hut"][1], C.HERMIT[1]))
byts("town_npc_first", npc_first)
byts("town_npc_count", (len(t.npcs) for t in TOWNS))
byts("npc_x", (n[0] for n in allnpc))
byts("npc_y", (n[1] for n in allnpc))
ptrs("rumor", [S(r) for spec in C.TOWNS for r in spec["rumors"]])
assert all(len(spec["rumors"]) == 8 for spec in C.TOWNS)
shops = [(ti, s) for ti, spec in enumerate(C.TOWNS) for s in spec["shops"]]
for k, i in (("x0", 0), ("y0", 1), ("x1", 2), ("y1", 3)):
    byts(f"shop_{k}", (TOWNS[ti].shops[j % 5][i] for j, (ti, _) in enumerate(shops)))
ptrs("sname", [S(s[0], 20) for _, s in shops])
ptrs("squote", [S(s[1], 20) for _, s in shops])
ptrs("sign", [S(s[2]) for _, s in shops])
ptrs("greet", [S(s[3]) for _, s in shops])
items = [it for _, s in shops for it in s[4]]
assert len(items) == len(shops) * 4
ptrs("it_name", [S(it[0] or "-", 11) for it in items])
byts("it_stat", (it[1] for it in items))
byts("it_price_lo", (it[2] & 255 for it in items))
byts("it_price_hi", (it[2] >> 8 for it in items))
byts("it_eff", (it[3] for it in items))
byts("it_par", (it[4] for it in items))

# 3D view geometry
for i, (d, Lat, cells, dcells) in enumerate(elements):
    A(f"elem{i}: ; forward {d}, lateral {Lat:+d}")
    A("  !byte " + ",".join(f"${b:02x}" for b in runs(cells)))
    if dcells is not cells:
        A(f"door{i}:")
        A("  !byte " + ",".join(f"${b:02x}" for b in runs(dcells)))
A(f"NUM_ELEM = {len(elements)}")
ptrs("elem", [f"elem{i}" for i in range(len(elements))])
ptrs("door", [f"door{i}" if e[3] is not e[2] else f"elem{i}" for i, e in enumerate(elements)])
dxs, dys = [], []
for dr in range(4):
    for d, Lat, _, _ in elements:
        dxs.append((d * FWD[dr][0] + Lat * RIGHT[dr][0]) & 0xFF)
        dys.append((d * FWD[dr][1] + Lat * RIGHT[dr][1]) & 0xFF)
A("elem_dx !byte " + ",".join(f"${v:02x}" for v in dxs))
A("elem_dy !byte " + ",".join(f"${v:02x}" for v in dys))
A("dir_base !byte " + ",".join(str(dr * len(elements)) for dr in range(4)))
A("fwd_dx !byte " + ",".join(f"${v & 0xFF:02x}" for v, _ in FWD))
A("fwd_dy !byte " + ",".join(f"${v & 0xFF:02x}" for _, v in FWD))

# level data (pristine)
for i, b in enumerate(levels_bin):
    A(f"lvl_data{i}")
    for k in range(0, 256, 32):
        A("  !byte " + ",".join(f"${v:02x}" for v in b[k:k + 32]))

# all strings
for text, label in STRS.items():
    A(f'{label} !scr "{text.lower()}" : !byte $ff' if text else f"{label} !byte $ff")
open(os.path.join(OUT, "gen.asm"), "w").write("\n".join(L) + "\n")

# ---------------------------------------------------------------- people, quests, story -> build/quests.asm
# text at $2C00-$37FF, tables at $5C00-$5FFF (both free RAM inside the loaded file)
QL, QSTR = [], {}
def QS(text, width=38):
    check_chars(text, "quest text")
    assert len(text) <= width, f"too long ({len(text)}>{width}): {text!r}"
    if text not in QSTR:
        QSTR[text] = f"qstr{len(QSTR)}"
    return QSTR[text]
COND = {"q": 1, "runes": 2, "sigil": 3}
OPS = {"setq": 1, "gold": 2, "xp": 3, "weapon": 4, "bonus": 5}
pages, lines, acts, npc_pg, npc_np = [], [], [], [], []
for _, _, plist in allnpc:
    npc_pg.append(len(pages))
    npc_np.append(len(plist))
    assert plist and not plist[-1][0], "a person's last page must have no conditions"
    for when, text, do in plist:
        cs = [(COND[c[0]], c[1], c[2]) for c in when] + [(0, 0, 0)] * (2 - len(when))
        pages.append((cs, len(lines), len(text), len(acts), len(do)))
        lines += [QS(t) for t in text]
        acts += [(OPS[a[0]], a[1], a[2]) for a in do]
        for a in do:
            if a[0] == "setq":
                assert a[1] < 16 and a[2] < 4
assert len(pages) < 256 and len(lines) < 256 and len(acts) < 256
def qbyts(label, vals):
    QL.append(f"{label} !byte " + ",".join(str(v) for v in vals))
def qptrs(label, labels):
    labels = list(labels)
    QL.append(f"{label}_lo !byte " + ",".join(f"<{l}" for l in labels))
    QL.append(f"{label}_hi !byte " + ",".join(f">{l}" for l in labels))
QL.append("*= $5c00")
qbyts("npc_pg", npc_pg)
qbyts("npc_np", npc_np)
for k in range(2):
    qbyts(f"pg_ct{k}", (p[0][k][0] for p in pages))
    qbyts(f"pg_ca{k}", (p[0][k][1] for p in pages))
    qbyts(f"pg_cb{k}", (p[0][k][2] for p in pages))
qbyts("pg_l0", (p[1] for p in pages))
qbyts("pg_nl", (p[2] for p in pages))
qbyts("pg_a0", (p[3] for p in pages))
qbyts("pg_na", (p[4] for p in pages))
qptrs("ln", lines)
qbyts("ac_op", (a[0] for a in acts))
qbyts("ac_a", (a[1] for a in acts))
qbyts("ac_b", (a[2] for a in acts))
qbyts("lvl_qid", (C.QITEMS[i][0] if i in C.QITEMS else 255 for i in range(len(C.FLOORS))))
qptrs("lvl_qt1", (QS(C.QITEMS[i][1]) if i in C.QITEMS else "qnone" for i in range(len(C.FLOORS))))
qptrs("lvl_qt2", (QS(C.QITEMS[i][2]) if i in C.QITEMS else "qnone" for i in range(len(C.FLOORS))))
QL.append(f"INTRO_N = {len(C.INTRO)}")
qptrs("intro", (QS(t, 25) if t else "qnone" for t in C.INTRO))
QL.append(f"NUM_QUESTS = {len(C.QUESTS)}")
qptrs("qname", (QS(n, 22) for n, _ in C.QUESTS))
qptrs("qhint", (QS(h, 24) for _, h in C.QUESTS))
QL.append("quests_tables_end")
QL.append('!if quests_tables_end > $6000 { !error "quest tables overflow $5C00-$5FFF" }')
QL.append("*= $2c00")
QL.append("qnone !byte $ff")
QH, used = [], 1                     # what doesn't fit at $2C00 goes with the high code (quests_hi.asm)
for text, label in QSTR.items():
    line = f'{label} !scr "{text.lower()}" : !byte $ff'
    if used + len(text) + 1 <= 0x3800 - 0x2c00:
        QL.append(line)
        used += len(text) + 1
    else:
        QH.append(line)
QL.append("quests_text_end")
QL.append('!if quests_text_end > $3800 { !error "quest text overflows $2C00-$37FF" }')
open(os.path.join(OUT, "quests.asm"), "w").write("\n".join(QL) + "\n")
open(os.path.join(OUT, "quests_hi.asm"), "w").write("\n".join(QH) + "\n")
qtext = sum(len(t) + 1 for t in QSTR) + 1
print(f"quests: {len(allnpc)} people, {len(pages)} pages, {len(lines)} lines, {len(acts)} actions, "
      f"text {qtext} bytes ({used} at $2C00)")

# previews
try:
    from PIL import Image
    pal = {T["GRASS"]: (80, 160, 60), T["WATER"]: (40, 60, 200), T["FOREST"]: (20, 90, 30),
           T["MOUNTAIN"]: (130, 90, 50), T["TOWN"]: (255, 60, 60), T["CASTLE"]: (255, 255, 0),
           T["DUNGEON"]: (255, 0, 255), T["ROAD"]: (180, 140, 90), T["BRIDGE"]: (200, 160, 100),
           T["SNOW"]: (230, 230, 240), T["ASH"]: (70, 60, 60), T["DEADWOOD"]: (100, 70, 60)}
    im = Image.new("RGB", (N, N))
    for y in range(N):
        for x in range(N):
            im.putpixel((x, y), pal.get(world[y][x], (0, 0, 0)))
    im.putpixel(start, (255, 255, 255))
    im.resize((N * 6, N * 6), Image.NEAREST).save(os.path.join(OUT, "owmap.png"))
except ImportError:
    pass

print(f"levels={len(C.FLOORS)} guards={len(GUARDS)} tiles={len(TILES)} strings={len(STRS)} far={far} "
      f"3d-elements={len(elements)} edge-glyphs={len(edge_glyphs)}")
print("sites:", {k: (v, dist.get(v)) for k, v in sites.items()})
