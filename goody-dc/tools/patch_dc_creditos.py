#!/usr/bin/env python3
# Goody Dreamcast: creditos del menu (Opciones > Creditos). Usaban los graficos 2 (texto
# que sube) y 3 (fondo) de gmenu, que no entraron en gmenu.fpg. Ahora estan en
# gcrm1.fpg / gcrm2.fpg (sacados de gmenu.gdg / gmenu2.gdg del BennuGD2 original con
# extraer_fpg.py), que se cargan solo mientras se ven los creditos.
#   python3 patch_dc_creditos.py Goody.prg
import sys
p = sys.argv[1]
s = open(p, encoding='latin-1').read()
if 'gcredm' in s:
    sys.exit("ya parcheado")

def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"no encaja ({n} veces): {old[:70]!r}")
    s = s.replace(old, new)

rep('    int gcred;', '    int gcred;  int gcredm;   // gcrm1/2.fpg: fondo y texto de los creditos del menu\n   ')
rep('    dc_preload("data1/gcr*.fpg");      // creditos\n',
    '    dc_preload("data1/gcr*.fpg");      // creditos (gcr1/2 del final y gcrm1/2 del menu)\n')
rep('''    music_fade_off(1200);
    file=gmenu; graph=3; z=-70;''', '''    music_fade_off(1200);
    if (idioma&1) gcredm=fpg_load("data1/gcrm1.fpg"); else gcredm=fpg_load("data1/gcrm2.fpg"); end
    file=gcredm; graph=3; z=-70;''')
rep('''            music_play(musica1,-1);

            signal(id,s_kill);
        end
        frame;
    end
end''', '''            music_play(musica1,-1);

            graph=0;
            if (gcredm<>0) fpg_unload(gcredm); gcredm=0; end
            signal(id,s_kill);
        end
        frame;
    end
end''')
open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
