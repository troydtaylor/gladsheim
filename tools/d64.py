#!/usr/bin/env python3
"""Write a single PRG onto a fresh 1541 .d64 image.  usage: d64.py out.d64 file.prg NAME"""
import sys

SPT = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5   # sectors per track, tracks 1..35

def offset(t, s):
    return (sum(SPT[:t - 1]) + s) * 256

def make(out, prg, name):
    img = bytearray(sum(SPT) * 256)
    used = {(18, 0), (18, 1)}
    data = open(prg, "rb").read()
    chunks = [data[i:i + 254] for i in range(0, len(data), 254)]

    # allocate sectors, track 17 downward then 19 upward, interleave 10
    order = []
    tracks = list(range(17, 0, -1)) + list(range(19, 36))
    for t in tracks:
        n = SPT[t - 1]
        s, seen = 0, set()
        while len(seen) < n:
            while s in seen:
                s = (s + 1) % n
            seen.add(s)
            order.append((t, s))
            s = (s + 10) % n
    secs = order[:len(chunks)]
    for i, (chunk, (t, s)) in enumerate(zip(chunks, secs)):
        o = offset(t, s)
        if i + 1 < len(secs):
            img[o], img[o + 1] = secs[i + 1]
        else:
            img[o], img[o + 1] = 0, len(chunk) + 1
        img[o + 2:o + 2 + len(chunk)] = chunk
        used.add((t, s))

    # BAM
    b = offset(18, 0)
    img[b:b + 4] = bytes([18, 1, 0x41, 0])
    for t in range(1, 36):
        free = [s for s in range(SPT[t - 1]) if (t, s) not in used]
        bits = sum(1 << s for s in free)
        e = b + 4 * t
        img[e:e + 4] = bytes([len(free), bits & 255, (bits >> 8) & 255, (bits >> 16) & 255])
    pad = lambda s, n: s.upper().encode("ascii")[:n].ljust(n, b"\xa0")
    img[b + 0x90:b + 0xA0] = pad(name, 16)
    img[b + 0xA0:b + 0xAB] = b"\xa0\xa0KE\xa02A\xa0\xa0\xa0\xa0"

    # directory
    d = offset(18, 1)
    img[d:d + 2] = bytes([0, 0xFF])
    img[d + 2] = 0x82                          # closed PRG
    img[d + 3], img[d + 4] = secs[0]
    img[d + 5:d + 21] = pad(name, 16)
    img[d + 30], img[d + 31] = len(chunks) & 255, len(chunks) >> 8
    open(out, "wb").write(img)
    print(f"{out}: {name} {len(chunks)} blocks")

if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
