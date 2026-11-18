#!/bin/bash
# Compila Goody y hace la GDI. Uso: g_build.sh [prg] [salida] [CFLAGS extra]
set -e
J=~/bennudc/goody/goody-dc/juego
PRG=${1:-Goody.prg}
OUT=${2:-~/bennudc/goody/gdi}
cd $J
~/bennudc/dc/host/bgdc $PRG | grep -iE 'error|compiled|warning' || true
DCB=$J/${PRG%.prg}.dcb
[ -f $DCB ] || exit 1
R=$(mktemp -d)
trap "rm -rf $R" EXIT
mkdir -p $R
cp -r $J/data1 $J/data2 $R/
[ -f $J/TITLE.TXT ] && cp $J/TITLE.TXT $R/
for f in $J/*.TXT; do [ -f "$f" ] && cp "$f" $R/; done
rm -f ~/bennudc/dc/build-dc/obj/port_*.o
EXTRA_DC_CFLAGS="$3" bash ~/bennudc/dc/make-gdi.sh $DCB $R GOODY $OUT 2>&1 | tail -3
ls -la $OUT
