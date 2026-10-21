#!/bin/sh
# Build: generate data, assemble, crunch, make the disk image.
#   build/proto.prg   the assembled game (37 KB, runs as-is)
#   build/packed.prg  self-decrunching version (Exomizer), ~40% of the load time
#   build/kesh.d64    disk image holding the packed game (or the plain one without Exomizer)
set -e
cd "$(dirname "$0")"
python3 gen.py
acme main.asm
if command -v exomizer >/dev/null 2>&1; then
    exomizer sfx sys -q -o build/packed.prg build/proto.prg
    GAME=build/packed.prg
else
    echo "exomizer not found: the disk gets the unpacked game (slower to load)"
    GAME=build/proto.prg
fi
python3 tools/d64.py build/kesh.d64 "$GAME" "vaults of kesh"
