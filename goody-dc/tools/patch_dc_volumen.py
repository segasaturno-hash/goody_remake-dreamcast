#!/usr/bin/env python3
# Goody Dreamcast: con la musica sonando desde RAM (dc_preload) las cargas ya no la
# cortan, asi que no hace falta callarla al cargar el menu o una pagina de ayuda.
#   python3 patch_dc_volumen.py Goody.prg
import sys

p = sys.argv[1]
s = open(p, encoding='latin-1').read()
old1 = '    music_set_volume(0);                       // la carga bloquea el audio: se calla mientras dura\n'
old2 = '    music_set_volume(0);\n'
if s.count(old1) != 1 or s.count(old2) != 1:
    sys.exit("no encaja (ya parcheado?)")
s = s.replace(old1, '').replace(old2, '')
open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
