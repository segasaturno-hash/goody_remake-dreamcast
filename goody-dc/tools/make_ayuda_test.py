#!/usr/bin/env python3
# Prueba de la ayuda sin mando, por el camino real: menu -> Opciones -> Ayuda -> paginas ->
# salir -> el menu de opciones vuelve a responder. Trazas [ayuda].
#   python3 make_ayuda_test.py Goody.prg Goody_ayuda.prg
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='latin-1').read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"no encaja: {old[:60]!r}")
    s = s.replace(old, new)

rep('    int diag=0;', '    int diag=0; int auto_m; int auto_o; int auto_fin;')
# menu principal: a los ~3 s elige "Opciones"
rep('''         if(key(_alt) and key(_s)) exit("",0); end
''' if False else '''          Frame;
      Until(confirm())''', '''          Frame;
          auto_m++; if (auto_m == 80) say("[ayuda] menu: elijo Opciones"); opcioness=2; break; end
      Until(confirm())''')
# menu de opciones: a los ~2 s abre la ayuda (una vez); al volver, dice que responde
rep('''       If ( confirm() )
          While( confirm() ) Frame; End

          Switch(opcion2)''', '''       auto_o++;
       if (auto_o == 50 and !auto_fin) say("[ayuda] opciones: abro la ayuda, RAM libre "+(dc_ram_free()/1024)+" KB"); Ayuda(320,240,file,29,-100,0,0); end
       if (auto_fin == 1) auto_fin = 2; say("[ayuda] opciones: el menu responde otra vez"); end
       If ( confirm() )
          While( confirm() ) Frame; End

          Switch(opcion2)''')
rep('''   int pag=29;
begin''', '''   int pag=29; int auto_k;
begin''')
rep('''        If ((key(teclado[KRIGHT])or Joys_x==2) AND pag<39)''',
'''        auto_k++;
        If (auto_k % 40 == 0 AND pag<39)
           pag++; ayuda_pagina(pag); file=gayuda; graph=1;
           say("[ayuda] pagina "+pag+" fichero "+gayuda+", RAM libre "+(dc_ram_free()/1024)+" KB, VRAM libre "+(dc_vram_free()/1024)+" KB");
        End
        if (auto_k > 480) say("[ayuda] salgo de la ayuda"); break; end
        If ((key(teclado[KRIGHT])or Joys_x==2) AND pag<39)''')
rep('''     signal(father,s_wakeup);
     set_fps(26,0);
     fpg_unload(gayuda); gayuda=0;''', '''     signal(father,s_wakeup);
     set_fps(26,0);
     fpg_unload(gayuda); gayuda=0;
     say("[ayuda] ayuda cerrada"); auto_fin = 1;''')
open(dst, 'w', encoding='latin-1', newline='').write(s)
print("ok:", dst)
