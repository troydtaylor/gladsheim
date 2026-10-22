#!/usr/bin/env python3
"""
Automated full playthrough of build/proto.prg (Gladsheim).

The bot only presses keys. It reads emulated memory to see where it is and the
dungeon floors, and content.py for puzzle answers -- like a player with the map
and a walkthrough. It shops, rests, grinds when under-levelled, solves every
dungeon and kills Nidhogg. Assertions check the game state along the way.

    python3 tools/playtest.py [--seed 0x1234] [--quiet]
"""
import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import C64
import content as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FWD = [(0, -1), (1, 0), (0, 1), (-1, 0)]
DIRKEY = {(0, -1): 'W', (0, 1): 'S', (-1, 0): 'A', (1, 0): 'D'}
OWNAME = {'W': "W  north", 'S': "S  south", 'A': "A  west", 'D': "D  east"}
NAMES = ["ARDEN", "MIRA", "TORVIK", "SELA"]
WALL, DOOR, SECRET = 1, 4, 13


class Wipe(Exception):
    pass


class Retreat(Exception):
    """too hurt to go on: climb out, rest, come back"""


class Fallen(Exception):
    """the party was wiped out and woke at the keep"""


class Bot:
    def __init__(self, on_frame=None, seed=None, log=print):
        self.c = C64(os.path.join(ROOT, "build", "proto.prg"))
        self.on_frame = on_frame or (lambda caption, hold: None)
        self.c.on_pause = lambda c: self.on_frame(None, 5)
        self.c.run_until_idle()
        if "(N)EW PARTY" in self.c.screen_text():          # the story so far
            self.on_frame(None, 40)
            self.c.key('N')
        for _ in range(12):                              # keep the heroes' names, keep the first roll
            if "CREATE YOUR PARTY" not in self.c.screen_text():
                break
            self.on_frame(None, 6)
            self.c.key('\r')
        if seed is not None:
            self.c.mem[self.sym("seed")] = seed & 255
            self.c.mem[self.sym("seed") + 1] = (seed >> 8) | 1
        self.log = log
        self.battles = 0
        self.deaths = 0
        self.stats = []
        self.low = 1.0          # lowest party HP fraction seen since the last report
        self.dead_since = 0
        self.may_retreat = True
        self.retreats = 0
        self.deepest = {}
        self.wipes = 0
        self.wipes_since = 0

    # ---------------------------------------------------------------- memory
    def sym(self, n): return self.c.sym[n]
    def v(self, name, off=0): return self.c.mem[self.sym(name) + off]
    def table(self, name, n): return [self.v(name, i) for i in range(n)]
    @property
    def mode(self): return self.c.mem[0x10]
    @property
    def opos(self): return (self.c.mem[0x11], self.c.mem[0x12])
    @property
    def dpos(self): return (self.c.mem[0x13], self.c.mem[0x14])
    @property
    def dir(self): return self.c.mem[0x15]
    def hp(self): return self.table("hp", 4)
    def maxhp(self): return self.table("maxhp", 4)
    def lvls(self): return self.table("lvl", 4)
    def gold(self): return self.v("gold") | self.v("gold", 1) << 8
    def dcell(self, x, y):
        if not (0 <= x < 16 and 0 <= y < 16):
            return WALL
        return self.c.mem[self.sym("DMAP") + y * 16 + x]
    def bottom(self): return self.c.screen_text().splitlines()[24].strip()
    def lines(self, n=5): return [l.strip() for l in self.c.screen_text().splitlines()[25 - n:]]

    # ---------------------------------------------------------------- input
    def key(self, k, caption=None, hold=3):
        self.c.key(k)
        self.on_frame(caption or k, hold)
        if self.v("incombat"):
            self.fight()

    def fight(self):
        self.battles += 1
        mt = self.v("mtype")
        alive0 = sum(1 for h in self.hp() if h)
        for _ in range(600):
            if not self.v("incombat"):
                break
            cur = self.v("cur")
            hp, mx, sp = self.hp(), self.maxhp(), self.table("sp", 4)
            self.low = min(self.low, sum(hp) / sum(mx))
            key, why = 'A', "attack"
            low = [i for i in range(4) if hp[i] and hp[i] * 5 < mx[i] * 2]
            if cur == 0 and sp[0] >= 3 and low:
                key, why = 'H', "heal"
            elif cur == 1 and sp[1] >= 3:
                key, why = 'B', "flame bolt"
            elif cur == 3 and sp[3] >= 2 and sum(hp) * 2 < sum(mx):
                key, why = 'S', "sing"
            elif cur == 1 and hp[1] * 3 < mx[1]:
                key, why = 'P', "parry"
            self.c.key(key)
            if key == 'H':                               # heal the most wounded
                who = min(low, key=lambda i: hp[i] / mx[i])
                self.c.key(str(who + 1))
                why = f"heal {NAMES[who].title()}"
            self.on_frame(f"{key}  {NAMES[cur]}: {why}", 2)
        else:
            raise AssertionError("combat never ended")
        lost = alive0 - sum(1 for h in self.hp() if h)
        self.deaths += max(0, lost)
        self.dead_since += max(0, lost)
        if self.mode == 0 and "AWAKEN" in " ".join(self.lines(3)):
            self.wipes += 1
            self.wipes_since += 1
            self.log(f"   ...wiped by {C.MONSTERS[mt][0]} at levels {self.lvls()}")
            raise Fallen()

    def type_word(self, word, caption):
        for ch in word:
            self.c.key(ch)
            self.on_frame(caption, 3)
        self.c.mem[0x03FF] = 0x0D
        self.c.step()
        while self.c.mem[0x03FF]:
            self.c.step()
        self.c.run_until_idle()
        self.on_frame(caption + "  [RETURN]", 12)

    def say(self, text, hold=14):
        self.on_frame(text, hold)

    # ---------------------------------------------------------------- party care
    def camp_heal(self):
        """H outside combat while someone is hurt and Arden has SP"""
        for _ in range(12):
            hp, mx = self.hp(), self.maxhp()
            if not hp[0] or self.v("sp", 0) < 3:
                return
            if all(h == 0 or h * 4 >= m * 3 for h, m in zip(hp, mx)):
                return
            self.c.key('H')
            self.c.key('\r')                            # RETURN: the most wounded
            self.on_frame("H  Arden heals", 4)

    def healthy(self):
        hp, mx = self.hp(), self.maxhp()
        return 0 not in hp and sum(hp) * 100 >= sum(mx) * 80

    def weak(self):
        hp, mx = self.hp(), self.maxhp()
        return sum(hp) * 100 < sum(mx) * 45 or hp.count(0) >= 2

    # ---------------------------------------------------------------- dungeon movement
    def face(self, want):
        turn = (want - self.dir) & 3
        if turn == 1: self.key('D', "D  turn right")
        elif turn == 3: self.key('Q', "Q  turn left")
        elif turn == 2: self.key('S', "S  turn around")

    def dpath(self, goal, through_guards=True):
        s = self.dpos
        prev, q = {s: None}, deque([s])
        while q:
            p = q.popleft()
            if p == goal:
                break
            for dx, dy in FWD:
                n = (p[0] + dx, p[1] + dy)
                c = self.dcell(*n)
                if n in prev or c in (WALL, DOOR) or (not through_guards and c >= 0x80 and n != goal):
                    continue
                prev[n] = p
                q.append(n)
        if goal not in prev:
            return None
        out, n = [], goal
        while prev[n]:
            out.append(n)
            n = prev[n]
        return out[::-1]

    def goto(self, goal):
        for _ in range(300):
            if self.dpos == goal:
                return
            p = self.dpath(goal)
            assert p, f"floor {self.v('level')}: no path {self.dpos}->{goal}"
            nxt = p[0]
            x, y = self.dpos
            self.face(FWD.index((nxt[0] - x, nxt[1] - y)))
            lv = self.v("level")
            self.key('W', "W  forward")
            if self.v("level") != lv or self.mode != 1:
                return
            if self.dpos != nxt:          # fled from a guardian; try again
                continue
            if self.weak():
                self.camp_heal()
                if self.weak() and self.may_retreat:
                    raise Retreat()
        raise AssertionError("goto never arrived")

    def find(self, cell):
        return [(x, y) for y in range(16) for x in range(16) if self.dcell(x, y) == cell]

    def adjacent_to(self, target):
        best = None
        for d, (dx, dy) in enumerate(FWD):
            stand = (target[0] - dx, target[1] - dy)
            if self.dcell(*stand) in (WALL, DOOR):
                continue
            p = self.dpath(stand)
            if p is not None and (best is None or len(p) < len(best[1])):
                best = (stand, p, d)
        assert best, f"can't reach next to {target}"
        return best[0], best[2]

    # ---------------------------------------------------------------- overworld / town movement
    def tile_pass(self): return self.table("tile_pass", self.sym("NUM_TILES"))

    def ow_tile(self, x, y):
        if self.mode == 2:
            if not (0 <= x < 32 and 0 <= y < 25):
                return self.sym("T_WALL")
            page = self.v("town_page", self.v("town"))
            return self.c.mem[page * 256 + y * 32 + x]
        if not (0 <= x < 64 and 0 <= y < 64):
            return 1
        return self.c.mem[0x4000 + y * 64 + x]

    def walk_to(self, goal, avoid=(6, 4)):
        """overworld or town: BFS on passable tiles, never stepping on other places"""
        tp = self.tile_pass()
        s = self.opos
        prev, q = {s: None}, deque([s])
        while q:
            p = q.popleft()
            if p == goal:
                break
            for (dx, dy), k in DIRKEY.items():
                n = (p[0] + dx, p[1] + dy)
                t = self.ow_tile(*n)
                if n in prev or not tp[t] or (t in avoid and n != goal and self.mode == 0):
                    continue
                prev[n] = (p, k)
                q.append(n)
        assert goal in prev, f"no path {s}->{goal}"
        keys, n = [], goal
        while prev[n]:
            n, k = prev[n]
            keys.append(k)
        for k in reversed(keys):
            self.key(k, OWNAME[k], 2)
        assert self.opos == goal, (self.opos, goal)

    def place(self, i):
        return (self.v("place_x", i), self.v("place_y", i))

    def bump(self, target, caption, hold=12):
        tp = self.tile_pass()
        for (dx, dy), k in DIRKEY.items():
            stand = (target[0] - dx, target[1] - dy)
            w, h = (32, 25) if self.mode == 2 else (64, 64)
            if 0 <= stand[0] < w and 0 <= stand[1] < h and tp[self.ow_tile(*stand)]:
                try:
                    self.walk_to(stand)
                except AssertionError:
                    continue
                self.key(k, caption, hold)
                return
        raise AssertionError(f"cannot reach {target}")

    # ---------------------------------------------------------------- towns
    def enter_town(self, t):
        self.walk_to(self.place(6 + t))
        self.key('E', f"E  enter {C.TOWNS[t]['name'].title()}", 14)
        assert self.mode == 2 and self.v("town") == t

    def leave_town(self):
        self.walk_to((15, 24))
        self.key('S', "S  out the gate", 10)
        assert self.mode == 0

    def counter_of(self, shop):
        """counter/altar tiles inside the shop's walls"""
        x0, y0 = self.v("shop_x0", shop), self.v("shop_y0", shop)
        x1, y1 = self.v("shop_x1", shop), self.v("shop_y1", shop)
        want = (self.sym("T_COUNTER"), self.sym("T_ALTAR"))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.ow_tile(x, y) in want:
                    yield (x, y)

    def open_shop(self, kind, caption):
        t = self.v("town")
        shop = t * 5 + kind
        for target in self.counter_of(shop):
            try:
                self.bump(target, caption)
            except AssertionError:
                continue
            if self.v("inshop"):
                assert self.v("shop") == shop
                return shop
        raise AssertionError(f"could not open shop {shop}")

    def buy(self, letter, who=None, caption=""):
        self.c.key(letter)
        self.on_frame(caption or f"{letter}  buy", 6)
        if who is not None and "WHO" in self.bottom():
            self.c.key(str(who))
            self.on_frame(caption, 6)
        self.on_frame(None, 8)
        return self.bottom()

    def close_shop(self):
        self.key('X', "X  leave", 6)
        assert not self.v("inshop")

    def items(self, shop):
        spec = C.TOWNS[shop // 5]["shops"][shop % 5][4]
        return spec

    def reserve(self):
        return self.reserve_for(self.v("town"))

    def reserve_for(self, t):
        return 40 if t == 0 else 150                   # keep money for rooms and raising the dead

    # ---------------------------------------------------------------- people and quests
    def quests(self):
        return self.table("qs", 8)

    def talk_all(self, t):
        """everyone in town t, to take quests and collect rewards"""
        first, n = self.v("town_npc_first", t), self.v("town_npc_count", t)
        for i in range(first, first + n):
            before = self.quests()
            self.bump((self.v("npc_x", i), self.v("npc_y", i)), "Talking to the townsfolk", 10)
            if self.quests() != before:
                self.log(f"   quest: {' / '.join(self.lines(4)[-4:])}")
                self.on_frame("A quest!", 30)

    def visit_hermit(self):
        self.bump((self.sym("HUT_X"), self.sym("HUT_Y")), "The hermit's hut", 30)
        self.log(f"   hermit: {' / '.join(self.lines(4)[-4:])}")

    def resupply(self, t, shopping=True, talk=True):
        """people, inn, temple if anyone died, then gear: the best affordable upgrades"""
        self.enter_town(t)
        if talk:
            self.talk_all(t)
        dead = [i for i, h in enumerate(self.hp()) if h == 0]
        if dead:
            self.open_shop(2, "the temple")
            for i in dead:
                self.buy('B', i + 1, f"B  raise {NAMES[i].title()}")
            self.close_shop()
        if shopping:
            # plan purchases against the budget: fighters' weapons first, then everyone's armour
            budget = self.gold() - self.reserve_for(t)
            wpn, arm = self.table("wpn", 4), self.table("arm", 4)
            plan = {0: [], 1: []}
            for kind, who in ((0, 2), (1, 2), (1, 0), (1, 1), (1, 3), (0, 0), (0, 3), (0, 1)):
                stock = self.items(t * 5 + kind)
                cur = (wpn if kind == 0 else arm)[who]
                for j in (3, 2, 1, 0):
                    name, val, price, eff, _ = stock[j]
                    if val > cur and price <= budget:
                        budget -= price
                        plan[kind].append((j, who, name))
                        (wpn if kind == 0 else arm)[who] = val
                        break
            for kind in (0, 1):
                if plan[kind]:
                    self.open_shop(kind, ["the weaponsmith", "the armory"][kind])
                    for j, who, name in plan[kind]:
                        self.buy("ABCD"[j], who + 1, f"{'ABCD'[j]}  {name} for {NAMES[who].title()}")
                    self.close_shop()
            shop = self.open_shop(4, "the magic shop")
            for j in (0, 1, 2):
                name, val, price, eff, par = self.items(shop)[j]
                if self.v("bonus", par) < val and price + self.reserve() <= self.gold():
                    self.buy("ABCD"[j], None, f"{'ABCD'[j]}  {name}")
            self.close_shop()
            if t == 1:
                shop = self.open_shop(2, "the shrine")
                for who in (1, 3, 0, 2):
                    if self.gold() >= 500 + 200:
                        self.buy('C', who + 1, f"C  blessing for {NAMES[who].title()}")
                self.close_shop()
        self.open_shop(3, "the inn")
        self.buy('B', None, "B  rent a room")
        assert all(h == m or h == 0 for h, m in zip(self.hp(), self.maxhp()))
        self.close_shop()
        self.leave_town()

    # ---------------------------------------------------------------- dungeons
    def enter_dungeon(self, d):
        self.walk_to(self.place(d))
        self.key('E', f"E  enter {C.DUNGEONS[d][0].title()}", 14)
        assert self.mode == 1 and self.v("dungeon") == d, self.bottom()

    def climb_out(self):
        for _ in range(6):
            if self.mode != 1:
                return
            s = self.find(2)
            assert s, "no stairs up"
            self.goto(s[0])
            self.key('E', "E  climb the stairs", 8)
        assert self.mode == 0

    def solve_floor(self):
        lv = self.v("level")
        f = C.FLOORS[lv]
        for p in self.find(5):                       # inscriptions
            self.goto(p)
        for p in self.find(14):                      # quest item
            self.goto(p)
            self.log(f"   found: {' / '.join(self.lines(2))}")
        for p in self.find(10):                      # key
            self.goto(p)
            assert self.v("keys") & (1 << self.v("dungeon"))
        if f["puzzle"] == C.P_LEVER:
            for cell in (6, 7, 8):
                self.goto(self.find(cell)[0])
                self.key('E', f"E  pull the {['iron', 'bone', 'gold'][cell - 6]} lever", 10)
            assert self.v("pstate", lv) == 3 and not self.find(DOOR)
        if f["puzzle"] == C.P_PLATES:
            while self.find(11):
                self.goto(self.find(11)[0])
            assert not self.find(DOOR), "plates should open the door"
        doors = self.find(DOOR)
        if doors:
            stand, d = self.adjacent_to(doors[0])
            self.goto(stand)
            self.face(d)
            self.key('W', "W  the door", 10)
            if f["puzzle"] == C.P_RIDDLE:
                self.type_word(f["answer"].upper(), f"Typing: {f['answer'].upper()}")
            assert self.dcell(*doors[0]) != DOOR, (lv, self.lines())
        chests = self.find(3)
        if chests and self.may_retreat and not self.healthy():
            raise Retreat()                          # rest before facing the boss
        for p in chests:                             # chest (behind the boss)
            self.goto(p)
        down = self.find(9)
        return down[0] if down else None

    def run_dungeon(self, d):
        town = 0 if d < 3 else 1
        for attempt in range(8):
            self.enter_dungeon(d)
            try:
                floor = self.dungeon_floor_target(d)
                while True:
                    while self.v("level") < floor:      # back down to where we were
                        down = self.find(9)
                        self.goto(down[0])
                        self.key('E', "E  descend", 10)
                    down = self.solve_floor()
                    if self.v("won") or down is None:
                        break
                    self.goto(down)
                    self.key('E', "E  descend", 10)
                    floor = self.v("level")
                    self.deepest[d] = floor
                self.may_retreat = False
                try:
                    self.climb_out()
                except Fallen:
                    pass
                self.may_retreat = True
                return
            except Fallen:
                self.resupply(town, shopping=True)
                continue
            except Retreat:
                self.retreats += 1
                self.say("Too hurt to go on. Back to town to rest...", 12)
                self.may_retreat = False
                try:
                    self.climb_out()
                except Fallen:
                    pass
                self.may_retreat = True
                self.resupply(town, shopping=True)
        raise AssertionError(f"could not finish dungeon {d}")

    def dungeon_floor_target(self, d):
        return self.deepest.get(d, C.DUNGEONS[d][2][0])

    def grind(self, d, target):
        """wander the top floor of dungeon d until every survivor reaches `target`"""
        import random
        r = random.Random(self.battles)
        while min(l for l, h in zip(self.lvls(), self.hp()) if h) < target:
            self.may_retreat = False
            try:
                self.enter_dungeon(d)
                for _ in range(80):
                    cells = [(x, y) for y in range(16) for x in range(16)
                             if self.dcell(x, y) in (0, 12) and self.dpath((x, y), False)]
                    self.goto(r.choice(cells))
                    if self.weak() or min(l for l, h in zip(self.lvls(), self.hp()) if h) >= target:
                        break
                self.climb_out()
            except Fallen:
                pass
            self.may_retreat = True
            self.resupply(0 if d < 3 else 1, shopping=False, talk=False)

    def report(self, label):
        s = dict(label=label, levels=self.lvls(), gold=self.gold(), battles=self.battles,
                 hp=self.maxhp(), wpn=self.table("wpn", 4), arm=self.table("arm", 4),
                 low=self.low, deaths=self.dead_since)
        self.stats.append(s)
        s["retreats"] = self.retreats
        self.log(f"{label:<30} lv {s['levels']}  wpn {s['wpn']}  arm {s['arm']}  "
                 f"gold {s['gold']:5}  battles {s['battles']:3}  low {s['low']:.0%}  deaths {s['deaths']}  retreats {self.retreats}  wipes {self.wipes_since}")
        self.low, self.dead_since, self.wipes_since = 1.0, 0, 0


PLAN = [  # (dungeon, min party level to attempt, town to resupply at before, grind in dungeon)
    (0, 2, None, 0),
    (1, 4, 0, 0),
    (2, 5, 0, 1),
    (3, 9, 1, 2),
    (4, 13, 1, 3),
    (5, 18, 1, 4),
]


def run(b):
    b.say("The party sets out from the Einherjar Hall", 20)
    b.report("start")
    for d, need, town, grind_in in PLAN:
        if town is not None:
            b.resupply(town)
        if grind_in is not None and min(b.lvls()) < need:
            b.say(f"Training for the {C.DUNGEONS[d][0].title()}...", 12)
            b.grind(grind_in, need)
            b.resupply(town if town is not None else 0)
        b.say(f"Into the {C.DUNGEONS[d][0].title()}", 14)
        b.run_dungeon(d)
        sig = bin(b.v("sigils")).count("1")
        b.report(f"after {C.DUNGEONS[d][0]} ({sig} runestones)")
        if d < 5:
            assert sig == d + 1, f"expected {d + 1} runestones, have {sig}"
        if d == 2:                                   # the horn and the star iron
            b.say("To the hermit's hut, with his horn", 14)
            b.visit_hermit()
            b.say("Back to Thornbury with the star iron", 14)
            b.resupply(0, shopping=False)
    assert b.v("won") == 1, "Nidhogg should be dead"
    assert b.quests()[:7] == [3, 3, 3, 3, 3, 3, 2], f"quests left undone: {b.quests()}"
    b.say("Nidhogg is slain. The gates of Valhalla open!", 30)
    return b


if __name__ == "__main__":
    seed = int(sys.argv[sys.argv.index("--seed") + 1], 16) if "--seed" in sys.argv else None
    quiet = "--quiet" in sys.argv
    b = Bot(seed=seed, log=(lambda *a: None) if quiet else print)
    try:
        run(b)
        print("PASS  battles:", b.battles, " wipes:", b.wipes, " gold:", b.gold(), " levels:", b.lvls())
    except Wipe as e:
        print("WIPE", e, "battles:", b.battles, "levels:", b.lvls(), "floor:", b.v("level"))
        sys.exit(1)
