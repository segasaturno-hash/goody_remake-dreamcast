#!/usr/bin/env python3
# Version de prueba de Goody que recorre sola las fases mas pesadas (para Flycast,
# sin mando): cada ~4 s salta a la siguiente de la lista y escribe RAM, VRAM y FPS.
#   python3 make_auto_test.py Goody.prg Goody_auto.prg
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='latin-1').read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"no encaja: {old[:60]!r}")
    s = s.replace(old, new)

rep('    int diag=1;', '    int auto_t; int auto_i; int auto_l[8] = 8, 14, 19, 15, 21, 30, 1, 0;\n    int diag=1;')
rep('''        Switch(stage)
            Case 0:
                 If ((goodi.x<75 AND goodi.y>200)''',
'''        auto_t++;
        If (auto_t == 60)
            say("[auto] fase "+stage+": RAM libre "+(dc_ram_free()/1024)+" KB, VRAM libre "+(dc_vram_free()/1024)+" KB, fps "+frame_info.fps);
        End
        If (auto_t > 100 AND auto_i < 7)
            auto_t = 0; stage = auto_l[auto_i]; auto_i++;
            escalera = 0; nivel(stage);
        End
        Switch(stage)
            Case 0:
                 If ((goodi.x<75 AND goodi.y>200)''')
open(dst, 'w', encoding='latin-1', newline='').write(s)
print("ok:", dst)
