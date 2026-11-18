# Goody (remake) para Dreamcast

Port del remake de Goody (BennuGD2) a Dreamcast con el port de BennuGD2 para KallistiOS
(github.com/segasaturno-hash/bennugd2-dreamcast).

- `goody-dc/juego`: el juego (prg y datos) con los parches para Dreamcast (`tools/patch_dc_*.py`):
  todo a RAM al principio (DC_PRELOAD), sin pausas de carga ni cortes de musica, durezas
  en .map de 8 bits, menu sin opciones de PC, ayuda y creditos arreglados.
- `goody-dc/juego/tools`: parches y herramientas de datos (extraer_fpg.py, dur_a_map.py...).
- `original`: ficheros del juego original usados para los creditos (gmenu.gdg, gmenu2.gdg).
- `g_build.sh [prg] [salida] [CFLAGS]`: compila y monta el GDI.
