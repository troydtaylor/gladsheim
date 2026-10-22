#!/usr/bin/env python3
"""
Listen to the game's music without a C64: runs the real 6502 player (music_start / music_play from
build/proto.prg) one 60 Hz frame at a time, records what it writes to the SID, and renders that with
a simple software SID (oscillators, pulse width, noise, ADSR).  Not reSID, but close enough to judge
the tunes.

    python3 tools/musicwav.py out.wav tune [seconds]
"""
import os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import C64

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATE, FPS, CLOCK = 44100, 60, 985248
SPF = RATE // FPS
ATTACK = [2, 8, 16, 24, 38, 56, 68, 80, 100, 250, 500, 800, 1000, 3000, 5000, 8000]
DECAY = [6, 24, 48, 72, 114, 168, 204, 240, 300, 750, 1500, 2400, 3000, 9000, 15000, 24000]

def call(c, addr, a=0, limit=200000):
    """JSR addr from a trap at $0340 and run until it returns"""
    c.mem[0x0340:0x0346] = bytes([0x20, addr & 255, addr >> 8, 0x4C, 0x43, 0x03])
    c.cpu.pc, c.cpu.a = 0x0340, a
    for _ in range(limit):
        if c.cpu.pc == 0x0343:
            return
        c.cpu.step()
    raise RuntimeError("player never returned")

def sid_frames(tune, frames):
    c = C64(os.path.join(ROOT, "build", "proto.prg"))
    call(c, c.sym["music_init"])
    call(c, c.sym["music_start"], tune)
    out = []
    for _ in range(frames):
        call(c, c.sym["music_play"])
        out.append(bytes(c.mem[0xD400:0xD419]))
    return out

class Voice:
    def __init__(self):
        self.phase, self.env, self.stage, self.gate = 0.0, 0.0, "release", 0
        self.noise = np.random.default_rng(1).uniform(-1, 1, 1 << 16)

    def render(self, regs, n):
        freq = (regs[0] | regs[1] << 8) * CLOCK / 16777216
        pw = ((regs[2] | (regs[3] & 15) << 8) or 1) / 4096
        ctrl, ad, sr = regs[4], regs[5], regs[6]
        gate = ctrl & 1
        if gate and not self.gate:
            self.stage = "attack"
        elif not gate and self.gate:
            self.stage = "release"
        self.gate = gate
        # envelope, step by step through the frame
        env = np.empty(n)
        a = 1 / (ATTACK[ad >> 4] * RATE / 1000)
        d = 1 / (DECAY[ad & 15] * RATE / 1000)
        r = 1 / (DECAY[sr & 15] * RATE / 1000)
        sus = (sr >> 4) / 15
        e, st = self.env, self.stage
        for i in range(n):
            if st == "attack":
                e += a
                if e >= 1:
                    e, st = 1.0, "decay"
            elif st == "decay":
                e = max(sus, e - d * max(e, 0.05) * 3)      # roughly exponential, like the chip
                if e <= sus:
                    st = "sustain"
            elif st == "release":
                e = max(0.0, e - r * max(e, 0.05) * 3)
            env[i] = e
        self.env, self.stage = e, st
        ph = self.phase + np.arange(1, n + 1) * freq / RATE
        self.phase = ph[-1] % 1.0
        p = ph % 1.0
        wavef = np.zeros(n)
        if ctrl & 0x10:
            wavef += 1 - 4 * np.abs(p - 0.5)
        if ctrl & 0x20:
            wavef += 2 * p - 1
        if ctrl & 0x40:
            wavef += np.where(p < pw, 1.0, -1.0)
        if ctrl & 0x80:
            wavef += self.noise[(np.floor(ph * 16).astype(np.int64)) & 0xFFFF]
        return wavef * env

def render(tune, seconds):
    frames = sid_frames(tune, int(seconds * FPS))
    voices = [Voice(), Voice(), Voice()]
    out = []
    for regs in frames:
        vol = (regs[0x18] & 15) / 15
        mix = sum(v.render(regs[k * 7:k * 7 + 7], SPF) for k, v in enumerate(voices))
        out.append(mix * vol * 0.28)
    s = np.concatenate(out)
    k = np.ones(3) / 3                                  # a touch of the chip's high-end roll-off
    s = np.convolve(s, k, mode="same")
    return np.clip(s, -1, 1)

if __name__ == "__main__":
    path, tune = sys.argv[1], int(sys.argv[2])
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 32
    s = render(tune, secs)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((s * 32767).astype("<i2").tobytes())
    print(path, f"{len(s) / RATE:.1f} s")
