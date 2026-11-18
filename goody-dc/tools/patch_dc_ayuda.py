#!/usr/bin/env python3
# Goody Dreamcast: la ayuda no se veia. Cada ay?_NN.fpg conserva el codigo original de su
# pagina (ay1_29.fpg tiene el grafico 29, no el 1): se dibuja graph=pag.
#   python3 patch_dc_ayuda.py Goody.prg
import sys
p = sys.argv[1]
s = open(p, encoding='latin-1').read()
old = 'file=gayuda; graph=1;'
n = s.count(old)
if n != 3:
    sys.exit(f"no encaja ({n} veces, esperaba 3)")
s = s.replace(old, 'file=gayuda; graph=pag;')
open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
