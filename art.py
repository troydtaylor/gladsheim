"""
Monster portraits: 24 fat pixels wide x 42 rows (= 2x2 multicolour sprites, X+Y expanded).
'.' transparent   a = $D025 (shared)   c = sprite colour   b = $D026 (shared)
"""

def sym(halves):
    assert len(halves) == 42, len(halves)
    out = []
    for h in halves:
        assert len(h) == 12, h
        out.append(list(h + h[::-1]))
    return out

def put(img, pts, ch):
    for x, y in pts:
        img[y][x] = ch

def pad(rows, top=0):
    rows = ["." * 12] * top + rows
    return rows + ["." * 12] * (42 - len(rows))

# ------------------------------------------------------------------ originals
SKELETON = sym([
 "............", "..........cc", "........cccc", ".......ccccc", "......cccccc",
 "......cbbbcc", "......cbbbcc", "......cccccc", ".......cccca", ".......ccccc",
 ".......cacac", "........cccc", "..........cc", ".....ccccccc", "....cc....cc",
 "....c.aaaacc", "...cc.....cc", "...c..aaaacc", "...c......cc", "...c..aaaacc",
 "..cc......cc", "..c....aaacc", "..c.......cc", "..c....ccccc", ".cc...cccccc",
 ".cc...cc..cc", "......cc....", ".......c....", ".......c....", ".......c....",
 ".......c....", "......ccc...", ".......c....", ".......c....", ".......c....",
 ".......c....", ".......c....", "......cc....", ".....ccc....", "....cccc....",
 "............", "............"])
put(SKELETON, [(21, y) for y in range(4, 23)], 'a')
put(SKELETON, [(x, 23) for x in range(19, 24)], 'a')
put(SKELETON, [(21, 24), (21, 25)], 'c')

SLIME = sym(pad([
 "..........cc", "........cccc", "......cccccc", ".....ccccaac", "....cccaaacc",
 "...cccaacccc", "...ccacccccc", "..cccccccccc", "..cccbbbcccc", "..cccbbbcccc",
 ".ccccbbbcccc", ".ccccccccccc", ".ccccccccccc", ".ccccccccbbb", ".cccccccccbb",
 "cccccccccccc", "cccccccccccc", "cccccccccccc", "cccacccccccc", "ccacccccaccc",
 "cccccccccccc", "cccccccccccc", "cccccccccccc", ".ccccccccccc", ".cc.ccc.cccc",
 "..c..c...ccc", "..c......c.."], top=14))

ORC = sym([
 "............", ".........ccc", "........cccc", ".......ccccc", ".......ccccc",
 "......cbbccc", "......cccccc", ".....ccccccc", ".......cccac", "......cbcccc",
 "......cbbccc", ".......ccccc", "........cccc", "....aaaaaaaa", "...aaaaaaaaa",
 "..ccaaaaaaaa", "..ccaaacaaaa", "..ccaaaaaaaa", ".ccc.aaaaaaa", ".ccc.aaaaaaa",
 ".cc..aaaaaaa", ".cc..aaaaaaa", ".cc..aabbbbb", "ccc..aaaaaaa", "cc...aaaaaaa",
 "cc...aaaa.aa", ".....aaa....", ".....ccc....", ".....ccc....", ".....ccc....",
 ".....ccc....", ".....ccc....", ".....ccc....", ".....ccc....", ".....aaa....",
 "....aaaa....", "...aaaaa....", "............", "............", "............",
 "............", "............"])
put(ORC, [(22, y) for y in range(6, 30)], 'a')
for y, w in zip(range(5, 13), (2, 3, 4, 4, 4, 4, 3, 2)):
    put(ORC, [(x, y) for x in range(22 - w, 22)] + [(23, y)], 'b')

KING = [row[:] for row in SKELETON]
for y, h in enumerate(["............", ".......b..b.", ".......b.bbb", "......bbbbbb"]):
    KING[y] = list(h + h[::-1])
put(KING, [(9, 5), (14, 5)], 'b')

# ------------------------------------------------------------------ new portraits
SPIDER = sym(pad([
 "aa..........", "..a.........", "...a........", "....a...cccc", "aa...a.ccccc",
 "..a...cccccc", "...a.ccccccc", "....accccacc", "aa..cccccaac", "..aacccccccc",
 "....aacccacc", "aa..ccaccccc", "..aacccccccc", "....accccccc", ".....acccccc",
 "aaa...cccccc", "...aa..ccccc", ".....aa.cccc", "a......acccc", ".a.....ccccc",
 "..a...cbbcbb", "...a..cbbcbb", "....a.cccccc", ".....acccccc", "......cccc.c",
 ".......ccc.c", "........cc.a", "..........a."], top=6))
put(SPIDER, [(11, y) for y in range(0, 6)] + [(12, y) for y in range(0, 6)], 'a')   # silk thread

WRAITH = sym(pad([
 "..........cc", "........cccc", ".......ccccc", "......cccccc", "......ccaaaa",
 ".....ccaaaaa", ".....ccaabba", ".....ccaabba", ".....ccaaaaa", ".....cccaaaa",
 "....cccccaaa", "...ccccccccc", "..cc.ccccccc", ".cc..ccccccc", "cc...ccccacc",
 "c....ccccacc", "c....ccccacc", ".....ccccccc", ".....ccccccc", "....cccccacc",
 "....cccccacc", "....cccccccc", "...ccccacccc", "...ccccacccc", "...ccccccccc",
 "..cccccccacc", "..cccccccacc", "..c.ccc.cccc", "..c.cc..c.cc", ".c...c..c..c",
 ".c......c..."], top=2))

TROLL = sym(pad([
 "..........cc", ".........ccc", "........cccc", "........cbcc", "........cccc",
 ".........ccb", ".........ccc", "......cccccc", "....cccccccc", "...ccccccccc",
 "..cccccccccc", ".ccccccccccc", ".cccc.cccccc", "cccc..cccccc", "ccc...cccccc",
 "ccc...ccaccc", "ccc...cccacc", "ccc...cccccc", "cc....cccccc", "cc....cccccc",
 "cc....cccccc", "cc....aaaaaa", "cc....aaaaaa", "ccc...aaaaaa", "ccc...aabaaa",
 "cc....aaa.aa", "cc....aaa..a", "......ccc...", "......ccc...", ".....cccc...",
 ".....cccc...", ".....ccc....", ".....ccc....", ".....ccc....", ".....ccc....",
 "....cccc....", "...ccccc....", "..cccccc...."], top=3))
put(TROLL, [(0, y) for y in range(18, 32)] + [(1, y) for y in range(26, 34)], 'a')  # club
put(TROLL, [(23, y) for y in range(18, 32)] + [(22, y) for y in range(26, 34)], '.')

KNIGHT = sym([
 "..........b.", ".........bbb", "..........b.", ".........ccc", "........cccc",
 ".......ccccc", ".......caaaa", ".......caaaa", ".......ccccc", ".......ccacc",
 "........cccc", ".....ccccccc", "....cccccccc", "...ccccacccc", "...ccccacccc",
 "..cccccacccc", "..cc.ccacccc", "..cc.ccacccc", "..cc.caaaaaa", "..cc.ccccccc",
 "..cc.ccccccc", "..cc.ccccacc", "..cc.ccccacc", "..cc.ccccacc", "..cc.aaaaaaa",
 "..cc.ccc..cc", ".....ccc....", ".....ccc....", ".....cac....", ".....ccc....",
 ".....ccc....", ".....ccc....", ".....ccc....", ".....cac....", "....cccc....",
 "...ccccc....", "............", "............", "............", "............",
 "............", "............"])
for y in range(12, 30):                                       # kite shield on its left
    w = 5 if y < 24 else 5 - (y - 23)
    put(KNIGHT, [(x, y) for x in range(0, max(w, 1))], 'b' if (y in (12, 13) or y == 20) else 'a')
put(KNIGHT, [(x, y) for y in range(12, 30) for x in range(0, 5) if KNIGHT[y][x] == 'a' and x in (2,)], 'b')
put(KNIGHT, [(22, y) for y in range(2, 26)], 'b')             # sword
put(KNIGHT, [(x, 24) for x in range(20, 24)], 'a')

MAGE = sym([
 "............", "..........cc", ".........ccc", "........cccc", ".......ccccc",
 ".......caaaa", "......ccaaaa", "......cca.ba", "......ccaaaa", "......cccaaa",
 ".....ccccccc", "....cccccccc", "...ccccccccc", "...ccccacccc", "..cccccacccc",
 "..ccc.cacccc", ".ccc..cacccc", ".cc...cacccc", ".cc...caaaaa", "......cacccc",
 "......cacccc", ".....ccacccc", ".....ccacccc", ".....ccacccc", "....cccacccc",
 "....cccacccc", "....cccacccc", "...ccccacccc", "...ccccacccc", "..cccccacccc",
 "..cccccccccc", ".ccccccccccc", ".ccccccccccc", "............", "............",
 "............", "............", "............", "............", "............",
 "............", "............"])
put(MAGE, [(23, y) for y in range(4, 34)], 'a')              # staff
put(MAGE, [(22, 1), (23, 1), (22, 2), (23, 2), (21, 2), (22, 3), (23, 3)], 'b')   # orb

DRAGON = sym([
 "............", "............", "a...........", "aa..........", ".aa.........",
 ".aaa......cc", "..aaa....ccc", "..aaaa...cbc", "...aaaa..ccc", "...aaaaa.ccc",
 "....aaaa.ccc", "....aaaa..cc", "....aaaaa.cc", ".....aaaa.cc", ".....aaaaacc",
 "......aaaccc", "......aaaccc", ".......acccc", "......cccccc", ".....ccccccc",
 "....cccbcccc", "....ccbbbccc", "...cccbbbccc", "...ccbbbbbcc", "...ccbbbbbcc",
 "...ccbbbbbcc", "...cccbbbccc", "....ccbbbccc", "....cccccccc", ".....ccc.ccc",
 ".....ccc..cc", "....cccc..cc", "...ccccc...c", "............", "............",
 "............", "............", "............", "............", "............",
 "............", "............"])
put(DRAGON, [(9, 7), (14, 7)], 'b')

IMAGES = [SKELETON, SLIME, ORC, KING, SPIDER, WRAITH, TROLL, KNIGHT, MAGE, DRAGON]
IMG = {n: i for i, n in enumerate(["SKELETON", "SLIME", "ORC", "KING", "SPIDER", "WRAITH",
                                   "TROLL", "KNIGHT", "MAGE", "DRAGON"])}
