#!/bin/bash
# GDI de Goody con el perfilador de opcodes (-DBGD_DC_PROF). Despues deja el interprete
# marcado para recompilarse sin el en la siguiente compilacion normal.
set -e
S=~/bennudc/bgd-v2.1.0
touch $S/core/bgdrtm/interpreter.c $S/core/common/debug.c
bash ~/bennudc/goody/g_build.sh Goody.prg ~/bennudc/goody/gdi-prof -DBGD_DC_PROF 2>&1 | grep -iE 'error|FALLO|compiled|track03' || true
touch $S/core/bgdrtm/interpreter.c $S/core/common/debug.c
