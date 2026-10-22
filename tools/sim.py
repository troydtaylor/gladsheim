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
        self.mem[0xCB] = 0x40                  # KERNAL: no key held down
        self.mem[0xDD00] = 0x97                # VIC bank 0 until the game changes it
        entry = 0x080D
        if load == 0x0801:                    # follow the BASIC stub's SYS
            line = bytes(self.mem[0x0801:0x0830])
            i = line.find(b"\x9e")
            if i >= 0:
                digits = bytes(ch for ch in line[i + 1:i + 8] if 0x30 <= ch <= 0x39)
                entry = int(digits.decode()) if digits else entry
        self.cpu = MPU(memory=self.mem, pc=entry)
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
        self.disk = {}            # fake 1541: name -> bytes (2-byte load address + data)
        self.write_protect = False
        self._io = {"name": b"", "lfn": 0, "dev": 0, "sa": 0, "chan": b"", "chkin": False}
        self.kernal = {0xFFBA: self._setlfs, 0xFFBD: self._setnam, 0xFFC0: self._open,
                       0xFFC3: self._close, 0xFFC6: self._chkin, 0xFFCC: self._clrchn,
                       0xFFCF: self._chrin, 0xFFD5: self._load, 0xFFD8: self._save,
                       0xFFB7: self._readst, 0xFF90: lambda: None}
        for a in self.kernal:
            self.mem[a] = 0x60     # RTS; the Python handler runs first
        self.pause_addr = self.sym.get("pause")
        if self.pause_addr:
            self.mem[self.pause_addr] = 0x60      # RTS: skip the delay loop, call on_pause instead

    def step(self):
        pc = self.cpu.pc
        if pc == self.pause_addr and self.on_pause:
            self.on_pause(self)
        h = self.kernal.get(pc)
        if h:
            h()
        self.cpu.step()

    # ---------------------------------------------------------------- fake KERNAL disk I/O
    def _carry(self, on):
        self.cpu.p = (self.cpu.p | 1) if on else (self.cpu.p & ~1)
    def _setlfs(self):
        self._io.update(lfn=self.cpu.a, dev=self.cpu.x, sa=self.cpu.y)
    def _setnam(self):
        n, a = self.cpu.a, self.cpu.x | self.cpu.y << 8
        self._io["name"] = bytes(self.mem[a:a + n])
    def _status(self, code, text):
        self._io["chan"] = f"{code:02d}, {text},00,00\r".encode()
    def _open(self):
        io = self._io
        if io["lfn"] == 15 and io["name"].startswith(b"S0:"):
            fn = io["name"][3:]
            hit = fn in self.disk
            self.disk.pop(fn, None)
            self._status(1, "FILES SCRATCHED")
        self._carry(False)
    def _close(self):
        self._carry(False)
    def _chkin(self):
        self._io["chkin"] = True
        self._carry(False)
    def _clrchn(self):
        self._io["chkin"] = False
    def _chrin(self):
        ch = self._io["chan"] or b"00, OK,00,00\r"
        self.cpu.a = ch[0]
        self._io["chan"] = ch[1:] if len(ch) > 1 else b""
        if not self._io["chan"]:
            self._status(0, "OK")
    def _readst(self):
        self.cpu.a = 0
    def _save(self):
        z = self.cpu.a
        start = self.mem[z] | self.mem[z + 1] << 8
        end = self.cpu.x | self.cpu.y << 8
        if self.write_protect:
            self._status(26, "WRITE PROTECT ON")
        else:
            self.disk[self._io["name"]] = bytes([start & 255, start >> 8]) + bytes(self.mem[start:end])
            self._status(0, "OK")
        self._carry(False)
    def _load(self):
        f = self.disk.get(self._io["name"])
        if f is None:
            self._status(62, "FILE NOT FOUND")
            self.cpu.a = 4
            self._carry(True)
            return
        addr = f[0] | f[1] << 8
        self.mem[addr:addr + len(f) - 2] = f[2:]
        end = addr + len(f) - 2
        self.cpu.x, self.cpu.y = end & 255, end >> 8
        self._status(0, "OK")
        self._carry(False)

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
        """Draw the VIC-II picture: text or multicolour text mode, or hires bitmap mode, plus sprites."""
        m = self.mem
        bank = (3 - (m[0xDD00] & 3)) * 0x4000 if m[0xDD02] & 3 else 0
        sbase = bank + (m[0xD018] >> 4) * 0x400
        border = 32
        im = Image.new("RGB", (320 + 2 * border, 200 + 2 * border), PAL[m[0xD020] & 15])
        px = im.load()
        if m[0xD011] & 0x20:                          # hires bitmap
            bbase = bank + (0x2000 if m[0xD018] & 8 else 0)
            for row in range(25):
                for colm in range(40):
                    cv = m[sbase + row * 40 + colm]
                    fg, bgc = PAL[cv >> 4], PAL[cv & 15]
                    for r in range(8):
                        b = m[bbase + row * 320 + colm * 8 + r]
                        y = border + row * 8 + r
                        for i in range(8):
                            px[border + colm * 8 + i, y] = fg if b & (0x80 >> i) else bgc
        else:
            cbase = bank + ((m[0xD018] >> 1) & 7) * 0x800
            mc = bool(m[0xD016] & 0x10)
            bg = [m[0xD021] & 15, m[0xD022] & 15, m[0xD023] & 15]
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
            data = bank + m[sbase + 0x3F8 + i] * 64
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
        """the text on screen: the game's 40-column text layer when it has one, else the char screen"""
        vtx = self.sym.get("VTX")
        cols, base = (40, vtx) if vtx else (40, 0x0400)
        out = []
        for row in range(25):
            line = ""
            for c in range(cols):
                v = self.mem[base + row * cols + c]
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
