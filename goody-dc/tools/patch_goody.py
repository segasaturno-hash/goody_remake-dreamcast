#!/usr/bin/env python3
"""
Adapta Goody.prg (BennuGD2/games/Goody) a la Dreamcast.
Cada cambio comprueba que el texto original existe el numero de veces esperado:
si el Goody.prg de partida no es el esperado, el script se para en vez de
generar algo a medias.

Uso: patch_goody.py Goody.prg_original Goody.prg_salida
(el fichero se lee y se escribe en latin-1, como el original)
"""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
import json, os
crops_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(dst)), 'crops.json')
CROPS = json.load(open(crops_path)) if os.path.exists(crops_path) else {}

# centro (x,y) en pantalla de los logos recortados. Original: dibujados en (320,240) y el 2o con y-50.
#   logo 20: caja x 72..551, y 190..294  -> 480x105 -> centro (72+240, 190+52)
#   logo 42: caja x 136..500, y 205..345 -> 365x141 -> centro (136+182, 205+70) y -50
LOGO_POS = {20: (312, 242), 42: (318, 225)}
t = open(src, encoding='latin-1').read()

def sub(pattern, repl, count=1, flags=0, literal=False, what=''):
    global t
    if literal:
        n = t.count(pattern)
        if n != count:
            sys.exit('ERROR (%s): se esperaban %d coincidencias y hay %d:\n%s' % (what, count, n, pattern[:120]))
        t = t.replace(pattern, repl)
    else:
        t, n = re.subn(pattern, repl, t, flags=flags)
        if n != count:
            sys.exit('ERROR (%s): se esperaban %d coincidencias y hay %d' % (what, count, n))

# 1. mod_debug: no se usa (no hay ni una llamada) -------------------------------
sub('import "mod_debug";\n', '', literal=True, what='import mod_debug')

# 2. variables nuevas -----------------------------------------------------------
sub('    int logos = -1;\n',
    '    int logos = -1;\n'
    '\n'
    '    //-- Dreamcast: FPG que se cargan por trozos (ver tools/prepare_assets.py) --//\n'
    '    int gayuda;       // pagina de ayuda actual\n'
    '    int gcred;        // fondos y textos de los creditos\n'
    '    int gmenu_tipo;   // 0 = nada cargado, 1 = solo lo de dentro de la partida, 2 = menu completo\n'
    '    int glogo1; int glogo2; int glogo3;   // un FPG por logo (se precargan mientras se ve el anterior)\n',
    literal=True, what='variables')

# 3. ventana / pantalla completa: no existen en Dreamcast --------------------------
#    (se quita antes de reescribir main(), que pone su propio set_mode)
sub(r'^[ \t]*screen\.fullscreen=(true|false);[ \t]*\n', '', count=9, flags=re.M, what='fullscreen')
sub(r'^[ \t]*window_move\(.*\);[ \t]*\n', '', count=5, flags=re.M, what='window_move')
# set_mode(640,480) en los conmutadores F3 / opcion de menu: reiniciar el video
# a mitad de partida no esta probado en el port; se quitan (main lo pone una vez)
sub(r'^[ \t]*set_mode\(640,480\);[ \t]*\n', '', count=8, flags=re.M, what='set_mode 640 en conmutadores')

# 4. main(): sin lanzador de 320x240, sin ventana ----------------------------------
old_main = re.search(r'process main\(\)\nbegin\n.*?    frame;\n\n    select_joy\(0\);', t, flags=re.S)
if not old_main:
    sys.exit('ERROR: no encuentro process main()')
new_main = '''process main()
begin
    //-- Dreamcast: 640x480 fijo. Sin ventana, sin el lanzador de 320x240 ni --//
    //-- eleccion de pantalla completa. Idioma 1 por defecto (cambiar a 2 para el otro).      --//
    desktop_width=640; desktop_height=480;
    Idioma=1;
    p_completa=1;
    set_mode(640,480);

    frame;

    select_joy(0);'''
t = t[:old_main.start()] + new_main + t[old_main.end():]

# 5. fases: un FPG por fase (data1/niv_NN.fpg) -------------------------------------
cases = '\n'.join('            Case %d: gnivel=fpg_load("data1/niv_%02d.fpg"); End' % (i, i) for i in range(32))
sub(r'         Switch\(stage\)\n            Case 0\.\.8:   gnivel=fpg_load\("data1/gnivel1\.gdg"\); End\n'
    r'            Case 9\.\.16:  gnivel=fpg_load\("data1/gnivel2\.gdg"\); End\n'
    r'            Case 17\.\.22: gnivel=fpg_load\("data1/gnivel3\.gdg"\); End\n'
    r'            Case 23\.\.31: gnivel=fpg_load\("data1/gnivel4\.gdg"\); End\n'
    r'         End\n',
    lambda m: '         music_set_volume(0);\n         Switch(stage)\n' + cases + '\n         End\n         music_set_volume(volumen);\n',
    what='carga de fases')

# 6. FPG pequenos sin cambios de nombre: solo ruta -----------------------------------
for nombre in ('gscore', 'ggoody', 'genemigos', 'gscena2', 'gscena'):
    sub('data1/%s.gdg' % nombre, 'data1/%s.fpg' % nombre, literal=True, what=nombre)

# 7-pre. Casos especiales de gmenu, ANTES del reemplazo general --------------------------
#   F5 en partida (ayuda): Ayuda usa sus propios FPG, no hace falta cargar gmenu
sub('''            if (idioma&1)
                gmenu=fpg_load("data1/gmenu.gdg");
            else
                gmenu=fpg_load("data1/gmenu2.gdg");
            end
            Ayuda(320,240,gmenu,29,-100,0,1);''',
    '            Ayuda(320,240,0,29,-100,0,1);', literal=True, what='ayuda en juego')

#   creditos finales: fondos en su propio FPG, con la fase y el menu descargados
sub('''    fpg_unload(gmenu);
    if (idioma&1)
        gmenu=fpg_load("data1/gmenu.gdg");
    else
        gmenu=fpg_load("data1/gmenu2.gdg");
    end

    set_fps(26,0);
    creditos2(320,240,gmenu,60,-50);

    fade_on(2000); while(exists (type creditos2)) frame; end

    menu_inicio();
''', '''    descargar_gmenu();
    if (gnivel<>0) fpg_unload(gnivel); gnivel=0; end
    if (idioma&1) gcred=fpg_load("data1/gcr1.fpg"); else gcred=fpg_load("data1/gcr2.fpg"); end

    set_fps(26,0);
    creditos2(320,240,gcred,60,-50);

    fade_on(2000); while(exists (type creditos2)) frame; end

    fpg_unload(gcred); gcred=0;
    menu_inicio();
''', literal=True, what='creditos')

# 7. gmenu: cargas y descargas con control de lo que hay cargado -----------------------
#    7a. bloques if/else de 5 lineas (idioma 1 -> gmenu, idioma 2 -> gmenu2)
pat = (r'(?P<ind>[ \t]*)if ?\(idioma&1\)\n[ \t]*gmenu=fpg_load\("data1/gmenu\.gdg"\);\n'
       r'[ \t]*else\n[ \t]*gmenu=fpg_load\("data1/gmenu2\.gdg"\);\n[ \t]*end\n')
blocks = list(re.finditer(pat, t, flags=re.I))
g_ini = re.search(r'^Process Game_over2', t, flags=re.M).start()
g_fin = re.search(r'^//-- Scanlines --//', t, flags=re.M).start()          # entre ambos: dentro de la partida
out, last = [], 0
n_menu = n_game = 0
for m in blocks:
    tipo = 1 if g_ini <= m.start() < g_fin else 2
    n_menu += tipo == 2; n_game += tipo == 1
    out.append(t[last:m.start()]); out.append('%scargar_gmenu(%d);\n' % (m.group('ind'), tipo)); last = m.end()
out.append(t[last:]); t = ''.join(out)
print('   gmenu: %d cargas de menu, %d dentro de la partida' % (n_menu, n_game))

#    7c. cambio de idioma en el menu (carga directa)
sub('fpg_unload(gmenu);\n                    gmenu=fpg_load("data1/gmenu2.gdg");',
    'descargar_gmenu(); cargar_gmenu(2);', literal=True, what='idioma 2')
sub('fpg_unload(gmenu);\n                    gmenu=fpg_load("data1/gmenu.gdg");',
    'descargar_gmenu(); cargar_gmenu(2);', literal=True, what='idioma 1')

#    7d. descargas: todas pasan por descargar_gmenu() (salvo la de Ayuda, que se reescribe abajo)
sub('If (game) fpg_unload(gmenu);', 'fpg_unload(gayuda); gayuda=0;\n     If (game)', literal=True, what='ayuda unload')
n = t.count('fpg_unload(gmenu);')
t = t.replace('fpg_unload(gmenu);', 'descargar_gmenu();')
print('   gmenu: %d descargas' % n)

# 8. menu_inicio(): al volver de una partida hay que tener el menu completo -------------
sub('Process menu_inicio()\nPrivate\n   int seleccion;\n   int ini;\n   int cor;\nbegin\n      let_me_alone();\n',
    'Process menu_inicio()\nPrivate\n   int seleccion;\n   int ini;\n   int cor;\nbegin\n      let_me_alone();\n'
    '      //-- Dreamcast: liberar la fase y tener el menu completo --//\n'
    '      if (gnivel<>0) fpg_unload(gnivel); gnivel=0; end\n'
    '      cargar_gmenu(2);\n',
    literal=True, what='menu_inicio')

# 9. Funciones nuevas (justo antes de skip_action) ------------------------------------
helpers = '''//-- Dreamcast: gmenu cargado por trozos --//
//   tipo 2: menu completo (fondo + botones)     tipo 1: solo lo de dentro de la partida
function cargar_gmenu(int tipo)
begin
    if (gmenu_tipo == tipo) return; end
    music_set_volume(0);                       // la carga bloquea el audio: se calla mientras dura
    if (gmenu_tipo <> 0) fpg_unload(gmenu); gmenu=0; gmenu_tipo=0; end
    if (tipo == 2)
        if (idioma&1) gmenu=fpg_load("data1/gmenu.fpg"); else gmenu=fpg_load("data1/gmenu2.fpg"); end
    else
        if (idioma&1) gmenu=fpg_load("data1/gmenui.fpg"); else gmenu=fpg_load("data1/gmenui2.fpg"); end
    end
    gmenu_tipo = tipo;
    music_set_volume(volumen);
end

function descargar_gmenu()
begin
    if (gmenu_tipo <> 0) fpg_unload(gmenu); end
    gmenu=0; gmenu_tipo=0;
end

//-- Dreamcast: logos de la intro, un FPG por logo --//
function descargar_logos()
begin
    if (glogo1 <> 0) fpg_unload(glogo1); glogo1=0; end
    if (glogo2 <> 0) fpg_unload(glogo2); glogo2=0; end
    if (glogo3 <> 0) fpg_unload(glogo3); glogo3=0; end
    logos=0;
end

//-- Dreamcast: carga los graficos principales POR TROZOS mientras se ven los logos --//
//   (si se salta la intro, main() llama a los tres trozos; lo ya cargado no se repite)
function precarga(int n)
begin
    switch (n)
        case 1:
            cargar_gmenu(2);
        end
        case 2:
            if (gscore==0)     gscore=fpg_load("data1/gscore.fpg"); end
            if (ggoody==0)     ggoody=fpg_load("data1/ggoody.fpg"); end
            if (genemigos==0)  genemigos=fpg_load("data1/genemigos.fpg"); end
        end
        case 3:
            if (gscena==0)     gscena=fpg_load("data1/gscena.fpg"); end
            if (gscena2==0)    gscena2=fpg_load("data1/gscena2.fpg"); end
        end
    end
end

//-- Dreamcast: una pagina de ayuda cada vez (640x480 a 32 bits = 1,2 MB) --//
function ayuda_pagina(int p)
begin
    music_set_volume(0);
    if (gayuda <> 0) fpg_unload(gayuda); gayuda=0; end
    if (idioma&1)
        switch (p)
            case 29: gayuda=fpg_load("data1/ay1_29.fpg"); end
            case 30: gayuda=fpg_load("data1/ay1_30.fpg"); end
            case 31: gayuda=fpg_load("data1/ay1_31.fpg"); end
            case 32: gayuda=fpg_load("data1/ay1_32.fpg"); end
            case 33: gayuda=fpg_load("data1/ay1_33.fpg"); end
            case 34: gayuda=fpg_load("data1/ay1_34.fpg"); end
            case 35: gayuda=fpg_load("data1/ay1_35.fpg"); end
            case 36: gayuda=fpg_load("data1/ay1_36.fpg"); end
            case 37: gayuda=fpg_load("data1/ay1_37.fpg"); end
            case 38: gayuda=fpg_load("data1/ay1_38.fpg"); end
            case 39: gayuda=fpg_load("data1/ay1_39.fpg"); end
        end
    else
        switch (p)
            case 29: gayuda=fpg_load("data1/ay2_29.fpg"); end
            case 30: gayuda=fpg_load("data1/ay2_30.fpg"); end
            case 31: gayuda=fpg_load("data1/ay2_31.fpg"); end
            case 32: gayuda=fpg_load("data1/ay2_32.fpg"); end
            case 33: gayuda=fpg_load("data1/ay2_33.fpg"); end
            case 34: gayuda=fpg_load("data1/ay2_34.fpg"); end
            case 35: gayuda=fpg_load("data1/ay2_35.fpg"); end
            case 36: gayuda=fpg_load("data1/ay2_36.fpg"); end
            case 37: gayuda=fpg_load("data1/ay2_37.fpg"); end
            case 38: gayuda=fpg_load("data1/ay2_38.fpg"); end
            case 39: gayuda=fpg_load("data1/ay2_39.fpg"); end
        end
    end
    music_set_volume(volumen);
end


'''
sub('function int skip_action()', helpers + 'function int skip_action()', literal=True, what='helpers')

# 10. Ayuda: paginas sueltas ---------------------------------------------------------
sub('Process Ayuda(double x,y, int file,graph, double z, size, int game)\nbegin\n'
    '     signal(father,s_sleep);\n     write_delete(all_text);\n     x=320;\n     set_fps(35,0);\n',
    'Process Ayuda(double x,y, int file,graph, double z, size, int game)\nPrivate\n   int pag=29;\nbegin\n'
    '     signal(father,s_sleep);\n     write_delete(all_text);\n     x=320;\n     set_fps(35,0);\n'
    '     ayuda_pagina(pag); file=gayuda; graph=1;\n',
    literal=True, what='Ayuda inicio')
sub('        If ((key(teclado[KRIGHT])or Joys_x==2) AND graph<39)\n'
    '           While(key(teclado[KRIGHT])or Joys_x==2) Frame; End\n           graph++;\n        End\n'
    '        If ((key(teclado[KLEFT])or Joys_x==1) AND graph>29)\n'
    '           While(key(teclado[KLEFT])or Joys_x==1) Frame; End\n           graph--;\n        End\n',
    '        If ((key(teclado[KRIGHT])or Joys_x==2) AND pag<39)\n'
    '           While(key(teclado[KRIGHT])or Joys_x==2) Frame; End\n'
    '           pag++; ayuda_pagina(pag); file=gayuda; graph=1;\n        End\n'
    '        If ((key(teclado[KLEFT])or Joys_x==1) AND pag>29)\n'
    '           While(key(teclado[KLEFT])or Joys_x==1) Frame; End\n'
    '           pag--; ayuda_pagina(pag); file=gayuda; graph=1;\n        End\n',
    literal=True, what='Ayuda paginas')

# 11. Logos: se carga TODO antes de que empiece la musica ---------------------------------
#     Cargar con la musica sonando la corta (el audio se alimenta desde el bucle del juego).
#     Los logos OPERA y COPTRON son casi todo negro: se recortan a su caja (tools/prepare_assets.py)
#     y se colocan en el mismo sitio; asi los 3 caben en RAM a la vez junto al resto del juego.
sub('    set_fps(26,0);\n    fade_on(FADE_TIME);\n    logos=fpg_load("data1/logos.gdg");\n',
    '''    set_fps(26,0);
    fade_on(100);
    //-- Dreamcast: se carga todo ahora, antes de la musica y de los logos --//
    If (l_mensajes==0) L_mensajes=fnt_load("data1/mensajes.glt"); End
    txt=write(l_mensajes,320,240,4,"CARGANDO...");
    Frame; Frame;
    glogo1=fpg_load("data1/logo1.fpg");
    glogo2=fpg_load("data1/logo2.fpg");
    glogo3=fpg_load("data1/logo3.fpg");
    logos=glogo1;
    precarga(1); precarga(2); precarga(3);
    write_delete(txt);
''', literal=True, what='Logotipos carga')
sub('Process logotipos()\nbegin\n', 'Process logotipos()\nPrivate\n    int txt;\nbegin\n', literal=True, what='Logotipos private')
sub('fpg_unload(logos);', 'descargar_logos();', count=3, literal=True, what='fpg_unload(logos)')

m = re.search(r'Process OPERA\(double x,y,int file,graph\)\nbegin\n.*?\n   fade_off\(875\); While\(fade_info\.fading\) Frame; End\nEnd\n', t, flags=re.S)
if not m:
    sys.exit('ERROR: no encuentro Process OPERA')
t = t[:m.start()] + '''Process OPERA(double x,y,int file,graph)
begin
   //-- Dreamcast: la animacion original son 42 fotogramas de 640x480 (25 MB). --//
   //-- Solo se conservan 3: OPERA soft (20), COPTRON games (42) y creditos (22). --//
   //-- Ya estan todos en RAM (los carga Logotipos); aqui no se carga nada.       --//
   //-- Los dos primeros estan recortados: x,y es el centro de la caja recortada.  --//
   file=glogo1; graph=20; x=LOGO1_X; y=LOGO1_Y;
   timer[0]=0; while(timer[0]<170) check_if_cancel_intro(); frame; end
   fade_off(250); While(fade_info.fading) Frame; End
   fade_on(FADE_TIME);
   file=glogo2; graph=42; x=LOGO2_X; y=LOGO2_Y;
   timer[0]=0; while(timer[0]<200) check_if_cancel_intro(); frame; end
   fade_off(250); While(fade_info.fading) Frame; End
   file=glogo3; graph=22; x=320; y=240;
   fade_on(500); While(fade_info.fading) Frame; End
   timer[0]=0; while(timer[0]<350) check_if_cancel_intro(); frame; end
   fade_off(875); While(fade_info.fading) Frame; End
End
'''.replace('LOGO1_X', str(LOGO_POS[20][0])).replace('LOGO1_Y', str(LOGO_POS[20][1])) \
   .replace('LOGO2_X', str(LOGO_POS[42][0])).replace('LOGO2_Y', str(LOGO_POS[42][1])) + t[m.end():]

# main(): lo que no se haya precargado se carga aqui (por ejemplo si se salto la intro)
sub('''    cargar_gmenu(2);

    gscore=fpg_load("data1/gscore.fpg");
    ggoody=fpg_load("data1/ggoody.fpg");
    genemigos=fpg_load("data1/genemigos.fpg");
    gscena=fpg_load("data1/gscena.fpg");
    gscena2=fpg_load("data1/gscena2.fpg");
''', '''    precarga(1); precarga(2); precarga(3);
''', literal=True, what='main precarga')

# 12. video final: la Dreamcast no reproduce Theora -------------------------------------
sub('''    file=0;
    mid = media_load( "data2/final.gdm", &graph, 0 );
    map_clear(0,graph,rgba(0,0,0,0));
    x=320; y=240;

    fade_on(2000); // While(fade_info.fading) Frame; End

    media_play(mid);

    while( media_get_status( mid ) != MEDIA_STATUS_ENDED ) frame; end

    fade_off(2000); While(fade_info.fading) Frame; End

    media_unload( mid );
''', '''    //-- Dreamcast: sin el video final (final.gdm, Theora 23 MB). Se pasa a los creditos. --//
''', literal=True, what='video final')


# 15. Redefine: "Conforme S/N ?" con el mando: START = S (si), B = N (no) --------------------
sub(r'(Process Redefine\([^)]*\)\nPrivate\n)', r'\1    int hint;\n', what='Redefine private')
sub('''    graph=20;
    Repeat Frame; Until(key(_s) or key(_y) OR key(_n) OR key(_esc) OR get_joy_button(JOY_BUTTON_BACK))
    If (key(_s) or key(_y))
       From asigna=0 To 5;
          teclado[asigna]=redef[asigna];
       End
    End
    While(key(_esc) OR get_joy_button(JOY_BUTTON_BACK)) Frame; End
''', '''    graph=20;
    //-- Dreamcast: con el mando START = S (confirmar), B = N (cancelar) --//
    If (l_mensajes==0) L_mensajes=fnt_load("data1/mensajes.glt"); End
    hint=write(l_mensajes,x,y+34,4,"START SI    B NO");
    While((get_joy_button(JOY_BUTTON_START) OR key(_enter)) OR get_joy_button(JOY_BUTTON_B)) Frame; End
    Repeat Frame; Until(key(_s) or key(_y) OR key(_n) OR key(_esc) OR get_joy_button(JOY_BUTTON_BACK) OR (get_joy_button(JOY_BUTTON_START) OR key(_enter)) OR get_joy_button(JOY_BUTTON_B))
    If (key(_s) or key(_y) or (get_joy_button(JOY_BUTTON_START) OR key(_enter)))
       From asigna=0 To 5;
          teclado[asigna]=redef[asigna];
       End
    End
    write_delete(hint);
    While(confirm() OR key(_esc) OR get_joy_button(JOY_BUTTON_BACK) OR (get_joy_button(JOY_BUTTON_START) OR key(_enter)) OR get_joy_button(JOY_BUTTON_B)) Frame; End
''', literal=True, what='Redefine S/N')

# 16. B = CANCELAR. En Goody confirm() incluye B (y A, X, Y, Enter): al pulsar B para salir de
#     Opciones se leia primero como "confirmar" y volvia a abrir la opcion (Redefinir...). Un
#     mando de PC tiene el boton Back para cancelar; la Dreamcast no. Ahora:
#       confirm()      = Enter/START, Espacio, A, X, Y        (B ya no confirma)
#       cancelar       = Esc, Back y B (las listas de cancelar del juego ya incluian B)
sub('return key(_enter) OR key(_space) OR get_joy_button(JOY_BUTTON_Y) OR get_joy_button(JOY_BUTTON_X) OR get_joy_button(JOY_BUTTON_A) OR get_joy_button(JOY_BUTTON_B);',
    'return key(_enter) OR key(_space) OR get_joy_button(JOY_BUTTON_START) OR get_joy_button(JOY_BUTTON_Y) OR get_joy_button(JOY_BUTTON_X) OR get_joy_button(JOY_BUTTON_A);',
    literal=True, what='confirm sin B')
#     Continuar? y Abandonar partida: la unica cancelacion era Esc/Back (2 dialogos)
sub('if(key(_esc) or get_joy_button(JOY_BUTTON_BACK)) Aban=0; end',
    'if(key(_esc) or get_joy_button(JOY_BUTTON_BACK) or get_joy_button(JOY_BUTTON_B)) Aban=0; end',
    count=2, literal=True, what='Continuar/Abandona con B')

# 17. COLISIONES: la dureza se lee de un PNG RGBA (ruta probada en el port), no del FPG de 8 bits --------
#     Goody compara map_get_pixel() con 5 constantes segun map_info(...,g_depth): indices de paleta
#     (8 bits) o 0xRRGGBBAA (32 bits). El port convierte las superficies a RGBA8888 al leerlas y
#     ninguno de sus ejemplos ejercita un FPG de 8 bits con paleta; si map_info dice 8 y get_pixel
#     devuelve RGBA, nada coincide: todo es "aire" y Goody se cae por el suelo. Con un PNG RGBA
#     (prepare_assets.py: paleta*4, igual que las constantes de 32 bits) el resultado es exacto.
LIN_X0, LIN_Y0, LIN_STAGE = 544, 14, 28          # deben coincidir con prepare_assets.py
sub('    int mapa_dureza;\n', '    int mapa_dureza;\n    int gdureza; int glingo; int t_dur;   // PNG de dureza y mascara de lingotes (map_load, fichero 0)\n',
    literal=True, what='globales dureza')
cases_dur = '\n'.join('     case %d: gdureza=map_load("data1/dur_%02d.png"); end' % (i, i) for i in range(32))
m = re.search(r'function set_mapa_dureza\(int n\)\nbegin\n.*?  mapa_dureza = n;\nend\n', t, flags=re.S)
if not m:
    sys.exit('ERROR: no encuentro set_mapa_dureza')
t = t[:m.start()] + '''function set_mapa_dureza(int n)
begin
  //-- Dreamcast: la dureza viene de data1/dur_NN.png (RGBA, ver prepare_assets.py) y se usan --//
  //-- siempre las constantes de 32 bits. n (codigo del mapa en el FPG) ya no hace falta.     --//
  t_dur=get_timer();
  if (gdureza<>0) map_unload(0,gdureza); gdureza=0; end
  if (glingo<>0)  map_unload(0,glingo);  glingo=0;  end
  switch (stage)
''' + cases_dur + '''
  end
  if (stage==LIN_STAGE_N) glingo=map_load("data1/lin_LIN_STAGE_N.png"); end
  Color_dureza1=0xfce888ff;
  Paredes=0x4040fcff;
  Techos=0xe8e8fcff;
  paredescala=0x006c00ff;
  color_lingote=0xfcfc28ff;
  mapa_dureza = n;
  say("[goody] dureza fase "+stage+": "+(get_timer()-t_dur)+" ms, id "+gdureza+", RAM libre "+(memory_free()/1024)+" KB");
end
'''.replace('LIN_STAGE_N', str(LIN_STAGE)) + t[m.end():]
sub('map_get_pixel(gnivel,mapa_dureza,', 'map_get_pixel(0,gdureza,', count=43, literal=True, what='lecturas de dureza')
sub('if (map_get_pixel(gnivel,11,x,y)<>color_lingote) return; end',
    'if (map_get_pixel(0,glingo,(x-%d)/2,(y-%d)/2)<>color_lingote) return; end' % (LIN_X0, LIN_Y0),
    count=1, literal=True, what='lingotes')

# 18. Nivel: texto "CARGANDO..." mientras se carga la fase y tiempos en la consola -----------------
sub('Process Nivel(stage)\nPrivate\n   int Aguas;\n   int numer;\nbegin\n',
    'Process Nivel(stage)\nPrivate\n   int Aguas;\n   int numer;\n   int txtc;\n   int t0;\nbegin\n', literal=True, what='Nivel private')
sub('   put_screen(0,0);\n\nframe;\n',
    '   put_screen(0,0);\n   txtc=write(l_mensajes,320,200,4,"CARGANDO...");\n   t0=get_timer();\nframe;\n', literal=True, what='Nivel cargando')
sub('   ini_files();\n',
    '   ini_files();\n   write_delete(txtc);\n   say("[goody] fase "+stage+" cargada en "+(get_timer()-t0)+" ms, RAM libre "+(memory_free()/1024)+" KB");\n',
    literal=True, what='Nivel say')


# 19. Mapas de objetos recortados (ver prepare_assets.py): el Escenario se coloca en el centro de la caja ---
if CROPS:
    n0 = t.index('Process Nivel(stage)')
    n1 = t.index('//-- Carga Ficheros Graficos')
    nivel = t[n0:n1]
    parts = re.split(r'(?m)^(?=\s{6}Case \d+:)', nivel)
    for k, part in enumerate(parts):
        m = re.match(r'\s{6}Case (\d+):', part)
        if not m: continue
        stage = int(m.group(1))
        for c in CROPS.values():
            if c['stage'] != stage: continue
            def mover(mm, c=c):
                X, Y = int(mm.group(1)), int(mm.group(2))
                nx = X + c['x0'] + c['bw'] // 2 - c['ww'] // 2
                ny = Y + c['y0'] + c['bh'] // 2 - c['hh'] // 2
                return 'Escenario(%d,%d,gnivel,%d,' % (nx, ny, c['code'])
            part, n = re.subn(r'Escenario\(\s*(\d+)\s*,\s*(\d+)\s*,\s*gnivel\s*,\s*%d\s*,' % c['code'], mover, part)
            if n < 1:
                sys.exit('ERROR: recorte fase %d mapa %d: no encuentro el Escenario' % (stage, c['code']))
        parts[k] = part
    t = t[:n0] + ''.join(parts) + t[n1:]
    print('   recortes aplicados:', len(CROPS))

# 20. Panel de diagnostico en pantalla (esquina superior izquierda, con la fuente de digitos) -------------
#     arriba -> abajo: ms de carga del FPG de fase, ms de carga de la dureza, RAM libre en KB, FPS reales.
#     Se ve hasta el siguiente cambio de fase. Para quitarlo: diag=0 en la declaracion.
sub('    int gdureza; int glingo; int t_dur;', '    int diag=1; int d_fase; int d_dur; int d_ram;   // panel de diagnostico\n    int gdureza; int glingo; int t_dur;',
    literal=True, what='globales diag')
sub('  say("[goody] dureza fase "+stage+": "+(get_timer()-t_dur)+" ms, id "+gdureza+", RAM libre "+(memory_free()/1024)+" KB");',
    '  d_dur=get_timer()-t_dur; d_ram=memory_free()/1024;\n  say("[goody] dureza fase "+stage+": "+d_dur+" ms, id "+gdureza+", RAM libre "+d_ram+" KB");',
    literal=True, what='diag dureza')
sub('   write_delete(txtc);\n',
    '   write_delete(txtc);\n   d_fase=get_timer()-t0;\n   if (diag) write_var(l_money,12,12,0,d_fase); write_var(l_money,12,40,0,d_dur); write_var(l_money,12,68,0,d_ram); write_var(l_money,12,96,0,fps); end\n',
    literal=True, what='diag overlay')


# 21. MANDO DE DREAMCAST como configuracion por defecto -----------------------------------------------
#     El port genera, ademas del joystick, estas teclas (sdl_dc_input.c):
#       cruceta y stick -> flechas · A -> Ctrl · B -> Alt · X -> Espacio · Y -> Shift izq. · START -> Enter
#     Mapeo elegido:  mover = cruceta o stick (analogico/digital) · A = lanzar ladrillos (mantener y soltar)
#                     X = poner/recoger escalera · Y o arriba = saltar · START = pausa · B = cancelar
#     Se usan TECLAS y botones de joystick a la vez (si uno de los dos caminos falla, el otro sigue).
sub('    teclado[KSPACE]=_SPACE;\n    teclado[KENTER]=_ENTER;\n',
    '    teclado[KSPACE]=_CONTROL;      // A  = lanzar ladrillos (en PC era Espacio)\n    teclado[KENTER]=_SPACE;        // X  = escalera          (en PC era Enter; en la DC Enter es START)\n',
    literal=True, what='teclas por defecto')
#     ladrillos: boton A (antes X)
def ladrillos(m):
    return m.group(0).replace('JOY_BUTTON_X', 'JOY_BUTTON_A')
t, n_l = re.subn(r'(?m)^.*teclado\[KSPACE\].*(?:potencia<=14|AND disparo).*$', ladrillos, t)
if n_l != 4:
    sys.exit('ERROR (ladrillos): se esperaban 4 lineas y hay %d' % n_l)
#     escalera: boton X (antes B)
sub('If ((key(teclado[KENTER]) or get_joy_button(JOY_BUTTON_B)>0) AND ascensor==0 AND barca==0)',
    'If ((key(teclado[KENTER]) or get_joy_button(JOY_BUTTON_X)>0) AND ascensor==0 AND barca==0)', literal=True, what='escalera poner')
sub('While(key(teclado[KENTER])or get_joy_button(JOY_BUTTON_B)>0) Frame; End',
    'While(key(teclado[KENTER])or get_joy_button(JOY_BUTTON_X)>0) Frame; End', literal=True, what='escalera soltar')
sub('If ((coger AND (key(teclado[KENTER]) or get_joy_button(JOY_BUTTON_B)>0)) OR Ascen2)',
    'If ((coger AND (key(teclado[KENTER]) or get_joy_button(JOY_BUTTON_X)>0)) OR Ascen2)', literal=True, what='escalera recoger')
sub('If (get_joy_button(JOY_BUTTON_B)>0); While(get_joy_button(JOY_BUTTON_B)>0) Frame; End End',
    'If (get_joy_button(JOY_BUTTON_X)>0); While(get_joy_button(JOY_BUTTON_X)>0) Frame; End End', literal=True, what='escalera recoger 2')
#     saltar: Y tambien por tecla (Shift izq.)
sub('(get_joy_button(JOY_BUTTON_Y)>0) or Joys_Y==1) AND', '(get_joy_button(JOY_BUTTON_Y)>0) or key(_l_shift) or Joys_Y==1) AND', literal=True, what='saltar')
#     pausa: START (Enter por tecla); Ctrl ya no, porque Ctrl es el boton A (ladrillos)
sub('If ( ( key_down(_control) or get_joy_button(JOY_BUTTON_START) ) AND pausado==false',
    'If ( key_down(_enter) AND pausado==false', literal=True, what='pausa')
#     confirmar: A tambien por tecla
sub('return key(_enter) OR key(_space) OR get_joy_button(JOY_BUTTON_START)',
    'return key(_enter) OR key(_space) OR key(_control) OR get_joy_button(JOY_BUTTON_START)', literal=True, what='confirm control')
#     cancelar: B tambien por tecla (Alt izq.). Todas las lecturas de B que no sean ">0" (las de escalera ya son X).
n_b = len(re.findall(r'get_joy_button\(JOY_BUTTON_B\)(?!\s*>)', t))
t = re.sub(r'get_joy_button\(JOY_BUTTON_B\)(?!\s*>)', '(get_joy_button(JOY_BUTTON_B) OR key(_alt))', t)
print('   mando DC: %d lecturas del boton B ahora tambien por tecla Alt' % n_b)


# 22. Frecuencia de la logica dentro de una fase, en un solo sitio ---------------------------------------
#     Al terminar cada cortinilla el proceso `cortina` fija set_fps(25,0): esa es la velocidad de juego.
#     La pantalla de la DC va a 60 Hz y 60/25 = 2,4: unos fotogramas duran 2 refrescos y otros 3, y el scroll
#     "tropieza". Para probar sin tocar nada mas: FPS_JUEGO 30 (2 refrescos exactos, el juego va un 20 % mas
#     rapido) o 20 (3 refrescos exactos, un 20 % mas lento). Menus, ayuda y creditos no se tocan.
n_fps = t.count('set_fps(25,0)')
if n_fps != 1:
    sys.exit('ERROR (fps): se esperaba 1 set_fps(25,0) y hay %d' % n_fps)
t = t.replace('set_fps(25,0)', 'set_fps(FPS_JUEGO,0)')
sub('#define put_screen(f,g)', '#define FPS_JUEGO 25      // fotogramas por segundo de la logica DENTRO de una fase (ver LEEME)\n#define put_screen(f,g)', literal=True, what='define fps')

# 23. START = SOLO pausa; cada boton con una unica funcion en juego -----------------------------------------
#     - El mando de Dreamcast no tiene "Back". Segun como numere Bennu los botones, JOY_BUTTON_BACK cae en
#       START (boton 4 del joystick) o no existe; en cualquier caso en la DC sobra: se anula en todo el juego.
#       (Antes START podia abrir "Abandonar" y a la vez pausar, y en los menus cancelar y confirmar a la vez.)
#     - En la pantalla de pausa solo START o B reanudan (antes tambien Ctrl, Espacio, es decir A y X: reanudar
#       con X ponia la escalera, con A empezaba a cargar un ladrillo).
#     - Y en la pausa abre "Abandonar" (antes solo se abria con Esc, que la DC no tiene).
n_back = len(re.findall(r'get_joy_button\(\s*JOY_BUTTON_BACK\s*\)', t))
t = re.sub(r'get_joy_button\(\s*JOY_BUTTON_BACK\s*\)', '0', t)
print('   JOY_BUTTON_BACK anulado en %d sitios' % n_back)
m = re.search(r'Process pausar\(\)\nPrivate\n.*?    descargar_gmenu\(\);\nEnd\n', t, flags=re.S)
if not m:
    sys.exit('ERROR: no encuentro Process pausar')
t = t[:m.start()] + '''Process pausar()
Private
    int efecto;
    int direccion;
    int abandonar;
begin
    frame;
    x=320; y=200;
    cargar_gmenu(1);
    file=gmenu; graph=43;
    z=-200;
    efecto=256;
    Direccion=1;
    Loop
        //-- Dreamcast: START (Enter) o B (Alt) reanudan; Y (Shift) abandona la partida --//
        If (key_down(_enter) OR key_down(_alt))
            frame;
            pausado=false; Break;
        End
        If (key_down(_l_shift))
            frame;
            pausado=false; abandonar=1; Break;
        End

        If (direccion==1)
            efecto-=10;
            If (efecto<=150) direccion=2; End
        Else
            efecto+=10;
            If (efecto>246) direccion=1; End
        End
        alpha=efecto;

        Frame;
    End
    while(key(_enter) OR key(_alt) OR key(_l_shift)) frame; end
    descargar_gmenu();
    If (abandonar) Abandona(320,200,-100); End
End
''' + t[m.end():]


# 14. Tipos de parametros = tipos de las variables locales predefinidas de TU bgdc ---------
#     Goody es de la rama master de BennuGD2 (z = DOUBLE). El bgdc 2.0.0 del kit define
#     INT z, DOUBLE x,y,size, INT file,graph,angle,flags,region, BYTE alpha, y rechaza
#     "double z" con: error: Parameter type invalid (token error: "Z").
PRE = {'x': 'double', 'y': 'double', 'z': 'int', 'file': 'int', 'graph': 'int',
       'size': 'double', 'angle': 'int', 'flags': 'int', 'region': 'int',
       'alpha': 'byte', 'ctype': 'int', 'cnumber': 'int'}
TYPES = {'int', 'double', 'float', 'byte', 'word', 'dword', 'string', 'int64', 'short', 'long', 'char'}
HDR = re.compile(r'^([ \t]*(?:declare[ \t]+)?(?:process|function)[ \t]+(?:(?:int|double|float|string|byte|word|dword)[ \t]+)?\w+[ \t]*)\(([^)]*)\)', re.I | re.M)
changed_hdr = 0
changed_par = 0
def fix_header(m):
    global changed_hdr, changed_par
    params = [p.split() for p in m.group(2).split(',')]
    cur = 'int'; eff = []
    for toks in params:
        if not toks:
            return m.group(0)
        if len(toks) >= 2 and toks[0].lower() in TYPES:
            cur = toks[0].lower()
        name = toks[-1]
        e = cur
        if name.lower() in PRE and PRE[name.lower()] != cur and (len(toks) >= 2 or True):
            # solo se fuerza si el parametro lleva tipo explicito o hereda uno distinto
            e = PRE[name.lower()]
        eff.append((e, name, cur))
    # sin cambios si ningun parametro predefinido discrepa
    if all(e == c for e, n, c in eff):
        return m.group(0)
    out = []; emitted = 'int'
    for e, name, c in eff:
        if e != emitted:
            out.append('%s %s' % (e, name)); emitted = e
        else:
            out.append(name)
    changed_hdr += 1
    changed_par += sum(1 for e, n, c in eff if e != c)
    return '%s(%s)' % (m.group(1), ', '.join(out))
t = HDR.sub(fix_header, t)
print('   tipos de parametros: %d cabeceras corregidas (%d parametros)' % (changed_hdr, changed_par))

open(dst, 'w', encoding='latin-1', newline='\n').write(t)
print('escrito', dst)
