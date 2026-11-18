#!/usr/bin/env python3
# Goody Dreamcast, acabado de menus:
#  - sin "Salir" en el menu principal (en la consola no hay a donde salir) ni Alt+S
#  - sin "Pantalla ventana/completa" en Configuracion (siempre pantalla completa)
#  - sin el CARGANDO de cada fase (sale de RAM en ~0,1 s); el del arranque se queda
#  - sin el panel de diagnostico (numeros arriba a la izquierda)
#  - scanlines: el grafico 100 de gscore (640x480) se quito para ahorrar memoria; ahora
#    se hace una tira de 8x480 en memoria y se estira al ancho de la pantalla
#   python3 patch_dc_menu.py Goody.prg
import sys

p = sys.argv[1]
s = open(p, encoding='latin-1').read()
if 'g_scan' in s:
    sys.exit("ya parcheado")

def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f"no encaja ({n} veces, esperaba {count}): {old[:70]!r}")
    s = s.replace(old, new)

# panel de diagnostico
rep('int diag=1;', 'int diag=0;')

# CARGANDO de cada fase
rep('   txtc=write(l_mensajes,320,200,4,"CARGANDO...");\n', '')
rep('   write_delete(txtc);\n', '')

# Salir: fuera del menu principal (2 opciones) y el atajo Alt+S
rep('      opciones(260,310,27,100,-5,1,3);\n', '')
rep('            opcion--; If (opcion<1) opcion=3; End', '            opcion--; If (opcion<1) opcion=2; End')
rep('            opcion++; If (opcion>3) opcion=1; End', '            opcion++; If (opcion>2) opcion=1; End')
rep('         if(key(_alt) and key(_s)) exit("",0); end\n', '', 2)

# Configuracion: sin "pantalla"; quedan sonido, scanlines e idioma (opt 2..4)
rep('''    Opcion3=1;
    signal(father,s_sleep);''', '''    Opcion3=2;
    signal(father,s_sleep);''')
rep('''    Options2(430,228,70,z+1,1);
    Options2(430,256,74,z+1,2);
    Options2(430,285,72,z+1,3);
    Options2(430,314,76,z+1,4);''', '''    Options2(430,228,74,z+1,2);
    Options2(430,256,72,z+1,3);
    Options2(430,285,76,z+1,4);''')
rep('opcion3--; y-=29; If (opcion3<1) opcion3=4; y=325; End', 'opcion3--; y-=29; If (opcion3<2) opcion3=4; y=296; End')
rep('opcion3++; y+=29; If (opcion3>4) opcion3=1; y=238; End', 'opcion3++; y+=29; If (opcion3>4) opcion3=2; y=238; End')

# scanlines
rep('int Scanline;', 'int Scanline;  int g_scan;')
rep('''Process scanlines(double x, y, int file, graph, z)
begin
   alpha=60;''', '''Process scanlines(double x, y, int file, graph, z)
private int sy; end
begin
   //-- Dreamcast: tira de 8x480 con una linea negra de cada dos, estirada a 640 --//
   if (g_scan==0)
       g_scan=map_new(8,480);
       for (sy=1; sy<480; sy+=2) map_put_pixel(0,g_scan,0,sy,rgb(0,0,0)); map_put_pixel(0,g_scan,1,sy,rgb(0,0,0));
           map_put_pixel(0,g_scan,2,sy,rgb(0,0,0)); map_put_pixel(0,g_scan,3,sy,rgb(0,0,0));
           map_put_pixel(0,g_scan,4,sy,rgb(0,0,0)); map_put_pixel(0,g_scan,5,sy,rgb(0,0,0));
           map_put_pixel(0,g_scan,6,sy,rgb(0,0,0)); map_put_pixel(0,g_scan,7,sy,rgb(0,0,0)); end
   end
   file=0; graph=g_scan; size_x=8000; size_y=100;
   alpha=90;''')

open(p, 'w', encoding='latin-1', newline='').write(s)
print("ok:", p)
