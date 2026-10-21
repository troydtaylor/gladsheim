#!/usr/bin/env python3
"""
Headless test harness: runs build/proto.prg on a 6502 core (py65) with a stubbed
KERNAL GETIN, feeds it keypresses, and renders the VIC-II text screen
(hires + multicolour character mode) to PNG.

usage: python3 tools/sim.py out_prefix "keys..."
  keys: W A S D E (letters), ^ v < > for cursor keys, '|' = take screenshot here
"""
import sys, os
from py65.devices.mpu6502 import MPU
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL = [(0,0,0),(255,255,255),(136,57,50),(103,182,189),(139,63,150),(85,160,73),(64,49,141),(191,206,114),
       (139,84,41),(87,66,0),(184,105,98),(80,80,80),(120,120,120),(148,224,137),(120,105,196),(159,159,159)]
KEYMAP = {'^': 0x91, 'v': 0x11, '<': 0x9d, '>': 0x1d}
KEYBUF = 0x03ff

class C64:
    def __init__(self, prg):
        self.mem = bytearray(65536)
        data = open(prg, "rb").read()
        load = data[0] | data[1] << 8
        self.mem[load:load + len(data) - 2] = data[2:]
        # GETIN stub: LDA $03FF / PHA / LDA #0 / STA $03FF / PLA / RTS
        stub = [0xAD, 0xFF, 0x03, 0x48, 0xA9, 0x00, 0x8D, 0xFF, 0x03, 0x68, 0x60]
        self.mem[0xFFE4:0xFFE4 + len(stub)] = bytes(stub)
        self.mem[0xD011] = 0x9B          # raster bit 8 set -> wait_vb falls through
        self.mem[0xD016] = 0xC8
        self.cpu = MPU(memory=self.mem, pc=0x080D)
        self.cpu.sp = 0xFF
        self.cycles = 0
        self.sym = {}
        symf = os.path.splitext(prg)[0] + ".sym"
        if os.path.exists(symf):
            for line in open(symf):
                parts = line.split("=")
                if len(parts) == 2 and "$" in parts[1]:
                    self.sym[parts[0].strip()] = int(parts[1].split(";")[0].strip()[1:], 16)
        self.on_pause = None
        self.pause_addr = self.sym.get("pause")
        if self.pause_addr:
            self.mem[self.pause_addr] = 0x60      # RTS: skip the delay loop, call on_pause instead

    def step(self):
        if self.cpu.pc == self.pause_addr and self.on_pause:
            self.on_pause(self)
        self.cpu.step()

    def var(self, name, off=0):
        return self.mem[self.sym[name] + off]

    def run_until_idle(self, limit=2_000_000):
        """run until the program polls GETIN with an empty buffer"""
        steps = 0
        while steps < limit:
            if self.cpu.pc == 0xFFE4 and self.mem[KEYBUF] == 0:
                return steps
            self.step()
            steps += 1
        raise RuntimeError(f"no idle after {limit} steps, pc=${self.cpu.pc:04X}")

    def key(self, k):
        self.mem[KEYBUF] = KEYMAP.get(k, ord(k.upper()))
        self.step()                       # enter stub so the key is consumed
        while self.mem[KEYBUF] != 0:
            self.step()
        return self.run_until_idle()

    def render(self, path, scale=3):
        m = self.mem
        cbase = ((m[0xD018] >> 1) & 7) * 0x800
        sbase = (m[0xD018] >> 4) * 0x400
        mc = bool(m[0xD016] & 0x10)
        bg = [m[0xD021] & 15, m[0xD022] & 15, m[0xD023] & 15]
        border = 32
        im = Image.new("RGB", (320 + 2 * border, 200 + 2 * border), PAL[m[0xD020] & 15])
        px = im.load()
        for row in range(25):
            for colm in range(40):
                code = m[sbase + row * 40 + colm]
                color = m[0xD800 + row * 40 + colm] & 15
                for r in range(8):
                    b = m[cbase + code * 8 + r]
                    y = border + row * 8 + r
                    if mc and color & 8:
                        for i in range(4):
                            v = (b >> (6 - 2 * i)) & 3
                            c = PAL[(color & 7) if v == 3 else bg[v]]
                            x = border + colm * 8 + i * 2
                            px[x, y] = c
                            px[x + 1, y] = c
                    else:
                        for i in range(8):
                            c = PAL[color] if b & (0x80 >> i) else PAL[bg[0]]
                            px[border + colm * 8 + i, y] = c
        # sprites (sprite 0 has highest priority, so draw 7..0)
        en = m[0xD015]
        for i in range(7, -1, -1):
            if not en & (1 << i):
                continue
            data = m[sbase + 0x3F8 + i] * 64
            sx = m[0xD000 + 2 * i] | ((m[0xD010] >> i) & 1) << 8
            sy = m[0xD001 + 2 * i]
            xe, ye = (m[0xD01D] >> i) & 1, (m[0xD017] >> i) & 1
            smc = (m[0xD01C] >> i) & 1
            cols = {1: m[0xD025] & 15, 2: m[0xD027 + i] & 15, 3: m[0xD026] & 15}
            for r in range(21):
                for bx in range(24):
                    byte = m[data + r * 3 + bx // 8]
                    if smc:
                        v = (byte >> (6 - 2 * ((bx % 8) // 2))) & 3
                        if not v:
                            continue
                        c = PAL[cols[v]]
                    else:
                        if not byte & (0x80 >> (bx % 8)):
                            continue
                        c = PAL[cols[2]]
                    for dy in range(1 + ye):
                        for dx in range(1 + xe):
                            X = border + sx - 24 + bx * (1 + xe) + dx
                            Y = border + sy - 50 + r * (1 + ye) + dy
                            if 0 <= X < im.width and 0 <= Y < im.height:
                                px[X, Y] = c
        im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)

    def screen_text(self):
        out = []
        for row in range(25):
            line = ""
            for c in range(40):
                v = self.mem[0x0400 + row * 40 + c]
                line += chr(v + 64) if 1 <= v <= 26 else (chr(v) if 32 <= v < 64 else '#')
            out.append(line)
        return "\n".join(out)

if __name__ == "__main__":
    prefix, keys = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""
    c = C64(os.path.join(ROOT, "build", "proto.prg"))
    n = c.run_until_idle()
    print(f"boot: {n} instructions")
    shot = 0
    if not keys or keys[0] != '|':
        pass
    for k in keys:
        if k == '|':
            p = f"{prefix}_{shot:02d}.png"
            c.render(p)
            print("shot", p, f"mode={c.mem[0x10]} ow=({c.mem[0x11]},{c.mem[0x12]}) dg=({c.mem[0x13]},{c.mem[0x14]}) dir={c.mem[0x15]}")
            shot += 1
        else:
            c.key(k)
    if "--text" in sys.argv:
        print(c.screen_text())
