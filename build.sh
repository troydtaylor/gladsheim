#!/bin/sh
# Build: generate data, assemble, crunch, make the disk image.
#   build/proto.prg   the assembled game (37 KB, runs as-is)
#   build/packed.prg  self-decrunching version (Exomizer), ~40% of the load time
#   build/gladsheim.d64  disk image holding the packed game (or the plain one without Exomizer)
set -e
cd "$(dirname "$0")"
python3 gen.py
acme main.asm
if command -v exomizer >/dev/null 2>&1; then
    # ROMs off while unpacking: part of the program lives in the RAM under BASIC
    exomizer sfx sys -q -n -Di_ram_during=0x34 -Di_irq_during=0 -o build/packed.prg build/proto.prg
    GAME=build/packed.prg
else
    echo "exomizer not found: the disk gets the unpacked game (slower to load)"
    GAME=build/proto.prg
fi
python3 tools/d64.py build/gladsheim.d64 "$GAME" "gladsheim"
