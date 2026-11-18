#!/usr/bin/env python3
# Goody para BennuGD2 Dreamcast: todo lo de las fases en RAM desde el principio.
#   python3 patch_dc_preload.py Goody.prg            (modifica el fichero; se para si no encaja)
# El .prg esta en Windows-1252: se lee y se escribe en latin-1 para no tocar los acentos.
import sys

p = sys.argv[1]
s = open(p, encoding='latin-1').read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f"no encaja ({n} veces, esperaba {count}): {old[:70]!r}")
    s = s.replace(old, new)

if 'dc_preload' in s:
    sys.exit("ya parcheado")

# 1. modulo de la Dreamcast
rep('import "libmod_sound";\n', 'import "libmod_sound";\nimport "libmod_dreamcast";   // dc_preload: fases en RAM\n')

# 2. al arrancar (pantalla CARGANDO, antes de la musica): fases, durezas, menus y la
#    musica del juego a RAM, una sola vez. Despues ningun cambio de fase lee el disco.
rep('''    glogo1=fpg_load("data1/logo1.fpg");''',
'''    dc_preload("data1/niv_*.fpg");     // 32 fases comprimidas: ~0,9 MB
    dc_preload("data1/dur_*.png");     // durezas: ~0,4 MB
    dc_preload("data1/lin_28.png");
    dc_preload("data1/gmenu*.fpg");    // menus (al volver de la partida)
    dc_preload("data1/*.glt");         // fuentes
    dc_preload("data2/musica1.gdt");   // musica de las fases (2 MB): suena desde RAM
    say("[goody] precarga: " + (dc_preload_total()/1024) + " KB en RAM, libre " + (dc_ram_free()/1024) + " KB");
    glogo1=fpg_load("data1/logo1.fpg");''')

# 3. el cambio de fase ya no lee el disco: la musica no se calla
rep('''         music_set_volume(0);
         Switch(stage)
            Case 0: gnivel=fpg_load("data1/niv_00.fpg"); End''',
'''         Switch(stage)
            Case 0: gnivel=fpg_load("data1/niv_00.fpg"); End''')
rep('''            Case 31: gnivel=fpg_load("data1/niv_31.fpg"); End
         End
         music_set_volume(volumen);''',
'''            Case 31: gnivel=fpg_load("data1/niv_31.fpg"); End
         End''')

open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
