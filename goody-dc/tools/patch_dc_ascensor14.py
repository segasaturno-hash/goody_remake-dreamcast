#!/usr/bin/env python3
# Goody Dreamcast: subida en ascensor de las cloacas (fase 9) a la fase 14. Goody llegaba
# en y=625 y la fase 14 lo devuelve abajo si y>630: solo 5 pixeles. Si el primer fotograma
# no "pisaba" el ascensor (se crea despues que Goody), caia y volvia a la fase 9 en bucle.
# En las demas subidas Goody llega 35 pixeles por encima del ascensor (285 con el ascensor
# en 320, igual que y=ascensor.y-35 al ir montado subiendo); aqui el ascensor esta en 640:
# 605, con el mismo margen que las demas.
#   python3 patch_dc_ascensor14.py Goody.prg
import sys
p = sys.argv[1]
s = open(p, encoding='latin-1').read()
old = '''stage=14;
                    goody_x=390; goody_y=625;'''
new = '''stage=14;
                    goody_x=390; goody_y=605;   // Dreamcast: era 625 (5 px del limite de vuelta, 630)'''
if s.count(old) != 1:
    sys.exit("no encaja (ya parcheado?)")
s = s.replace(old, new)
open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
