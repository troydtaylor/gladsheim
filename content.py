"""
Game content for Vaults of Kesh: monsters, dungeons and their floors, towns, shops, people.
gen.py turns this into assembler tables (build/gen.asm) and binary maps.
All text is upper/lower agnostic (rendered upper-case); keep lines within the noted widths.
"""
import random
from collections import deque

# ------------------------------------------------------------------ monsters
# name, plural, hp, dmg, hit(0-255), gold, xp, image, colour, $d025, $d026, max group, article
MONSTERS = [
# name,            plural,           hp, dmg, hit, gold,   xp, image,    col, d025, d026, grp, article, attacks, armour
 ("skeleton",      "skeletons",       8,  5, 150,   4,    5, "SKELETON",  1, 12,  2, 3, "a ",   1, 0),
 ("slime",         "slimes",         11,  4, 140,   3,    4, "SLIME",     5, 13,  0, 2, "a ",   1, 0),
 ("orc",           "orcs",           15,  8, 150,   8,   10, "ORC",       5,  9, 15, 3, "an ",  1, 1),
 ("bone king",     "bone kings",     50,  8, 175,  60,   60, "KING",      7,  8,  2, 1, "the ", 2, 2),
 ("goblin",        "goblins",        10,  6, 150,   6,    7, "ORC",      13,  6, 15, 4, "a ",   1, 0),
 ("orc chief",     "orc chiefs",     95, 13, 180,  90,  120, "ORC",      10,  9,  7, 1, "the ", 2, 3),
 ("giant spider",  "giant spiders",  30, 11, 165,  14,   20, "SPIDER",   12,  9,  2, 3, "a ",   1, 2),
 ("spider queen",  "spider queens", 190, 17, 185, 160,  230, "SPIDER",    4,  0,  7, 1, "the ", 2, 4),
 ("wraith",        "wraiths",        44, 15, 175,  18,   30, "WRAITH",   14,  6,  1, 3, "a ",   1, 4),
 ("troll",         "trolls",         60, 17, 160,  26,   44, "TROLL",    13,  9, 15, 2, "a ",   1, 3),
 ("frost troll",   "frost trolls",  230, 22, 185, 280,  400, "TROLL",    14,  6,  1, 1, "the ", 2, 6),
 ("dark knight",   "dark knights",   90, 21, 185,  36,   64, "KNIGHT",   12, 11,  2, 3, "a ",   1, 7),
 ("cultist",       "cultists",       65, 22, 175,  30,   54, "MAGE",      4, 10,  7, 3, "a ",   1, 3),
 ("death knight",  "death knights", 250, 30, 195, 450,  650, "KNIGHT",    1,  0,  2, 1, "the ", 2, 10),
 ("lich",          "liches",        120, 28, 190,  55,  100, "MAGE",     13,  4,  1, 2, "a ",   1, 6),
 ("drake",         "drakes",        150, 32, 185,  65,  125, "DRAGON",    2,  8,  7, 2, "a ",   1, 8),
 ("kesh the wyrm", "wyrms",         255, 34, 195,   0, 3000, "DRAGON",    4,  6,  1, 1, "",     3, 12),
]
MON = {m[0]: i for i, m in enumerate(MONSTERS)}

# ------------------------------------------------------------------ level-up curve (xp to reach level n)
XP_TABLE = [0, 0, 30, 80, 160, 280, 450, 680, 980, 1360, 1830, 2400, 3080,
            3880, 4820, 5900, 7140, 8560, 10180, 12000, 14000]   # index = level, max 20

# ------------------------------------------------------------------ dungeon floors
# Map legend: # wall  . floor  S stairs up (arrival)  V stairs down  T chest  D locked door
#   I inscription  1/2/3 levers (iron/bone/gold)  K key  P rune plate  X secret wall
#   lower-case letters = guardian groups declared in the floor's "guards"
P_NONE, P_RIDDLE, P_LEVER, P_KEY, P_PLATES = 0, 1, 2, 3, 4

CRYPT = [
 "################", "#S.....#.......#", "#.####.#.#####.#", "#.#....#.#..I#.#",
 "#.#.####.#.#.#.#", "#.#......#.#...#", "#.######.#.###.#", "#......#.#...#.#",
 "######.#g###.#.#", "#......#...#.#.#", "#.########.#.#.#", "#.#........#...#",
 "#.#.########.###", "#.#..........#T#", "#...########.Dk#", "################"]
SUNKEN = [
 "################", "#......3.......#", "#.####.#.#####.#", "#.#..#.#.#...#.#",
 "#.#..#...#.#.#.#", "#.##.#####.#...#", "#2...#...#.###.#", "######.#.#...#.#",
 "#......#.###.#.#", "#.####.#...#.#1#", "#.#..#.###.#.###", "#.#..#.#I..#...#",
 "#.#Tc#.#.#####.#", "#.##D#.#.......#", "#.....o...S....#", "################"]

def maze(seed, loops, start=(1, 1)):
    """perfect maze on the odd grid (1..13), then knock out `loops` extra walls"""
    r = random.Random(seed)
    g = [['#'] * 16 for _ in range(16)]
    nodes = [(x, y) for y in range(1, 14, 2) for x in range(1, 14, 2)]
    seen = {start}
    stack = [start]
    g[start[1]][start[0]] = '.'
    while stack:
        x, y = stack[-1]
        nb = [(x + dx, y + dy, dx, dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))
              if (x + dx, y + dy) in set(nodes) and (x + dx, y + dy) not in seen]
        if not nb:
            stack.pop()
            continue
        nx, ny, dx, dy = r.choice(nb)
        g[y + dy // 2][x + dx // 2] = '.'
        g[ny][nx] = '.'
        seen.add((nx, ny))
        stack.append((nx, ny))
    walls = [(x, y) for y in range(1, 14) for x in range(1, 14)
             if g[y][x] == '#' and ((x % 2 == 0 and y % 2 == 1) or (x % 2 == 1 and y % 2 == 0))]
    r.shuffle(walls)
    for x, y in walls[:loops]:
        g[y][x] = '.'
    return g, r

def bfs(g, s, blocked=()):
    dist, prev = {s: 0}, {s: None}
    q = deque([s])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in dist or not (0 <= n[0] < 16 and 0 <= n[1] < 16):
                continue
            if g[n[1]][n[0]] == '#' or n in blocked:
                continue
            dist[n] = dist[(x, y)] + 1
            prev[n] = (x, y)
            q.append(n)
    return dist, prev

def path_to(prev, t):
    out = []
    while t is not None:
        out.append(t)
        t = prev[t]
    return out[::-1]

def dead_ends(g):
    out = []
    for y in range(1, 15):
        for x in range(1, 15):
            if g[y][x] != '#':
                n = sum(g[y + dy][x + dx] != '#' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if n == 1:
                    out.append((x, y))
    return out

def build_floor(seed, loops, protect=None, boss=None, down=False, secret_to_down=False,
                items=(), guards=()):
    """
    protect: 'T' (chest behind boss+door) or 'V' (stairs down behind a door) or None
    items: list of map chars to drop at dead ends (I, K, P, 1, 2, 3, V)
    guards: list of guardian letters to place on corridors (declared by caller)
    Retries seeds until every rule holds.
    """
    for attempt in range(400):
        g, r = maze(seed * 1000 + attempt, loops)
        S = (1, 1)
        g[1][1] = 'S'
        dist, prev = bfs(g, S)
        ends = sorted((e for e in dead_ends(g) if e != S), key=lambda e: -dist[e])
        if len(ends) < len(items) + 3:
            continue
        used = set()
        ok = True
        # protected branch at the farthest dead end: [.. D boss T] or [.. D V]
        if protect:
            t = ends[0]
            p = path_to(prev, t)
            if len(p) < 6:
                continue
            door = p[-3] if protect == 'T' else p[-2]
            if protect == 'T':
                g[t[1]][t[0]] = 'T'
                g[p[-2][1]][p[-2][0]] = boss
                used |= {t, p[-2]}
            else:
                g[t[1]][t[0]] = 'V'
                used.add(t)
            g[door[1]][door[0]] = 'D'
            used.add(door)
            d2, _ = bfs(g, S, blocked={door})
            if t in d2:
                continue                       # loops made a way around the door
            reach = set(d2)
            ends = [e for e in ends[1:] if e in reach]
        else:
            reach = set(dist)
        todo = list(items)
        if down and 'V' not in todo and protect != 'V':
            todo.insert(0, 'V')
        for ch in todo:
            cand = [e for e in ends if e not in used]
            if not cand:
                ok = False
                break
            e = cand[0] if ch == 'V' else r.choice(cand[:max(1, len(cand) // 2 + 1)])
            g[e[1]][e[0]] = ch
            used.add(e)
        if not ok:
            continue
        if secret_to_down:
            v = next((x, y) for y in range(16) for x in range(16) if g[y][x] == 'V')
            dist, prev = bfs(g, S)
            p = path_to(prev, v)
            sec = None
            for c in reversed(p[1:-1]):
                if g[c[1]][c[0]] != '.':
                    continue
                d2, _ = bfs(g, S, blocked={c})
                if v not in d2 and all(pt in d2 for pt in
                                       [(x, y) for y in range(16) for x in range(16) if g[y][x] in 'IK123P']):
                    sec = c
                    break
            if sec is None:
                continue
            g[sec[1]][sec[0]] = 'X'
        # guardians on plain corridor cells, spread along the main routes
        cells = [c for c in reach if g[c[1]][c[0]] == '.' and dist.get(c, 0) > 4]
        r.shuffle(cells)
        for ch, c in zip(guards, cells):
            g[c[1]][c[0]] = ch
        if len(cells) < len(guards):
            continue
        return ["".join(row) for row in g]
    raise RuntimeError(f"could not build floor seed {seed}")

# each floor: name (<=16), dungeon, map, guards {letter: (monster, count)}, random encounter types (4),
#             puzzle, riddle answer, door text (2 lines), inscription (2 lines), chest (gold, line1, line2, sigil bit, victory)
FLOORS = [
 dict(name="crypt of varn", dungeon=0, map=CRYPT,
      guards={'g': ("skeleton", 3), 'k': ("bone king", 1)},
      rnd=("skeleton", "slime", "skeleton", "slime"), puzzle=P_RIDDLE, answer="varn",
      door=("a magic mouth on the door speaks:", "'name the dead king, and pass.'"),
      insc=("words carved on a tomb:", "'here lies varn, the last bone king.'"),
      chest=(100, "the crown of varn! +100 gold.", "a sigil glows: 1 of 5!", 0, 0)),
 dict(name="sunken halls", dungeon=1, map=SUNKEN,
      guards={'o': ("orc", 2), 'c': ("orc chief", 1)},
      rnd=("orc", "slime", "goblin", "orc"), puzzle=P_LEVER,
      door=("a great iron door. it won't budge.", "three levers must hold the key..."),
      insc=("an inscription on the wall reads:", "'east, then west, the north last.'"),
      chest=(200, "the sunken hoard! +200 gold.", "the second sigil is yours!", 1, 0)),
]

def floor(name, dungeon, seed, loops, rnd, guards, puzzle=P_NONE, answer="", door=("", ""),
          insc=("", ""), chest=None, **kw):
    letters = []
    for k, (m, n) in guards.items():
        letters += [k]
    gmap = build_floor(seed, loops, guards=[k for k in letters if k not in kw.get('boss_letters', '')],
                       **{a: b for a, b in kw.items() if a != 'boss_letters'})
    FLOORS.append(dict(name=name, dungeon=dungeon, map=gmap, guards=guards, rnd=rnd, puzzle=puzzle,
                       answer=answer, door=door, insc=insc, chest=chest or (0, "", "", 255, 0)))

# Webwood Caves (danger 3): find the warden's key above, open the queen's lair below
floor("webwood caves 1", 2, 21, 7, ("giant spider", "goblin", "giant spider", "slime"),
      {'w': ("giant spider", 2), 'b': ("goblin", 4)}, down=True, items=['K', 'I'],
      insc=("silk-wrapped bones clutch a note:", "'the queen's key... i hid it here...'"))
floor("webwood caves 2", 2, 22, 8, ("giant spider", "giant spider", "goblin", "orc"),
      {'w': ("giant spider", 3), 'q': ("spider queen", 1)}, protect='T', boss='q', boss_letters='q',
      items=['I'], puzzle=P_KEY,
      door=("a door sealed with web-crusted iron.", "it needs the key from the caves above."),
      insc=("scratched into the rock:", "'her lair is locked. the key, above.'"),
      chest=(350, "spider silk and gold! +350 gold.", "the third sigil is yours!", 2, 0))
# Frozen Deep (danger 4): an illusory wall hides the way down; rune plates open the troll's gate
floor("frozen deep 1", 3, 31, 7, ("wraith", "troll", "giant spider", "wraith"),
      {'t': ("troll", 2), 'h': ("wraith", 3)}, down=True, secret_to_down=True, items=['I'],
      insc=("frost spells out on the wall:", "'not every wall of ice is real.'"))
floor("frozen deep 2", 3, 32, 4, ("troll", "wraith", "troll", "wraith"),
      {'t': ("troll", 2), 'f': ("frost troll", 1)}, protect='T', boss='f', boss_letters='f',
      items=['P', 'P', 'P', 'P', 'I'], puzzle=P_PLATES,
      door=("a gate of black ice, cold as death.", "four rune plates lie dark..."),
      insc=("old runes in the ice read:", "'light four runes to open the gate.'"),
      chest=(600, "a hoard frozen in ice! +600 gold.", "the fourth sigil is yours!", 3, 0))
# Obsidian Keep (danger 5): iron, bone, gold levers; then speak the first flame's name
floor("obsidian keep 1", 4, 41, 5, ("dark knight", "cultist", "troll", "cultist"),
      {'n': ("dark knight", 2), 'u': ("cultist", 3)}, protect='V', items=['1', '2', '3', 'I'],
      puzzle=P_LEVER,
      door=("an obsidian door bars the stairs.", "three levers must hold the key..."),
      insc=("etched in obsidian:", "'iron, then bone, then gold.'"))
floor("obsidian keep 2", 4, 42, 9, ("dark knight", "cultist", "wraith", "dark knight"),
      {'n': ("dark knight", 3), 'd': ("death knight", 1)}, protect='T', boss='d', boss_letters='d',
      items=['I'], puzzle=P_RIDDLE, answer="ashara",
      door=("a door of living flame speaks:", "'name the first flame, and pass.'"),
      insc=("a charred inscription:", "'the sages of ravenmoor remember.'"),
      chest=(1000, "the knight's tribute! +1000 gold.", "the fifth sigil is yours!", 4, 0))
# Vaults of Kesh (danger 6): sealed by the five sigils
floor("vaults of kesh 1", 5, 51, 5, ("lich", "drake", "dark knight", "lich"),
      {'l': ("lich", 2), 'r': ("drake", 1)}, protect='V', items=['P', 'P', 'P', 'I'], puzzle=P_PLATES,
      door=("a vault door, cold and silent.", "three rune plates lie dark..."),
      insc=("gold letters on the floor:", "'three runes wake the vault.'"))
floor("vaults of kesh 2", 5, 52, 9, ("drake", "lich", "drake", "cultist"),
      {'r': ("drake", 2), 'l': ("lich", 2)}, down=True, secret_to_down=True, items=['K', 'I'],
      insc=("a whisper from the walls:", "'the way down hides in plain sight.'"))
floor("vaults of kesh 3", 5, 53, 8, ("drake", "lich", "drake", "lich"),
      {'r': ("drake", 2), 'z': ("kesh the wyrm", 1)}, protect='T', boss='z', boss_letters='z',
      items=['I'], puzzle=P_KEY,
      door=("the wyrm's door: a great lock.", "the key lies on the floor above."),
      insc=("bones of heroes past. a warning:", "'kesh wakes. kesh hungers.'"),
      chest=(0, "the heart of kesh is yours!", "the realm is saved!", 255, 1))

DUNGEONS = [  # name, entrance message (<=38), floors, required sigils mask
    ("crypt of varn",   "the crypt of varn. danger 1. (e)nter?",   [0], 0),
    ("sunken halls",    "the sunken halls. danger 2. (e)nter?",    [1], 0),
    ("webwood caves",   "the webwood caves. danger 3. (e)nter?",   [2, 3], 0),
    ("frozen deep",     "the frozen deep. danger 4. (e)nter?",     [4, 5], 0),
    ("obsidian keep",   "the obsidian keep. danger 5. (e)nter?",   [6, 7], 0),
    ("vaults of kesh",  "the vaults of kesh! danger 6. (e)nter?",  [8, 9, 10], 0x1f),
]

# ------------------------------------------------------------------ towns
# Each shop: (name<=20, quote<=20, sign line<=38, greeting<=38, 4 items)
# Item: (name<=11, stat, price, effect, param)   effects below
E_WEAPON, E_ARMOR, E_ALE, E_ROOM, E_RAISE, E_CURE, E_TOME, E_MANA, E_BLESS = 1, 2, 3, 4, 5, 6, 7, 8, 9
NOITEM = ("", 0, 0, 0, 0)

TOWNS = [
 dict(name="thornbury", layout="thornbury",
      shops=[
        ("ironhand's forge", "weapons. atk stat.", "the sign reads: ironhand's forge",
         "ironhand: 'steel for coin, friend!'",
         [("dagger", 5, 15, E_WEAPON, 0), ("short sword", 8, 35, E_WEAPON, 0),
          ("longsword", 11, 80, E_WEAPON, 0), ("runeblade", 14, 180, E_WEAPON, 0)]),
        ("the steel bastion", "armor soaks blows.", "the sign reads: the steel bastion",
         "armorer: 'nothing gets through these.'",
         [("leather", 1, 20, E_ARMOR, 0), ("chain mail", 2, 60, E_ARMOR, 0),
          ("plate armor", 3, 120, E_ARMOR, 0), ("mithril", 4, 220, E_ARMOR, 0)]),
        ("temple of dawn", "healing, rebirth.", "the sign reads: temple of dawn",
         "priestess: 'the light welcomes you.'",
         [("cure wounds", 0, 15, E_CURE, 0), ("raise dead", 0, 50, E_RAISE, 0), NOITEM, NOITEM]),
        ("the gilded tankard", "ale, rest, rumors.", "the sign reads: the gilded tankard",
         "barkeep: 'what'll it be, travelers?'",
         [("mug of ale", 0, 2, E_ALE, 0), ("room (rest)", 0, 10, E_ROOM, 0), NOITEM, NOITEM]),
        ("the arcanum", "spells made strong.", "the sign reads: the arcanum",
         "sage: 'knowledge has a price.'",
         [("fire tome", 4, 80, E_TOME, 1), ("mend tome", 4, 50, E_TOME, 0),
          ("elven lute", 2, 60, E_TOME, 2), ("mana potion", 0, 15, E_MANA, 0)]),
      ],
      npcs=[
        ("GUARD", "guard: 'welcome to thornbury.'", "'mind the orcs on the south road.'"),
        ("GUARD", "guard: 'the arcanum sells old tomes.'", "'your wizard could use one.'"),
        ("FOLK2", "maud: 'the crypt door has a mouth.'", "'it opens for the dead king's name.'"),
        ("FOLK", "pip: 'are you real adventurers?'", "'my da says orcs smell awful!'"),
        ("FOLK", "mayor brandt: 'five sigils seal'", "'the vaults of kesh. find them!'"),
        ("FOLK", "drunk: 'hic! levers... the sun...'", "'...always starts in the east! hic!'"),
      ],
      rumors=["'the bone king fears fire, they say.'", "'the sun rises in the east, friend.'",
              "'parry when the skeletons swarm.'", "'plate armor saved my life. twice!'",
              "'the temple can raise the fallen.'", "'orcs carry more gold than slimes.'",
              "'the keep can't raise the dead.'", "'ravenmoor sells finer steel.'"]),
 dict(name="ravenmoor", layout="ravenmoor",
      shops=[
        ("blackfire smithy", "masterwork steel.", "the sign reads: blackfire smithy",
         "smith: 'forged in dragonfire!'",
         [("war axe", 17, 300, E_WEAPON, 0), ("elven blade", 20, 650, E_WEAPON, 0),
          ("dragonfang", 24, 1300, E_WEAPON, 0), ("sunsword", 28, 2600, E_WEAPON, 0)]),
        ("the iron ward", "the finest armor.", "the sign reads: the iron ward",
         "armorer: 'dwarf-made, every piece.'",
         [("elven mail", 5, 450, E_ARMOR, 0), ("dwarf plate", 6, 900, E_ARMOR, 0),
          ("dragonscale", 7, 1800, E_ARMOR, 0), ("aegis plate", 8, 3500, E_ARMOR, 0)]),
        ("shrine of stars", "the stars provide.", "the sign reads: shrine of stars",
         "oracle: 'the stars have seen you.'",
         [("cure wounds", 0, 40, E_CURE, 0), ("raise dead", 0, 150, E_RAISE, 0),
          ("blessing", 6, 500, E_BLESS, 0), NOITEM]),
        ("the black raven", "drink and rest.", "the sign reads: the black raven",
         "innkeep: 'sit, rest your bones.'",
         [("dark ale", 0, 5, E_ALE, 0), ("room (rest)", 0, 30, E_ROOM, 0), NOITEM, NOITEM]),
        ("tower of runes", "high magic.", "the sign reads: tower of runes",
         "archmage: 'power, for the worthy.'",
         [("storm tome", 12, 1200, E_TOME, 1), ("life tome", 12, 900, E_TOME, 0),
          ("golden harp", 6, 800, E_TOME, 2), ("elixir", 0, 40, E_MANA, 0)]),
      ],
      npcs=[
        ("GUARD", "guard: 'ravenmoor, at world's edge.'", "'beyond lie the dark lands.'"),
        ("FOLK2", "sage elra: 'the first flame was'", "'called ashara. remember it.'"),
        ("FOLK", "miner: 'deep runes glow when stepped'", "'on. light them all, they say.'"),
        ("FOLK", "pilgrim: 'five sigils seal the'", "'vaults. kesh the wyrm sleeps below.'"),
        ("FOLK2", "old sailor: 'walls down there ain't'", "'always walls. mark me!'"),
      ],
      rumors=["'iron, bone, gold... or was it gold?'", "'a blessing makes you hardier.'",
              "'the death knight hits like a hammer.'", "'the frozen gate wants four runes.'",
              "'drakes breathe fire. wear good mail.'", "'kesh the wyrm has slept for ages.'",
              "'the storm tome is worth every coin.'", "'some walls are only illusions.'"]),
]
