#!/usr/bin/env python3
# Goody Dreamcast: dureza de 8 bits (data1/dur_NN.map, de dur_a_map.py) en vez de PNG de 32
# bits. El PNG de la fase 14 no cabia en RAM al cargarse (outofmem): sin dureza, Goody caia
# por todas partes. map_get_pixel de un grafico de 8 bits devuelve el color de su paleta en
# 32 bits (como en PC), y la paleta de los .map tiene exactamente los colores de la dureza:
# las constantes de 32 bits del juego (0xfce888ff...) no cambian.
#   python3 patch_dc_dureza8.py Goody.prg
import sys
p = sys.argv[1]
s = open(p, encoding='latin-1').read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f"no encaja ({n} veces, esperaba {count}): {old[:70]!r}")
    s = s.replace(old, new)

if 'dur_00.map' not in s:
    for i in range(32):
        rep(f'gdureza=map_load("data1/dur_{i:02d}.png");', f'gdureza=map_load("data1/dur_{i:02d}.map");')
    rep('glingo=map_load("data1/lin_28.png");', 'glingo=map_load("data1/lin_28.map");')
    rep('    dc_preload("data1/dur_*.png");     // durezas: ~0,4 MB\n', '    dc_preload("data1/dur_*.map");     // durezas de 8 bits: ~0,3 MB\n')
    rep('    dc_preload("data1/lin_28.png");\n', '    dc_preload("data1/lin_28.map");\n')

# una version anterior de este parche cambiaba las constantes a indices: se deshace
if '  Color_dureza1=90;' in s:
    rep('''  //-- Dreamcast: dureza de 8 bits (dur_NN.map): indices de paleta, como el original --//
  Color_dureza1=90;
  Paredes=30;
  Techos=20;
  paredescala=110;
  color_lingote=87;''', '''  Color_dureza1=0xfce888ff;
  Paredes=0x4040fcff;
  Techos=0xe8e8fcff;
  paredescala=0x006c00ff;
  color_lingote=0xfcfc28ff;''')
    rep('''    int Color_dureza1=90;
    int Paredes=30;
    int Techos=20;
    int paredescala=110;
    int color_lingote=87;''', '''    int Color_dureza1=0xfce888ff;
    int Paredes=0x4040fcff;
    int Techos=0xe8e8fcff;
    int paredescala=0x006c00ff;
    int color_lingote=0xfcfc28ff;''')
open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
