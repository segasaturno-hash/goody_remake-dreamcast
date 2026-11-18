#!/usr/bin/env python3
"""
Prepara los recursos de GOODY (BennuGD2/games/Goody) para la Dreamcast.

Problema: la Dreamcast tiene 16 MB de RAM y 8 MB de VRAM. Los FPG originales
(gnivel1..4, gmenu, logos) pesan 6-25 MB *descomprimidos* y el juego los carga
enteros. Aqui se trocean en ficheros pequenos con los MISMOS codigos de mapa,
asi el codigo del juego casi no cambia (solo cuando carga cada fichero).

Salida (todo en minusculas y nombres 8.3, para ISO9660/romdisk):

  data1/niv_NN.fpg      una fase: sus mapas visibles + fondos 98/99   (NN = stage)
  data1/dur_NN.png      mapa de dureza (colisiones) de esa fase, RGBA con las constantes de 32 bits
  data1/lin_28.png      mascara de lingotes (fase del banquero), media resolucion
  data1/gmenu.fpg       menu (idioma 1): sin ayuda, sin fondos de creditos, sin 2/3/90
  data1/gmenu2.fpg      idem, idioma 2
  data1/gmenui.fpg      solo los 13 graficos que se usan DENTRO de una partida (pausa,
  data1/gmenui2.fpg     game over, continuar): ~0,8 MB en vez de ~3,5 MB
  data1/ay1_29.fpg ...  una pagina de ayuda por fichero (idioma 1: ay1_, idioma 2: ay2_)
  data1/gcr1.fpg        fondos animados + textos de los creditos (idioma 1)
  data1/gcr2.fpg        idem, idioma 2
  data1/logo1..3.fpg    solo 3 fotogramas del logo (20, 42, 22); los 2 primeros recortados a su caja
  data1/gscore.fpg      marcador sin los mapas 99/100 (640x480, solo scanlines)
  data1/ggoody.fpg ...  el resto de FPG, tal cual pero sin comprimir
  data2/*.gdt           efectos sin cambios; musica larga a WAV ADPCM Yamaha
  (final.gdm, el video Theora de 23 MB, NO se copia: la Dreamcast no lo reproduce)

Uso:  prepare_assets.py <carpeta_goody_original> <carpeta_salida> [--raw]
      (por defecto los FPG se escriben comprimidos con zlib; --raw los deja sin comprimir)
Necesita: python3, numpy, ffmpeg.
"""
import gzip, os, re, shutil, struct, subprocess, sys

# ----------------------------------------------------------------- FPG -----
def read_fpg(path):
    raw = open(path, 'rb').read()
    try:
        d = gzip.decompress(raw)
    except OSError:
        d = raw
    magic = d[:3]
    depth = {b'fpg': 8, b'f16': 16, b'f32': 32, b'f24': 24, b'f01': 1}[magic]
    hdr_len = 8 + (768 + 576 if depth == 8 else 0)
    header = d[:hdr_len]
    recs = {}
    pos = hdr_len
    while pos < len(d) - 4:
        code, rl = struct.unpack('<ii', d[pos:pos + 8])
        if rl <= 0:
            raise ValueError('registro FPG corrupto en %s' % path)
        recs[code] = d[pos:pos + rl]          # registro completo, tal cual
        pos += rl
    return header, recs

GZ = True      # FPG comprimidos con zlib (Bennu los lee igual: detecta gzip por el contenido)

def write_fpg(path, header, recs, codes):
    missing = [c for c in codes if c not in recs]
    if missing:
        print('   AVISO: %s: faltan mapas %s' % (os.path.basename(path), missing))
    body = header + b''.join(recs[c] for c in sorted(codes) if c in recs)
    if GZ:
        body = gzip.compress(body, 9, mtime=0)
    with open(path, 'wb') as f:
        f.write(body)
    return os.path.getsize(path)

def map_px(rec):
    w, h = struct.unpack('<ii', rec[52:60])
    return w, h

# ------------------------------------------------- fases desde el .prg -----
def stage_maps(prg_text):
    """Por cada 'Case N:' de Process Nivel: codigos de gnivel que usa."""
    L = prg_text.split('\n')
    s = next(i for i, l in enumerate(L) if re.match(r'\s*Process Nivel', l, re.I))
    e = next(i for i, l in enumerate(L) if re.match(r'\s*//-- Carga Ficheros Graficos', l))
    cur = None
    st = {}
    for i in range(s, e):
        l = L[i]
        m = re.match(r'^\s{6}Case (\d+):', l)
        if m:
            cur = int(m.group(1)); st.setdefault(cur, set()); continue
        if cur is None:
            continue
        for mm in re.finditer(r'gnivel\s*,\s*(\d+)', l):
            st[cur].add(int(mm.group(1)))
        for mm in re.finditer(r'set_mapa_dureza\((\d+)\)', l):
            st[cur].add(int(mm.group(1)))
    return st

def stage_dur(prg_text):
    """Por cada fase: los codigos que pasa a set_mapa_dureza()."""
    L = prg_text.split('\n')
    s = next(i for i, l in enumerate(L) if re.match(r'\s*Process Nivel', l, re.I))
    e = next(i for i, l in enumerate(L) if re.match(r'\s*//-- Carga Ficheros Graficos', l))
    cur = None; out = {}
    for i in range(s, e):
        m = re.match(r'^\s{6}Case (\d+):', L[i])
        if m: cur = int(m.group(1)); out.setdefault(cur, set()); continue
        if cur is None: continue
        for mm in re.finditer(r'set_mapa_dureza\((\d+)\)', L[i]): out[cur].add(int(mm.group(1)))
    return out

def fpg_for_stage(stage):
    if stage <= 8:  return 'gnivel1.gdg'
    if stage <= 16: return 'gnivel2.gdg'
    if stage <= 22: return 'gnivel3.gdg'
    return 'gnivel4.gdg'


# ------------------------------------------- dureza: mapas de colisiones -----
# Goody lee la dureza con map_get_pixel y compara con constantes segun la profundidad del mapa:
#   8 bits  -> indices de paleta (90, 30, 20, 110, 87)
#   32 bits -> 0xRRGGBBAA (0xfce888ff, 0x4040fcff, 0xe8e8fcff, 0x006c00ff, 0xfcfc28ff)
# La paleta de los FPG es de 6 bits (0..63) y las constantes de 32 bits son exactamente
# valor*4 (p.ej. 0x3f*4 = 0xfc): es la expansion VGA de la version oficial.
# En la Dreamcast, el camino de PNG -> RGBA8888 -> map_get_pixel esta probado (bgd-pacman); el de
# FPG de 8 bits con paleta no lo ejercita ningun ejemplo del port. Por eso la dureza se entrega
# como PNG RGBA con esos mismos colores y el juego usa siempre las constantes de 32 bits.
import zlib

def write_png_rgba(path, w, h, rgba):
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    stride = w * 4
    raw = b''.join(b'\x00' + rgba[y * stride:(y + 1) * stride] for y in range(h))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) \
          + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)

SPECIAL = {90: 0xfce888, 30: 0x4040fc, 20: 0xe8e8fc, 110: 0x006c00, 87: 0xfcfc28}

def palette_rgba(header):
    """Tabla indice -> RGBA (palette*4, alfa 255; indice 0 transparente). Los indices que no son
    'especiales' pero darian el mismo color que uno especial se desplazan 1 unidad."""
    import numpy as np
    pal = np.frombuffer(header[8:8 + 768], dtype=np.uint8).astype(np.int32) * 4
    pal = np.minimum(pal, 255).reshape(256, 3)
    lut = np.zeros((256, 4), dtype=np.uint8)
    lut[:, :3] = pal; lut[:, 3] = 255; lut[0] = (0, 0, 0, 0)
    especiales = {(c >> 16 & 255, c >> 8 & 255, c & 255) for c in SPECIAL.values()}
    dup = 0
    for i in range(1, 256):
        if i not in SPECIAL and tuple(int(v) for v in lut[i, :3]) in especiales:
            lut[i, 2] = lut[i, 2] ^ 1; dup += 1
    return lut, dup

def map_indices(rec):
    import numpy as np
    w, h = map_px(rec)
    npts = struct.unpack('<i', rec[60:64])[0]
    off = 64 + npts * 4
    return np.frombuffer(rec[off:off + w * h], dtype=np.uint8).reshape(h, w)

def dureza_png(header, rec, path):
    lut, dup = palette_rgba(header)
    a = map_indices(rec)
    h, w = a.shape
    write_png_rgba(path, w, h, lut[a].tobytes())
    return w, h, dup

def banquero_stage(prg_text):
    L = prg_text.split('\n')
    s = next(i for i, l in enumerate(L) if re.match(r'\s*Process Nivel', l, re.I) and 'declare' not in l.lower())
    cur = None
    for i in range(s, len(L)):
        m = re.match(r'^\s{6}Case (\d+):', L[i])
        if m: cur = int(m.group(1))
        if 'Banquero(610,154' in L[i]: return cur
    raise SystemExit('no encuentro la fase del banquero')

LIN_X0, LIN_Y0 = 544, 14       # origen del recorte de la mascara de lingotes (la usa patch_goody.py)


# ------------------------------------- recorte de mapas de objetos casi vacios -----
# Los mapas 90..93 (capas de objetos: farolas, carteles...) son de 1280x320 o 1920x320 pero casi todo
# transparente (3-19 % opaco). A 1 byte/pixel en RAM y 2 en VRAM cuestan lo mismo vacios que llenos, y
# la fase 1 (la primera que se juega) es la que mas VRAM usa. Se recortan a su caja y el codigo coloca
# el objeto en el centro de la caja (patch_goody.py lee crops.json). Solo si el mapa se usa unicamente
# como Escenario(x,y,gnivel,CODE,...) con x,y literales dentro de su fase.
import json

def stage_blocks(prg_text):
    """{fase: texto del bloque 'Case N:' de Process Nivel}"""
    L = prg_text.split('\n')
    s = next(i for i, l in enumerate(L) if re.match(r'\s*Process Nivel', l, re.I))
    e = next(i for i, l in enumerate(L) if re.match(r'\s*//-- Carga Ficheros Graficos', l))
    out = {}; cur = None
    for i in range(s, e):
        m = re.match(r'^\s{6}Case (\d+):', L[i])
        if m: cur = int(m.group(1)); out[cur] = []
        if cur is not None: out[cur].append(L[i])
    return {k: '\n'.join(v) for k, v in out.items()}

def find_crops(prg_text, st, dur_codes, group_cache):
    import numpy as np
    blocks = stage_blocks(prg_text)
    crops = {}
    for stage, codes in st.items():
        header, recs = group_cache[fpg_for_stage(stage)]
        for code in sorted(codes - dur_codes[stage]):
            if code in (98, 99) or code not in recs:
                continue
            blk = blocks.get(stage, '')
            total = len(re.findall(r'gnivel\s*,\s*%d\b' % code, blk))
            esc = re.findall(r'Escenario\(\s*(\d+)\s*,\s*(\d+)\s*,\s*gnivel\s*,\s*%d\s*,' % code, blk)
            if total == 0 or total != len(esc):
                continue                      # se usa de otra forma (scroll, etc.): no se toca
            rec = recs[code]
            if struct.unpack('<i', rec[60:64])[0] != 0:
                continue                      # puntos de control: no se toca
            a = map_indices(rec)
            hh, ww = a.shape
            ys, xs = np.where(a != 0)
            if len(ys) == 0:
                continue
            bw = int(xs.max() - xs.min() + 1); bh = int(ys.max() - ys.min() + 1)
            if bw * bh >= 0.6 * ww * hh:
                continue
            crops['%d:%d' % (stage, code)] = dict(stage=stage, code=code, x0=int(xs.min()), y0=int(ys.min()),
                                                 bw=bw, bh=bh, ww=ww, hh=hh)
    return crops

def crop_record8(rec, c):
    a = map_indices(rec)[c['y0']:c['y0'] + c['bh'], c['x0']:c['x0'] + c['bw']]
    data = a.tobytes()
    hdr = bytearray(rec[:64])
    struct.pack_into('<i', hdr, 4, 64 + len(data))
    struct.pack_into('<i', hdr, 52, c['bw'])
    struct.pack_into('<i', hdr, 56, c['bh'])
    struct.pack_into('<i', hdr, 60, 0)
    return bytes(hdr) + data

# ---------------------------------------------------------------- audio ----
def ffprobe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0

def to_adpcm(src, dst):
    # Igual que convert-audio.sh del port: ADPCM Yamaha 44,1 kHz; en estereo se
    # intercambian los canales (ffmpeg pone el izquierdo en el nibble bajo, KOS
    # lo espera en el alto).
    subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                    '-i', src, '-af', 'pan=stereo|c0=c1|c1=c0', '-ar', '44100',
                    '-ac', '2', '-c:a', 'adpcm_yamaha', '-f', 'wav', dst], check=True)

# ----------------------------------------------------------------- main ----
def main():
    global GZ
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    GZ = '--raw' not in sys.argv
    if len(args) != 2:
        print(__doc__); sys.exit(1)
    src, out = args
    d1, d2 = os.path.join(src, 'data1'), os.path.join(src, 'data2')
    o1, o2 = os.path.join(out, 'data1'), os.path.join(out, 'data2')
    os.makedirs(o1, exist_ok=True); os.makedirs(o2, exist_ok=True)
    prg = open(os.path.join(src, 'Goody.prg'), encoding='latin-1').read()

    # ---- 1. fases ---------------------------------------------------------
    print('== fases')
    st = stage_maps(prg)
    dur_codes = stage_dur(prg)
    blocks_nivel = stage_blocks(prg)
    group_cache = {n: read_fpg(os.path.join(d1, n)) for n in ('gnivel1.gdg', 'gnivel2.gdg', 'gnivel3.gdg', 'gnivel4.gdg')}
    crops = find_crops(prg, st, dur_codes, group_cache)
    json.dump(crops, open(os.path.join(out, 'crops.json'), 'w'), indent=1)
    for c in crops.values():
        print('   recorte: fase %d mapa %d: %dx%d -> %dx%d' % (c['stage'], c['code'], c['ww'], c['hh'], c['bw'], c['bh']))
    cache = {}
    worst = 0
    for stage in sorted(st):
        name = fpg_for_stage(stage)
        if name not in cache:
            cache[name] = read_fpg(os.path.join(d1, name))
        header, recs = cache[name]
        st_dur = dur_codes[stage]
        # Los fondos 98/99 (cielo con nubes y estrellas, 5 colores, 2,4 % opaco, identicos en los 4 FPG)
        # solo se usan si la fase llama a scroll_start(..., g_fondo, ...): 14 de 32. En las otras 18 no
        # se dibujan nunca y ocupaban 0,41 M px (el 40 % de una fase media).
        usa_fondo = bool(re.search(r'scroll_start\s*\(\s*0\s*,\s*gnivel\s*,\s*\d+\s*,\s*g_fondo\b', blocks_nivel.get(stage, ''), re.I))
        codes = (set(st[stage]) - st_dur) | ({98, 99} if usa_fondo else set())
        recs_f = dict(recs)
        for key, c in crops.items():
            if c['stage'] == stage and c['code'] in recs_f:
                recs_f[c['code']] = crop_record8(recs[c['code']], c)
        size = write_fpg(os.path.join(o1, 'niv_%02d.fpg' % stage), header, recs_f, codes)
        px = sum(map_px(recs_f[c])[0] * map_px(recs_f[c])[1] for c in codes if c in recs_f)
        worst = max(worst, px)
        dw = dh = 0
        for dcode in st_dur:
            dw, dh, dup = dureza_png(header, recs[dcode], os.path.join(o1, 'dur_%02d.png' % stage))
            if dup: print('   (aviso: %d indices con el mismo color que uno especial, ajustados)' % dup)
        print('   stage %2d: mapas %-18s %6d KB fichero, %4.2f MB (32 bits) + dureza %dx%d (%4.2f MB)'
              % (stage, sorted(codes), size // 1024, px * 4 / 1e6, dw, dh, dw * dh * 4 / 1e6))
    # mascara de lingotes (fase del banquero): mapa 11, indice 87, a MEDIA resolucion y recortada
    import numpy as np
    bs = banquero_stage(prg)
    header, recs = cache[fpg_for_stage(bs)]
    a = map_indices(recs[11])
    lut, _ = palette_rgba(header)
    m = (a == 87)
    reg = m[LIN_Y0:LIN_Y0 + 308, LIN_X0:LIN_X0 + 1288]            # cubre los 5 rectangulos de aparicion
    h2, w2 = reg.shape[0] // 2, reg.shape[1] // 2
    half = reg[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).any(axis=(1, 3))
    img = np.zeros((h2, w2, 4), dtype=np.uint8)
    img[half] = lut[87]
    write_png_rgba(os.path.join(o1, 'lin_%02d.png' % bs), w2, h2, img.tobytes())
    print('   lin_%02d.png: mascara de lingotes %dx%d (fase %d)' % (bs, w2, h2, bs))
    print('   peor fase: %.2f MB RAM a 32 bits' % (worst * 4 / 1e6))

    # ---- 2. menu, ayuda, creditos ----------------------------------------
    print('== menu / ayuda / creditos')
    AYUDA = set(range(29, 40))
    CRED_BG = set(range(60, 65))
    CRED_TXT = set(range(50, 59))
    # 2, 3 y 90 (fondos 640x480/398x520) solo los usa el proceso creditos(), que
    # nadie llama, y el banner comentado: se quedan fuera.
    UNUSED = {2, 3, 90}
    INGAME = set(range(20, 29)) | set(range(40, 50))   # pausa, game over, continuar...
    for lang, fname in ((1, 'gmenu.gdg'), (2, 'gmenu2.gdg')):
        header, recs = read_fpg(os.path.join(d1, fname))
        allc = set(recs)
        sfx = '' if lang == 1 else '2'
        full = allc - AYUDA - CRED_BG - UNUSED
        ingame = INGAME & allc
        n = write_fpg(os.path.join(o1, 'gmenu%s.fpg' % sfx), header, recs, full)
        px = sum(map_px(recs[c])[0] * map_px(recs[c])[1] for c in full)
        print('   gmenu%s.fpg   %6d KB fichero  %5.2f MB RAM a 32 bits (menu)' % (sfx, n // 1024, px * 4 / 1e6))
        n = write_fpg(os.path.join(o1, 'gmenui%s.fpg' % sfx), header, recs, ingame)
        px = sum(map_px(recs[c])[0] * map_px(recs[c])[1] for c in ingame)
        print('   gmenui%s.fpg  %6d KB fichero  %5.2f MB RAM a 32 bits (dentro de la partida)' % (sfx, n // 1024, px * 4 / 1e6))
        for p in sorted(AYUDA):
            write_fpg(os.path.join(o1, 'ay%d_%d.fpg' % (lang, p)), header, recs, {p})
        cred = CRED_BG | CRED_TXT
        n = write_fpg(os.path.join(o1, 'gcr%d.fpg' % lang), header, recs, cred)
        px = sum(map_px(recs[c])[0] * map_px(recs[c])[1] for c in cred if c in recs)
        print('   gcr%d.fpg     %6d KB fichero  %5.2f MB RAM a 32 bits' % (lang, n // 1024, px * 4 / 1e6))

    # ---- 3. logos: 3 fotogramas -------------------------------------------
    print('== logos')
    header, recs = read_fpg(os.path.join(d1, 'logos.gdg'))
    # Logos 20 (OPERA) y 42 (COPTRON): casi todo fondo negro (0x0001). Se recortan a su caja:
    # de 640x480 a 480x105 y 365x141. El 22 (creditos) ocupa toda la pantalla y va entero.
    import numpy as np
    EXPECT = {20: (312, 242), 42: (318, 275)}      # centro de la caja en pantalla (sin el -50 del 2o)
    for nombre, codigo in (('logo1', 20), ('logo2', 42), ('logo3', 22)):
        rec = recs[codigo]
        if codigo in EXPECT:
            w, h = map_px(rec)
            npts = struct.unpack('<i', rec[60:64])[0]
            off = 64 + npts * 4
            a = np.frombuffer(rec[off:off + w * h * 2], dtype='<u2').reshape(h, w)
            vals, cnt = np.unique(a, return_counts=True)
            bg = vals[np.argmax(cnt)]
            ys, xs = np.where(a != bg)
            x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
            sub = np.ascontiguousarray(a[y0:y1 + 1, x0:x1 + 1])
            nh, nw = sub.shape
            data = sub.astype('<u2').tobytes()
            hdr = bytearray(rec[:64])
            struct.pack_into('<i', hdr, 4, 64 + len(data))
            struct.pack_into('<i', hdr, 52, nw)
            struct.pack_into('<i', hdr, 56, nh)
            struct.pack_into('<i', hdr, 60, 0)
            rec = bytes(hdr) + data
            cx, cy = int(x0) + nw // 2, int(y0) + nh // 2
            ok = (cx, cy) == EXPECT[codigo]
            print('   %s: caja %dx%d en (%d,%d) -> centro (%d,%d) %s' %
                  (nombre, nw, nh, x0, y0, cx, cy, 'OK' if ok else '*** NO COINCIDE con patch_goody.py ***'))
        with open(os.path.join(o1, nombre + '.fpg'), 'wb') as f:
            body = header + rec
            f.write(gzip.compress(body, 9, mtime=0) if GZ else body)
        print('   %s.fpg %d KB' % (nombre, os.path.getsize(os.path.join(o1, nombre + '.fpg')) // 1024))

    # ---- 4. marcador sin los mapas de 640x480 -----------------------------
    header, recs = read_fpg(os.path.join(d1, 'gscore.gdg'))
    n = write_fpg(os.path.join(o1, 'gscore.fpg'), header, recs, set(recs) - {99, 100})
    print('== gscore.fpg %d KB (sin 99/100)' % (n // 1024))

    # ---- 5. resto de graficos y fuentes sin cambios -----------------------
    # (se escriben sin comprimir: el cargador no necesita zlib y es mas rapido)
    for f in ('ggoody', 'genemigos', 'gscena', 'gscena2'):
        header, recs = read_fpg(os.path.join(d1, f + '.gdg'))
        write_fpg(os.path.join(o1, f + '.fpg'), header, recs, set(recs))
    for f in ('money.glt', 'vidas.glt', 'mensajes.glt'):
        shutil.copyfile(os.path.join(d1, f), os.path.join(o1, f))

    # ---- 6. audio ----------------------------------------------------------
    print('== audio')
    for f in sorted(os.listdir(d2)):
        if f == 'final.gdm':
            print('   %-14s OMITIDO (video Theora, 23 MB)' % f); continue
        s, t = os.path.join(d2, f), os.path.join(o2, f)
        dur = ffprobe_duration(s)
        if dur >= 10:
            to_adpcm(s, t)
            print('   %-14s %5.1f s  %5d KB -> %5d KB (ADPCM)' %
                  (f, dur, os.path.getsize(s) // 1024, os.path.getsize(t) // 1024))
        else:
            shutil.copyfile(s, t)
    print('listo ->', out)

if __name__ == '__main__':
    main()
