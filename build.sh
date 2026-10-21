#!/bin/sh
# Build: generate data, assemble, make disk image.
set -e
cd "$(dirname "$0")"
python3 gen.py
acme main.asm
python3 tools/d64.py build/kesh.d64 build/proto.prg "vaults of kesh"
