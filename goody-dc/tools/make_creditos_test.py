#!/usr/bin/env python3
# Prueba de los creditos del menu sin mando: menu -> Opciones -> Creditos. Trazas [cred].
#   python3 make_creditos_test.py Goody.prg Goody_cred.prg
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='latin-1').read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"no encaja: {old[:60]!r}")
    s = s.replace(old, new)

rep('    int diag=0;', '    int diag=0; int auto_m; int auto_o;')
rep('''          Frame;
      Until(confirm())''', '''          Frame;
          auto_m++; if (auto_m == 80) say("[cred] menu: elijo Opciones"); opcioness=2; break; end
      Until(confirm())''')
rep('''       If ( confirm() )
          While( confirm() ) Frame; End

          Switch(opcion2)''', '''       auto_o++;
       if (auto_o == 50) say("[cred] opciones: abro los creditos, RAM libre "+(dc_ram_free()/1024)+" KB"); Creditos(); end
       If ( confirm() )
          While( confirm() ) Frame; End

          Switch(opcion2)''')
rep('''    file=gcredm; graph=3; z=-70;''', '''    file=gcredm; graph=3; z=-70;
    say("[cred] creditos: fichero "+gcredm+", fondo "+map_exists(gcredm,3)+", texto "+map_exists(gcredm,2)+", RAM libre "+(dc_ram_free()/1024)+" KB");''')
open(dst, 'w', encoding='latin-1', newline='').write(s)
print("ok:", dst)
