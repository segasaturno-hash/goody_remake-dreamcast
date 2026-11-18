#!/bin/bash
set -e
J=~/bennudc/goody/goody-dc/juego
cd $J
~/bennudc/dc/host/bgdc tcarga.prg | grep -iE 'error|compiled'
R=$(mktemp -d)
trap "rm -rf $R" EXIT
mkdir -p $R/data1 $R/data2
cp $J/data1/niv_*.fpg $J/data1/dur_*.png $R/data1/
cp $J/data2/musica1.gdt $R/data2/
rm -f ~/bennudc/dc/build-dc/obj/port_*.o
EXTRA_DC_CFLAGS="$1" bash ~/bennudc/dc/make-gdi.sh $J/tcarga.dcb $R TCARGA ~/bennudc/goody/gdi-tc 2>&1 | grep -iE 'error|area de' | head
