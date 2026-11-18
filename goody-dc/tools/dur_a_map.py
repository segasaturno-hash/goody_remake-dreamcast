#!/usr/bin/env python3
# Dureza de Goody: PNG RGBA (32 bits) -> MAP de 8 bits de DIV/Bennu, comprimido.
# En la fase 14 el PNG de 32 bits (960x320 = 1,2 MB, mas lo que gasta descomprimirlo) no
# cabia en la RAM: "IMG_Load_RW: outofmem", sin dureza y Goody caia por todas partes.
# A 8 bits ocupa 4 veces menos. Los colores especiales van a sus indices del juego original
# (suelo 90, pared 30, techo 20, escala 110, lingote 87) y el juego compara por indice.
#   python3 dur_a_map.py <entrada.png> <salida.map>
import sys, gzip, struct, zlib

ESPECIALES = {(0xfc, 0xe8, 0x88): 90, (0x40, 0x40, 0xfc): 30, (0xe8, 0xe8, 0xfc): 20,
              (0x00, 0x6c, 0x00): 110, (0xfc, 0xfc, 0x28): 87}

def read_png(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n'
    off = 8; idat = b''
    while off < len(d):
        n = struct.unpack('>I', d[off:off+4])[0]; t = d[off+4:off+8]; c = d[off+8:off+8+n]
        if t == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', c[:10])
            assert bd == 8 and ct == 6, f"solo PNG RGBA de 8 bits por canal ({bd}, {ct})"
        if t == b'IDAT': idat += c
        off += 12 + n
    raw = zlib.decompress(idat); stride = w * 4; out = bytearray(); prev = bytearray(stride); p = 0
    for y in range(h):
        f = raw[p]; p += 1; line = bytearray(raw[p:p+stride]); p += stride
        for i in range(stride):
            a = line[i-4] if i >= 4 else 0; b = prev[i]; cc = prev[i-4] if i >= 4 else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa = abs(b - cc); pb = abs(a - cc); pc = abs(a + b - 2 * cc)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else cc)) & 255
        out += line; prev = line
    return w, h, bytes(out)

w, h, px = read_png(sys.argv[1])
pal = [(0, 0, 0)] * 256
idx = {}
for rgb, i in ESPECIALES.items():
    idx[rgb] = i; pal[i] = rgb
libres = [i for i in range(1, 256) if i not in ESPECIALES.values()]
out = bytearray(w * h)
for k in range(w * h):
    r, g, b, a = px[k*4:k*4+4]
    if a == 0:
        continue                      # 0 = transparente
    rgb = (r, g, b)
    if rgb not in idx:
        if not libres: sys.exit("mas de 250 colores en la dureza")
        i = libres.pop(0); idx[rgb] = i; pal[i] = rgb
    out[k] = idx[rgb]

m = bytearray(b'map\x1a\x0d\x0a\x00\x00')
m += struct.pack('<HHi', w, h, 0) + b'dureza'.ljust(32, b'\0')
m += bytes(v >> 2 for rgb in pal for v in rgb) + bytes(576)      # paleta de 6 bits + gamma
m += struct.pack('<H', 0)                                        # sin puntos de control
m += out
open(sys.argv[2], 'wb').write(gzip.compress(bytes(m), 9))
print(f"{sys.argv[2]}: {w}x{h}, {len(idx)} colores")
