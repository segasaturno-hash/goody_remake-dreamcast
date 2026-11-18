#!/usr/bin/env python3
# Goody Dreamcast: los 33 efectos de sonido se cargan en la carga inicial (antes, al
# entrar en la primera fase, leyendo el disco) y los creditos van a la precarga.
#   python3 patch_dc_efectos.py Goody.prg
import sys, re

p = sys.argv[1]
s = open(p, encoding='latin-1').read()
if 'cargar_efectos' in s:
    sys.exit("ya parcheado")

m = re.search(r'\n( *)If \(s_salto==0\)\n(.*?)\n\1End\n', s, re.S)
if not m or 'sound_load("data2/salto1.gdt")' not in m.group(2):
    sys.exit("no encuentro el bloque de sonidos")
cuerpo = m.group(2)

# la funcion nueva, al final del programa
s = s.rstrip('\n') + '\n\n//-- Dreamcast: efectos de sonido, una sola vez en la carga inicial --//\n' \
    'Function cargar_efectos()\nbegin\n    If (s_salto==0)\n' + cuerpo + '\n    End\nend\n'

old = '''    dc_preload("data2/musica1.gdt");   // musica de las fases (2 MB): suena desde RAM
'''
if s.count(old) != 1:
    sys.exit("falta patch_dc_preload.py")
s = s.replace(old, old + '''    dc_preload("data1/gcr*.fpg");      // creditos
    cargar_efectos();                  // los 33 efectos (antes se leian al entrar en la fase 1)
''')
open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
