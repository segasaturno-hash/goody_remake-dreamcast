#!/usr/bin/env python3
# Prueba de un ascensor de subida sin mando: en la fase 1, a los ~3 s, salta a la llegada
# por abajo de la fase pedida (como al subir desde la de abajo). Cuando el ascensor llega
# arriba (Goody deja de subir), Goody camina solo hacia <dir> (der/izq). Trazas [asc]
# cada fotograma: Goody, ascensor, y la dureza bajo sus pies.
#   python3 make_ascensor_test.py Goody.prg Goody_asc.prg <fase> <x> <y> <der|izq>
import sys
src, dst, fase, gx, gy, dirc = sys.argv[1:7]
s = open(src, encoding='latin-1').read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"no encaja: {old[:60]!r}")
    s = s.replace(old, new)

rep('    int diag=0;', '    int diag=0; int auto_t; int auto_hecho; int auto_dir; int auto_ymin=9999; int auto_quieto;')
rep('''     IF (get_joy_button(JOY_BUTTON_DPAD_RIGHT) or get_joy_position(0)>16384+8192) joys_X=2; END // derecha
''', '''     IF (get_joy_button(JOY_BUTTON_DPAD_RIGHT) or get_joy_position(0)>16384+8192) joys_X=2; END // derecha
     IF (auto_dir) joys_X=auto_dir; END
''')
rep('''          Frame;
      Until(confirm())''', '''          Frame;
          auto_t++; if (auto_t == 80) say("[asc] menu: Jugar"); opcioness=1; auto_t=0; break; end
      Until(confirm())''')
dval = '2' if dirc == 'der' else '1'
rep('''        Switch(stage)
            Case 0:
                 If ((goodi.x<75 AND goodi.y>200)''', f'''        auto_t++;
        if (auto_hecho and exists(goodi))
            say("[asc] t="+auto_t+" fase "+stage+" goody "+goodi.x+","+goodi.y+" asc "+goodi.ascensor+" vg "+goodi.velocidad_gravedad+" sube "+sube
                +" pie "+map_get_pixel(0,gdureza,goodi.x/2,(goodi.y+goodi.altura)/2)+" dir "+auto_dir);
            if (goodi.y < auto_ymin) auto_ymin = goodi.y; auto_quieto = 0; else auto_quieto++; end
            if (auto_quieto == 3 and auto_dir == 0 and stage == {fase}) auto_dir = {dval}; say("[asc] arriba: camino"); end
        end
        if (stage == 1 and auto_t > 60 and !auto_hecho)
            auto_hecho = 1; say("[asc] subo a la fase {fase} en el ascensor");
            stage={fase}; goody_x={gx}; goody_y={gy}; Goody_flag=goodi.flags;
            ascensor=1; Sube=-4;
            nivel(stage); Break;
        end
        Switch(stage)
            Case 0:
                 If ((goodi.x<75 AND goodi.y>200)''')
open(dst, 'w', encoding='latin-1', newline='').write(s)
print("ok:", dst)
