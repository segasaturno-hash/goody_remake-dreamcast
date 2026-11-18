#!/usr/bin/env python3
# Copia unos graficos de un FPG (gzip o no) a un FPG nuevo comprimido, tal cual (mismos
# codigos, puntos de control y pixeles).
#   python3 extraer_fpg.py <origen.gdg/.fpg> <destino.fpg> <codigo> [codigo...]
import sys, gzip, struct

src, dst = sys.argv[1], sys.argv[2]
want = [int(c) for c in sys.argv[3:]]
d = open(src, 'rb').read()
if d[:2] == b'\x1f\x8b':
    d = gzip.decompress(d)
magic = d[:3]
bpp = {b'f01': 1, b'fpg': 8, b'f08': 8, b'f16': 16, b'f32': 32}[magic]
head = 8 + (768 + 576 if bpp == 8 else 0)
out = bytearray(d[:head])
off = head
found = {}
while off + 64 <= len(d):
    code = struct.unpack_from('<i', d, off)[0]
    w, h, ncp = struct.unpack_from('<iii', d, off + 52)
    size = 64 + (ncp & 0xffff) * 4 + ((w * bpp + 7) // 8) * h
    if code in want:
        found[code] = d[off:off + size]
        print(f"grafico {code}: {w}x{h}, {bpp} bits")
    off += size
for c in want:
    if c not in found:
        sys.exit(f"no esta el grafico {c}")
    out += found[c]
open(dst, 'wb').write(gzip.compress(bytes(out), 9))
print(f"{dst}: {len(out)} bytes sin comprimir")
