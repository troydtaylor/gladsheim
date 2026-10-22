"""
Music for Gladsheim: two original tunes for the SID, as data.

  WILDS    (overworld and towns) - D major, a bright folk air over a harp-like broken chord
  DUNGEON  (the deep places)     - D minor, a slow lament over a restless arpeggio, a pounding
                                   bass and a muffled drum

Each tune has a speed (frames of the 60 Hz interrupt per tick; a tick is a 16th note) and three
voices; each voice plays a list of patterns in order and loops.  A pattern is a string of tokens:

  @name     switch instrument            d#4:6   note (c c# d ... b, or flats eb bb; octave 0-7)
  r:4       rest                          :n      length in 16ths (kept until changed)

gen.py turns this into build/music.asm and checks that every bar of every voice adds up.
"""

# instrument: waveform ($11 triangle, $21 saw, $41 pulse, $81 noise), attack/decay, sustain/release,
#             starting pulse width (high nibble of 12 bits), effects (1 pulse sweep, 2 vibrato)
INSTRUMENTS = {
    "lead":   (0x41, 0x0A, 0xA8, 0x08, 3),     # warm pulse, gentle vibrato
    "harp":   (0x11, 0x08, 0x00, 0x08, 0),     # plucked triangle
    "bass":   (0x11, 0x0A, 0x86, 0x08, 0),     # round triangle bass
    "mourn":  (0x21, 0x5A, 0xA9, 0x08, 2),     # swelling saw, vibrato
    "tense":  (0x41, 0x04, 0x00, 0x04, 1),     # short pulse plucks, sweeping
    "growl":  (0x21, 0x06, 0x00, 0x08, 0),     # biting saw bass
    "drum":   (0x81, 0x03, 0x00, 0x08, 0),     # noise: a muffled drum
}

# ---------------------------------------------------------------------------- the wilds
WILDS_LEAD = [
    "a4:4 f#4:2 a4:2 d5:6 c#5:2",   # D
    "b4:4 a4:4 e4:8",               # A
    "f#4:4 d4:2 f#4:2 b4:6 a4:2",   # Bm
    "g4:4 b4:4 d5:8",               # G
    "a4:4 f#4:2 a4:2 d5:4 e5:4",    # D
    "f#5:4 e5:2 d5:2 b4:8",         # G
    "e5:4 d5:2 b4:2 g4:4 b4:4",     # Em
    "a4:12 r:4",                    # A
    "b4:4 d5:4 g5:6 f#5:2",         # G
    "f#5:4 e5:2 d5:2 a4:8",         # D
    "b4:2 c#5:2 d5:4 e5:4 d5:2 b4:2",  # G
    "c#5:4 a4:4 e5:8",              # A
    "d5:4 f#5:4 b5:6 a5:2",         # Bm
    "g5:4 f#5:2 e5:2 d5:4 b4:4",    # G
    "a4:4 c#5:2 e5:2 g5:4 e5:4",    # A7
    "d5:12 r:4",                    # D
]
WILDS_CHORDS = ["D", "A", "Bm", "G", "D", "G", "Em", "A", "G", "D", "G", "A", "Bm", "G", "A", "D"]
HARP = {   # broken chords in 8ths
    "D":  "d3:2 a3 f#4 a3 d4 a3 f#4 a3",
    "A":  "a2:2 e3 c#4 e3 a3 e3 c#4 e3",
    "Bm": "b2:2 f#3 d4 f#3 b3 f#3 d4 f#3",
    "G":  "g2:2 d3 b3 d3 g3 d3 b3 d3",
    "Em": "e3:2 b3 g4 b3 e4 b3 g4 b3",
}
BASS = {   # root, fifth, octave, fifth in quarters
    "D": "d2:4 a2 d3 a2", "A": "a1:4 e2 a2 e2", "Bm": "b1:4 f#2 b2 f#2",
    "G": "g1:4 d2 g2 d2", "Em": "e2:4 b2 e3 b2",
}

# ---------------------------------------------------------------------------- the dungeon
DUNGEON_LEAD = [
    "d5:12 c#5:2 d5:2",             # Dm
    "e5:4 f5:4 a5:8",               # Dm
    "g5:6 f5:2 d5:8",               # Bb
    "c#5:12 r:4",                   # A
    "d5:4 a4:4 d5:4 f5:4",          # Dm
    "e5:6 d5:2 c#5:8",              # Dm
    "d5:4 bb4:4 g4:8",              # Gm
    "a4:12 r:4",                    # A
    "f5:8 d5:4 f5:4",               # Bb
    "bb5:12 a5:4",                  # Bb
    "g5:8 bb5:4 g5:4",              # Gm
    "d5:12 r:4",                    # Gm
    "eb5:8 g5:4 bb5:4",             # Eb
    "a5:8 g5:4 e5:4",               # A7
    "f5:4 e5:4 d5:4 c#5:4",         # Dm
    "a4:12 r:4",                    # A
]
DUNGEON_CHORDS = ["Dm", "Dm", "Bb", "A", "Dm", "Dm", "Gm", "A",
                  "Bb", "Bb", "Gm", "Gm", "Eb", "A", "Dm", "A"]
ARP = {    # restless 16ths, up and down
    "Dm": "d4:1 f4 a4 d5 a4 f4 d4 f4 a4 d5 a4 f4 d4 f4 a4 f4",
    "Bb": "bb3:1 d4 f4 bb4 f4 d4 bb3 d4 f4 bb4 f4 d4 bb3 d4 f4 d4",
    "A":  "a3:1 c#4 e4 a4 e4 c#4 a3 c#4 e4 a4 e4 c#4 a3 c#4 e4 c#4",
    "Gm": "g3:1 bb3 d4 g4 d4 bb3 g3 bb3 d4 g4 d4 bb3 g3 bb3 d4 bb3",
    "Eb": "eb4:1 g4 bb4 eb5 bb4 g4 eb4 g4 bb4 eb5 bb4 g4 eb4 g4 bb4 g4",
}
DRUMBASS = {  # pounding bass in 8ths, a drum on 2 and 4
    c: f"@growl {r}2:2 {r}2 @drum c5:2 @growl {r}2:2 {r}2:2 {r}2 @drum c5:2 @growl {r}3:2"
    for c, r in (("Dm", "d"), ("Bb", "bb"), ("A", "a"), ("Gm", "g"), ("Eb", "eb"))
}

# ---------------------------------------------------------------------------- assembled
PATTERNS = {}
def bars(prefix, items, instrument):
    names = []
    for i, text in enumerate(items):
        name = f"{prefix}{i}"
        PATTERNS[name] = f"@{instrument} {text}"
        names.append(name)
    return names
def chordpats(prefix, table, instrument, chords):
    for c, text in table.items():
        PATTERNS[f"{prefix}_{c}"] = (f"@{instrument} " if instrument else "") + text
    return [f"{prefix}_{c}" for c in chords]

TUNES = [
    dict(name="wilds", speed=7, voices=[
        bars("wl", WILDS_LEAD, "lead"),
        chordpats("wh", HARP, "harp", WILDS_CHORDS),
        chordpats("wb", BASS, "bass", WILDS_CHORDS),
    ]),
    dict(name="dungeon", speed=9, voices=[
        bars("dl", DUNGEON_LEAD, "mourn"),
        chordpats("da", ARP, "tense", DUNGEON_CHORDS),
        chordpats("dd", DRUMBASS, None, DUNGEON_CHORDS),
    ]),
]
