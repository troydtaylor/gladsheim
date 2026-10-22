#!/bin/sh
# Build: generate data, assemble, crunch, make the disk images.
#   build/proto.prg            the assembled game (runs as-is)
#   build/proto_nomusic.prg    the same game without the music
#   build/packed.prg, build/packed_nomusic.prg   self-decrunching versions (Exomizer)
#   build/gladsheim.d64, build/gladsheim-nomusic.d64   disk images holding them
set -e
cd "$(dirname "$0")"
python3 gen.py
acme main.asm
acme -DMUSIC=0 main.asm
for ED in "" _nomusic; do
    if command -v exomizer >/dev/null 2>&1; then
        # ROMs off while unpacking: part of the program lives in the RAM under BASIC
        exomizer sfx sys -q -n -Di_ram_during=0x34 -Di_irq_during=0 -o build/packed$ED.prg build/proto$ED.prg
        GAME=build/packed$ED.prg
    else
        echo "exomizer not found: the disks get the unpacked game (slower to load)"
        GAME=build/proto$ED.prg
    fi
    D64=build/gladsheim$(echo "$ED" | tr _ -).d64
    python3 tools/d64.py "$D64" "$GAME" "gladsheim"
done
