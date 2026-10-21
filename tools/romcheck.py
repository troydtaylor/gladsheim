#!/usr/bin/env python3
"""
Check that the crunched game unpacks correctly on a real memory map: while the BASIC ROM is
switched in ($01 bits 0-1 = 11), reads of $A000-$BFFF return ROM bytes, not RAM.
Boots build/packed.prg that way and compares memory with the uncrunched build/proto.prg.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import C64

class RomShadow(bytearray):
    def __getitem__(self, i):
        if isinstance(i, int) and 0xA000 <= i < 0xC000 and (bytearray.__getitem__(self, 1) & 3) == 3:
            return 0x4C            # whatever the ROM holds: certainly not our data
        return bytearray.__getitem__(self, i)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ref = C64(os.path.join(ROOT, "build", "proto.prg"))
ref.run_until_idle()
c = C64(os.path.join(ROOT, "build", "packed.prg"))
c.sym = ref.sym                      # same program, so the same symbols
shadow = RomShadow(c.mem)
shadow[1] = 0x37                    # the machine starts with every ROM in
c.mem = shadow
c.cpu.memory = shadow
c.run_until_idle(limit=80_000_000)
bad = [hex(a) for a in range(0x0801, 0xB400) if a != ref.pause_addr and shadow[a] != ref.mem[a] and not (0x2000 <= a < 0x2C00)]
print("ROM config while running:", hex(shadow[1]))
print("bytes differing from the uncrunched program:", len(bad), bad[:8])
print("screen text matches:", c.screen_text() == ref.screen_text())
sys.exit(1 if bad else 0)
