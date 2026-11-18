# Goody (BennuGD2/games/Goody) para tu BennuGD2 Dreamcast

**Estado: SIN COMPILAR NI PROBAR.** En mi entorno no hay `bgdc` para Linux, no hay Wine para ejecutar
tu `bgdc.exe` y no tengo red para construirlo.

**v2 (corrige el primer error de compilación):** `Goody.prg:18: Parameter type invalid (token error: "Z")`.
Goody es de la rama master de BennuGD2, donde `z` es `double`. Tu `bgdc` 2.0.0 define `INT z` (y `BYTE alpha`),
y rechaza `double z` en los parámetros. Se corrigen 160 parámetros en 157 cabeceras (`double z` -> `int z`,
`int alpha` -> `byte alpha`, sin cambiar el tipo de `size`, que sí es `DOUBLE`). Los tipos salen de las
cadenas de tu propio `bgdc.exe`.

**v11 - cada botón una sola función:**
- **START = solo pausa.** En la pantalla de pausa reanudan START o B; Y abre "Abandonar". Antes reanudaban también Ctrl
  y Espacio (los botones A y X del port): reanudar con X ponía la escalera y con A empezaba a cargar un ladrillo.
- **`JOY_BUTTON_BACK` anulado en todo el juego (26 sitios).** La DC no tiene Back; según cómo numere Bennu los botones
  del joystick, el botón 4 (que en el port es START) cae en BACK. Así START podía abrir "Abandonar" a la vez que pausaba
  y, en los menús, cancelar y confirmar a la vez. En juego START ya solo se lee por la tecla Enter.
- Resumen: A = ladrillos · X = escalera · Y/arriba = saltar · START = pausa · B = cancelar/reanudar · mover = cruceta o stick.

**v10 - mando de Dreamcast por defecto, y hallazgos del renderizador:**
- **Controles** (el port genera teclas Y joystick; el juego usa los dos a la vez por si uno de los caminos falla):
  mover = cruceta o stick (analógico/digital) · **A = lanzar ladrillos** (mantener y soltar) · **X = poner/recoger
  escalera** · Y o arriba = saltar · **START = pausa** · **B = cancelar** (menús, Continuar?, Abandonar,
  Conforme S/N). Antes: ladrillos = Espacio/X, escalera = Enter/B, pausa = Ctrl/START. Ctrl es el botón A del port,
  así que dejó de ser pausa. Las teclas por defecto son `teclado[KSPACE]=_CONTROL` y `teclado[KENTER]=_SPACE`.
- **Causa probable del "no puedo salir" y del START en Redefinir:** START genera la tecla Enter y Enter confirma;
  B solo cancelaba por joystick. Ahora B cancela también por la tecla Alt, que es lo que genera el port.
- **`FPS_JUEGO`** (arriba del todo, `#define FPS_JUEGO 25`): velocidad de la lógica dentro de las fases. La pantalla va
  a 60 Hz y 60/25 = 2,4: unos fotogramas duran 2 refrescos y otros 3, y el scroll tropieza. Prueba 30 (2 refrescos
  exactos, el juego va un 20 % más rápido) o 20 (3 exactos, un 20 % más lento).
- **Renderizador del port (`sdl_dc_video.c`), leído entero:** TODO se dibuja en la lista translúcida del PVR con
  orden por profundidad y texturas de 16 bits SIN twiddle. El PVR trata cada capa translúcida a pantalla completa
  píxel a píxel (sin descartar lo oculto, como hace con la lista opaca). El mapa principal de una fase es opaco
  solo en un 33-67 % (el resto es alfa 0), así que lo adecuado serían la lista de punch-through (alfa 0/255) o
  opaca. Eso exige un buffer de comandos de dibujo por lista y no se puede hacer a ciegas: es un cambio en C del
  port.

**v9 - baldosas (tiles) estudiadas, y FPS en el panel:**
- Mapa 1 de `gnivel1` (1920x320), baldosas únicas probando TODAS las alineaciones de la rejilla y con espejos:
  8x8 -> 34 % (3.197 de 9.600) · 16x16 -> 50 % · 32x32 -> 67 %. Ninguna alineación mejora de forma apreciable
  (35 % -> 34 %), así que el arte no se construyó sobre una rejilla de baldosas: está pintado. Tolerando baldosas
  casi iguales (hasta 8 de 64 píxeles distintos) en 8x8 solo se baja al 22 %.
- Coste: en 8x8 una pantalla de 640x320 son 3.200 baldosas por fotograma; en 16x16, 800. El motor no tiene
  tilemap; hacerlo con procesos sería 800-3.200 procesos (medido en tu MEDICIONES: 100 entidades = 92 ms/fotograma),
  y hacerlo bien exige una función en C nueva en el port (dibujar una rejilla de baldosas con una sola llamada).
- Las fases crean pocos procesos (media 13 llamadas a Process al empezar, máximo 33): el cuello de botella no
  parece ser el número de procesos al arrancar.
- **El panel de diagnóstico tiene ahora cuatro números** (arriba -> abajo): ms de carga del FPG de la fase,
  ms de carga de la dureza, RAM libre en KB y **FPS reales** (la variable `fps` de Bennu). Con los FPS se ve en
  qué fases el juego va lento y cuánto.

**v8 - análisis de colores de todos los FPG (se puede ver en `analisis-graficos-goody.png`):**
- **Fondos 98/99** (cielo con nubes y estrellas): idénticos en los 4 FPG de nivel, 5 colores, 2,4 % opaco. Solo
  se dibujan en las fases cuyo `scroll_start` pasa `g_fondo` como fondo (17 de 32), pero los FPG de fase los
  cargaban todos. Ahora solo los llevan esas 17: las otras 15 pierden 0,41 M px de RAM (~40 % de la fase).
- **4 bits:** entre los mapas de fase solo cumplen <=15 colores esos fondos y dos capas de objetos; el arte de
  los niveles usa ~90-119 colores. Sprites: 75 de 98 enemigos y 5 de 25 de Goody caben en 4 bits, pero suman
  ~0,1 M px (50 KB). Además el FPG de Bennu solo existe a 1, 8, 16 y 32 bits, y tu port crea texturas
  ARGB4444: 4 bits no se traduce en menos memoria sin cambiar el motor.
- Los sprites de Goody miden 62x45 con 17-25 colores; los enemigos, 11-40. El mapa de fase 1 de `gnivel1`
  (1920x320) usa 118 colores.

**v7 - estudio de memoria y recorte de capas vacías:**
- **Cómo pesa cada formato en tu port** (leído de `sdl_surface.c` y `sdl_dc_video.c`):
  FPG de 8 bits = 1 byte/píxel en RAM (superficie INDEX8) · FPG de 16 bits = 2 · PNG/`map_load` = 4 (RGBA8888;
  2 con BGD16.TXT) · en VRAM todo es ARGB4444 (2 bytes/píxel) en piezas de hasta 1024 redondeadas a potencia
  de 2 (1920x320 = 1,25 MB; 640x320 = 0,4 MB) y **la textura vive hasta que se descarga el mapa**. El formato
  del archivo (PNG indexado, zlib) solo cambia el disco, no la RAM ni la VRAM.
- **Los gráficos de nivel (38 mapas visibles, 20,4 M px) se repiten poco**: en baldosas de 8x8 solo el 16,5 % son
  únicas, de 16x16 el 30 %. Comprimen 36x con zlib porque son degradados y zonas planas, no porque repitan
  tiles. Un sistema de tilemap no ahorraría tanto como en una NES y exigiría un módulo en C para dibujar.
- **Por qué no mantener un grupo de fases entero en RAM:** en RAM cabría (4,9-6,1 M px = MB a 8 bits), pero cada
  fase dibujada crea sus texturas (2,5-3,3 MB de VRAM) y no se liberan hasta descargar el mapa: con ~4,3 MB de VRAM
  libres se llenaría a la segunda fase. Por eso se recarga por fase.
- **Hecho:** cuatro capas de objetos eran casi todo transparentes (fase 1 mapa 90: 1920x320 con un 3 % opaco; fase
  21 mapa 92; fase 22 mapa 93; fase 26 mapa 90). Se recortan a su caja y el `Escenario` se recoloca en el centro
  de la caja; comprobado píxel a píxel en pantalla (idénticos). En la fase 1, la primera que se juega, baja de
  ~3,3 MB a ~2,1 MB de VRAM y de 1,6 MB a ~1,1 MB de RAM. Coordenadas en `tools/crops.json`.
- **Panel de diagnóstico en pantalla** (esquina superior izquierda, dígitos dorados), de arriba abajo: ms de carga
  del FPG de la fase · ms de carga de la dureza · RAM libre en KB. Se ve hasta el siguiente cambio de fase. Se quita
  con `diag=0` en la declaración global. Con esto se ve cuánto tarda cada cambio de fase sin mirar la consola.

**v6 - prueba de FPG optimizados (datos medidos en el PC, no en la Dreamcast):**
- Las fases ya eran FPG de **8 bits con paleta** (`gnivel1..4`, `gscore`, `ggoody`, `genemigos`, `gscena*`);
  solo `gmenu` y `logos` eran de 16 bits. Los 601 KB de `niv_00.fpg` son 8 bits *sin comprimir*.
- Prueba con `gnivel1`: 24 mapas, 7,37 MB en bruto -> **0,35 MB** como PNG indexado optimizado.
  Las 32 fases juntas: 33,6 MB en bruto -> **0,93 MB con zlib** (36 veces menos). `niv_00`: 601 KB -> 15 KB.
- Lo que NO se puede hacer: cargar todo el juego de una vez. El tamaño en disco es irrelevante para eso; cuenta
  lo descomprimido: los mapas de nivel suman 26,4 millones de píxeles (84 mapas) = 26 MB a 8 bits y 105 MB a
  32 bits (tu port convierte PNG a RGBA8888, 4 bytes/píxel, así que **extraer a PNG sube la RAM**, no la baja).
  Un grupo de nueve fases son 7,4 MB a 8 bits, y solo cabrían si el port mantiene las superficies de 8 bits
  como INDEX8 (no lo he podido verificar) y aun así sobraría muy poco.
- Cambio: **todos los FPG van comprimidos con zlib** (Bennu detecta gzip por el contenido; el original ya iba
  así). Motivo: en un GD-ROM real leer 1,6 MB cuesta más que descomprimir 43 KB. Descomprimir las 32 fases
  tarda 54 ms en un PC (1,7 ms por fase); en la SH4 será bastante más, pero no lo he medido.
- Para comparar sin recompilar: `prueba-sin-comprimir/data1/niv_*.fpg` son las mismas fases sin comprimir.
  Cópialas encima de `juego/data1/` y compara las líneas `[goody] fase N cargada en X ms` de la consola.
- El texto pegado describe el port clásico de BennuGD1 (render por software). El tuyo es otro: PVR, texturas
  de 16 bits en VRAM sin twiddle, en piezas de hasta 1024 con tamaño potencia de 2 (`sdl_dc_video.c`); un mapa de
  1920x320 ocupa 2 piezas de 1024x512 = 2 MB de VRAM para 1,2 MB útiles.

**v5 - colisiones y cargas de fase:**
- **Colisiones.** Goody lee la dureza con `map_get_pixel` y compara con 5 constantes que dependen de
  `map_info(...,g_depth)`: índices de paleta (8 bits: 90, 30, 20, 110, 87) o `0xRRGGBBAA` (32 bits). Las
  constantes de 32 bits son exactamente la paleta del FPG x4 (la paleta es de 6 bits; comprobado: 0x3f*4=0xfc).
  Tu port convierte las superficies a RGBA8888 cuando se leen (`patch_bitmap.py`) y ninguno de sus ejemplos
  lee píxeles de un FPG de 8 bits con paleta (Pacman usa PNG). Si `map_info` dice 8 y `map_get_pixel` devuelve
  RGBA, ninguna comparación acierta y todo es "aire": Goody se cae por el suelo. Ahora la dureza va en
  `data1/dur_NN.png` (RGBA, mismos colores) cargada con `map_load` y `set_mapa_dureza` usa siempre las
  constantes de 32 bits. Los 32 PNG están comprobados con un lector independiente (contienen exactamente
  0x4040fcff, 0xe8e8fcff, 0xfce888ff y 0x6c00ff). Los lingotes del banquero (que leían el mapa 11) usan una
  máscara a media resolución (`lin_28.png`).
- **La carga de "casi un minuto" del ascensor** (hipótesis, no medida): `PRINCIPAL` cambia de fase cuando
  `goodi.y>296`; con la dureza rota Goody sigue cayendo y encadena cambios de fase, cada uno con su
  `fpg_load`. Arreglada la dureza deja de encadenarse.
- **Cada cambio de fase sigue cargando un FPG** (0,6-1,6 MB). El juego original ya hace
  `fpg_unload`+`fpg_load` en cada `Nivel`; en PC es instantáneo. Ahora se muestra "CARGANDO..." y la consola
  escribe `[goody] fase N cargada en X ms, RAM libre Y KB` y `[goody] dureza fase N: X ms ...`. Con esos
  números se decide si se puede tener un grupo de fases entero en RAM (sin cargas entre pantallas).
- La dureza ya no está dentro de los FPG de fase (menos que cargar).

**v4:**
- **Intro:** todo el juego (menú, marcador, Goody, enemigos, decorados y los 3 logos) se carga al principio,
  con un "CARGANDO...", ANTES de que empiece la música. Durante los logos no se carga nada (cargar con la
  música sonando la cortaba). Para que quepa, los logos OPERA y COPTRON se recortan a su caja (eran 640x480
  casi todo negro: ahora 480x105 y 365x141) y se dibujan en el mismo sitio.
- **Música en las cargas:** al cargar una fase, el menú o una página de ayuda con música sonando, el volumen
  baja a 0 durante la carga y se restaura (`volumen`), para que no se oiga el corte.
- **B = cancelar:** en este juego `confirm()` incluía B (con A, X, Y y Enter). En Opciones, B se leía como
  "confirmar" y reabría la opción (Redefinir), por eso no se podía salir; en PC se sale con Esc o con el
  botón Back, que la Dreamcast no tiene. Ahora `confirm()` = Enter/START, Espacio, A, X, Y, y B solo cancela
  (Opciones, Configurar, Continuar?, Abandonar, y "Conforme S/N").
- **Redefinir:** al terminar espera a soltar todos los botones antes de devolver el control.
  Durante las 6 pulsaciones de redefinir NO se puede cancelar con B (B puede ser una de las teclas a asignar);
  al final, B = "N" descarta los cambios.

Lo que sí he comprobado:
- Todas las funciones, constantes (`_F5`, `JOY_BUTTON_*`, `S_FREEZE`...) y miembros de struct
  (`scroll[0].ratio`, `keyboard.scan_code`...) que usa el programa existen en tu `bgdc.exe`.

- Los 106 ficheros que nombra `Goody.prg` existen en `juego/data1` y `juego/data2`.
- Los 66 FPG generados tienen estructura válida (cada mapa mide lo que dice su cabecera).
- Cada cambio del `.prg` lo hace `tools/patch_goody.py`, que se para si el original no es el esperado.

## Cómo probarlo

```
probar.bat goody-dc\juego\Goody.prg
```
(el kit copia `data1/` y `data2/` al disco y no copia `.prg`). Si `bgdc` da un error, pásamelo tal cual.

## El problema: la memoria

El juego carga FPG enteros. Descomprimidos: `gnivel1..4` 6-7 MB cada uno (8 bits), `gmenu` 12 MB,
`logos` 26 MB (42 fotogramas 640x480). Con 16 MB de RAM no cabe. Cada fase solo usa 4-5 mapas de su
FPG, así que lo troceo conservando **los mismos códigos de mapa**: el código del juego apenas cambia.

| Original | Ahora |
|---|---|
| `gnivel1..4.gdg` (4 FPG) | `niv_00..31.fpg`, uno por fase: mapas visibles y fondos 98/99; dureza en `dur_NN.png` |
| `gmenu.gdg` 12 MB | `gmenu.fpg` 1,7 MB (+ `gmenui.fpg` de 0,4 MB para dentro de la partida) |
| 11 páginas de ayuda dentro de gmenu | una por fichero (`ay1_29.fpg`...), cargadas al pasar página |
| créditos (60-64, 50-58) dentro de gmenu | `gcr1.fpg`, solo mientras ruedan los créditos |
| `logos.gdg` 42 fotogramas | `logo1/2/3.fpg`: 3 fotogramas (OPERA soft y Coptron recortados) |
| `gscore.gdg` con 2 mapas 640x480 | sin ellos (solo servían para las *scanlines*) |
| `musica1/intro1/final_2.gdt` (WAV 16 bits, 16 MB) | WAV ADPCM Yamaha, 4 MB; los 40 efectos no cambian |
| `final.gdm` (video Theora 23 MB) | omitido |

Los FPG de las fases, `gscore`, `ggoody`, `genemigos` y `gscena*` van sin comprimir (el cargador no
necesita zlib y es más rápido).

### Lo que NO sé: si cabe

Mi cálculo, suponiendo 4 bytes por píxel (el peor caso) y 2,9 MB de gráficos siempre cargados:

| fase | RAM de gráficos |
|---|---|
| 14 | 10,6 MB |
| 8 | 10,2 MB |
| 1, 19, 21 | 10,0 MB |
| resto | 6-8,5 MB |

Tu `MEDICIONES.md` deja ~9 MB libres con Pacman, y el .dcb, los sonidos y la VRAM también cuentan. **Las
cinco fases grandes pueden quedarse sin memoria.** Si el port mantiene los mapas de 8 bits como INDEX8
(el juego tiene una rama `case 8:` en `set_mapa_dureza`), serían 4 veces menos y no habría problema.
Lo dirá el informe `[mem]` de `-DBGD_DC_TRACE`: mídelo en esas fases. Si falta memoria, las palancas son
`BGD16.TXT` (ojo: el juego compara colores de dureza con constantes de 32 bits o por índice de paleta;
con ARGB1555 hay que comprobarlo) o quitar uno de los dos fondos 98/99 (0,8 MB).

## Cambios en Goody.prg (diff completo: `diff tools/Goody.original.prg juego/Goody.prg`)

1. Sin `import "mod_debug"` (no se usa nada de él).
2. `main()`: sin `desktop_get_size`, `window_move`, `window_set_title`, `screen.fullscreen`, sin el
   lanzador de 320x240 (`s_window`); `set_mode(640,480)` una vez. Los conmutadores de pantalla completa
   (F3 y la opción del menú) ya no reinician el vídeo. Idioma 1 por defecto (en Opciones se puede cambiar).
3. `Ini_files`: carga `data1/niv_NN.fpg` según la fase.
4. `cargar_gmenu(tipo)` / `descargar_gmenu()`: `gmenu` completo en menús, mínimo dentro de la partida;
   `menu_inicio()` libera la fase y recarga el menú completo al volver.
5. `Ayuda` carga una página cada vez (`ayuda_pagina`); F5 en partida ya no carga `gmenu`.
6. `OPERA`: la secuencia de logos con 3 fotogramas.
7. `video_final`: sin vídeo; pasa directamente a los créditos, que cargan `gcr*.fpg`.

El resto del juego no se ha tocado.

## Riesgos que veo (por orden)

- Memoria en las fases grandes (arriba).
- Rendimiento: el juego usa `scroll_start` con mapas de 1920x320 y llama a `map_get_pixel` muchas veces
  por fotograma (colisiones). Tu PENDIENTE ya apunta a los scrolls como punto débil.
- Mando: el juego usa `get_joy_button`, `get_joy_position` y `JOY_BUTTON_*`; la pausa es Ctrl o START y
  tu kit asigna A = Ctrl y START = Enter. Puede que haya que ajustar qué botón hace qué.
- Eliminé el vídeo final y 39 fotogramas de logos: es contenido que se pierde.
- Cambio de idioma en el menú: recarga `gmenu`; no lo he podido ver funcionar.

## Regenerar

```
python3 tools/prepare_assets.py <carpeta Goody original> <salida>   # necesita ffmpeg y numpy
python3 tools/patch_goody.py Goody.original.prg Goody.prg crops.json   # crops.json lo escribe prepare_assets.py
```
