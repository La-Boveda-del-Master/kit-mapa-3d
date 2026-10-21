"""Extrae el plano tecnico de Feria Effix 2026 a metros y lo ubica por NIVELES (v03).

Escala: cuadricula de fondo del PDF tecnico = 1 m (medida por FFT en cada imagen raster).
  Zonas principales: 9.25 pt/m (x pagina) y 9.76 pt/m (y pagina).
  Recuadro Gran Salon: 8.57 / 8.985.   Recuadro Caja de Madera (Registro): 8.76 / 9.135.
  Salon Multiproposito: 13.3 / 13.6 (sin cuadricula: deducida de la modulacion de columnas del Gran Salon,
  7.2 m, y comprobada con la tarima 5x3 y el ancho de las escaleras electricas).
Mundo: +X Este (Av. Ferrocarril), +Y Norte (Gran Salon / Caja), 1 u = 1 m.

En el PDF varios recintos estan dibujados "al lado"; aqui se reubican donde van:
  - Pabellon Rojo  -> debajo del Azul (mismo ancho de 41.8 m).
  - Auditorio Comunidades -> debajo del Verde (se desplaza perpendicular al borde norte del Verde).
  - Caja de Madera (Registro, piso 3) y Salon Multiproposito (piso 2) -> encima del Gran Salon (piso 1),
    alineados por el vacio central y las escaleras electricas, que aparecen en los tres planos
    (coinciden con < 1 m de diferencia).
"""
import json, math, pathlib, re, statistics
import pymupdf

ROOT = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
PDF = r'D:/Usuario/Downloads/Copia de feria effix 2026 tecnico.pdf'

SX, SY = 9.25, 9.76
OX, OY = 1300.0, 1150.0
GS_BOX = (2819, 864, 3817, 1521); GS_S = (8.57, 8.985)
CAJA_BOX = (3103, 1667, 3997, 2209); CAJA_S = (8.76, 9.135)
CAJA_OUTER = (3148.5, 1779.8, 3549.6, 2160.9)          # borde de celosia del recuadro
CAJA_PC = (3349.05, 1970.35); CAJA_WC = (10.8, 195.8)  # centro en pagina <-> centro en el mundo
CAJA_VOID = (3192.1, 1818.5, 3287.6, 2103.8)           # vacio de escaleras electricas
MULTI_BOX = (4080, 640, 4600, 1540); MULTI_S = (13.3, 13.6)
MULTI_REF_P = (4243.6, 884.1); MULTI_REF_W = (-8.5, 174.9)   # columna comun con el Gran Salon
ROJO_RECT = (317, 433, 704, 944); AZUL_RECT = (1095, 549, 1481, 1131)
ROJO_D = (AZUL_RECT[0] - ROJO_RECT[0], AZUL_RECT[1] - ROJO_RECT[1])
ROJO_IMG = (300, 380, 925, 1050)
COM_BOX = (2100, 480, 2480, 830); COM_SHIFT = (-241.6, 87.6)  # 257 pt hacia adentro del Verde
VERDE_N = (0.940, -0.341, 1694.0)                             # normal y termino del borde norte del Verde


def main_m(x, y):
    return ((y - OY) / SY, (x - OX) / SX)


GS_O = main_m(GS_BOX[0], GS_BOX[1])


def gs_m(x, y):
    return (GS_O[0] + (y - GS_BOX[1]) / GS_S[1], GS_O[1] + (x - GS_BOX[0]) / GS_S[0])


def caja_m(x, y):
    return (CAJA_WC[0] + (y - CAJA_PC[1]) / CAJA_S[1], CAJA_WC[1] + (x - CAJA_PC[0]) / CAJA_S[0])


def multi_m(x, y):
    return (MULTI_REF_W[0] + (y - MULTI_REF_P[1]) / MULTI_S[1], MULTI_REF_W[1] + (x - MULTI_REF_P[0]) / MULTI_S[0])


def rojo_m(x, y):
    return main_m(x + ROJO_D[0], y + ROJO_D[1])


def com_m(x, y):
    return main_m(x + COM_SHIFT[0], y + COM_SHIFT[1])


def inside(b, x, y, m=0):
    return b[0] - m <= x <= b[2] + m and b[1] - m <= y <= b[3] + m


def region(x, y):
    if inside(MULTI_BOX, x, y):
        return 'multi', multi_m
    if x > 4000 or y > 2150 or (x > 2590 and y < 520):
        return None, None
    if inside(GS_BOX, x, y):
        return 'gran_salon', gs_m
    if inside(CAJA_BOX, x, y):
        return 'caja', caja_m
    if inside(ROJO_IMG, x, y):
        return ('rojo', rojo_m) if inside(ROJO_RECT, x, y, 2) else (None, None)
    if inside(COM_BOX, x, y) and VERDE_N[0] * x + VERDE_N[1] * y > VERDE_N[2] + 10:
        return 'comunidades', com_m
    return 'main', main_m


def path_points(g):
    pts = []
    for it in g['items']:
        if it[0] == 'l':
            pts += [it[1], it[2]]
        elif it[0] == 're':
            r = it[1]; pts += [r.tl, r.tr, r.br, r.bl]
        elif it[0] == 'qu':
            q = it[1]; pts += [q.ul, q.ur, q.lr, q.ll]
        elif it[0] == 'c':
            pts += [it[1], it[4]]
    out = []
    for q in pts:
        t = (q.x, q.y)
        if not out or abs(out[-1][0] - t[0]) + abs(out[-1][1] - t[1]) > 1e-3:
            out.append(t)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) < 1e-3:
        out.pop()
    return out


def key(c):
    return tuple(round(v, 2) for v in c)


def R3(p):
    return [round(p[0], 3), round(p[1], 3)]


def pip(pt, poly):
    x, y = pt; ins = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            ins = not ins
    return ins


doc = pymupdf.open(PDF)
page = doc[0]
words = page.get_text('words')
drawings = page.get_drawings()

out = {'escala': {'pt_por_m': [SX, SY], 'gran_salon': GS_S, 'caja': CAJA_S, 'multi': MULTI_S,
                  'nota': 'Cuadricula PDF tecnico = 1 m. +X Este, +Y Norte.'},
       'stands': [], 'sillas': [], 'vip': [], 'carros': [], 'mesas': [], 'tarimas': [],
       'caja_items': [], 'caja_filas': []}

CHAIR = {(0.69, 0.68, 0.68), (0.44, 0.43, 0.43), (0.17, 0.28, 0.6)}
STAND = (0.95, 0.62, 0.64)
BLACK = (0.11, 0.11, 0.11)


def words_in(r, m=1):
    w = [v for v in words if r.x0 - m <= (v[0] + v[2]) / 2 <= r.x1 + m and r.y0 - m <= (v[1] + v[3]) / 2 <= r.y1 + m]
    w.sort(key=lambda v: (round(v[3]), v[0]))
    return w


for g in drawings:
    r = g['rect']
    cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
    reg, T = region(cx, cy)
    if not reg:
        continue
    f = g.get('fill')
    # filas con catenarias (lineas punteadas) dentro de la Caja de Madera
    if not f and reg == 'caja' and g.get('dashes') not in (None, '', '[] 0') and inside(CAJA_OUTER, cx, cy, 4):
        for it in g['items']:
            if it[0] == 'l':
                a, b = T(it[1].x, it[1].y), T(it[2].x, it[2].y)
                if math.dist(a, b) > .8:
                    out['caja_filas'].append([R3(a), R3(b)])
        continue
    if not f:
        continue
    k = key(f)
    pts = path_points(g)
    if len(pts) < 3:
        continue
    mpts = [T(x, y) for x, y in pts]
    if k == STAND and r.width * r.height > 40:
        inner = words_in(r)
        code = next((w[4] for w in inner if re.match(r'^[A-Z]{1,3}[- ]?\d', w[4]) and not re.match(r'^\d+[xX]\d+$', w[4])), '')
        size = next((w[4].upper() for w in inner if re.match(r'^\d+[xX]\d+$', w[4])), '')
        out['stands'].append({'region': reg, 'poly': [R3(p) for p in mpts], 'codigo': code, 'medida_rotulo': size,
                              'texto': ' '.join(w[4] for w in inner), 'bbox_pt': [r.width, r.height]})
    elif k in CHAIR and r.width < 15 and r.height < 15:
        c = (sum(a for a, _ in mpts) / len(mpts), sum(b for _, b in mpts) / len(mpts))
        e = (mpts[1][0] - mpts[0][0], mpts[1][1] - mpts[0][1])
        out['sillas'].append([round(c[0], 3), round(c[1], 3), round(math.atan2(e[1], e[0]), 4), reg])
    elif k == BLACK and reg == 'multi' and len(g['items']) == 4 and 9 < r.width < 15 and r.height < 6:
        c = T(cx, cy)
        out['mesas'].append([round(c[0], 3), round(c[1], 3), 0, reg])
    elif k == BLACK and reg in ('main', 'gran_salon') and sorted((r.width, r.height))[0] < 6 and 9 < sorted((r.width, r.height))[1] < 15:
        c = T(cx, cy)
        out['mesas'].append([round(c[0], 3), round(c[1], 3), 1 if r.width > r.height else 0, reg])
    elif k == BLACK and reg == 'caja' and len(g['items']) <= 4 and r.width * r.height > 60:
        txt = ' '.join(w[4] for w in words_in(r, 2)).lower()
        w_m, h_m = r.width / CAJA_S[0], r.height / CAJA_S[1]
        if 'portico' in txt or (r.width > 40 and r.height > 80):
            tipo = 'portico'
        elif 'backing' in txt:
            tipo = 'backing'
        elif 'taquilla' in txt:
            tipo = 'taquilla'
        elif 'vip' in txt:
            tipo = 'vip_black'
        elif 'control' in txt:
            tipo = 'control'
        elif 'tarima' in txt:
            tipo = 'tarima'
        elif 1.5 < w_m < 2.6 and h_m < 1.0:
            tipo = 'counter'
        else:
            tipo = 'bodega'
        out['caja_items'].append({'tipo': tipo, 'poly': [R3(p) for p in mpts]})
    elif k == (0.53, 0.53, 0.53) and r.width * r.height > 2000:
        out['vip'].append({'region': reg, 'poly': [R3(p) for p in mpts]})

# Pabellon Rojo: los stands son recuadros sobre fondo rojo; se ubican por su rotulo R-xx
rojo_fills = [g for g in drawings if g.get('fill') and inside(ROJO_RECT, g['rect'].x0, g['rect'].y0, 2)
              and inside(ROJO_RECT, g['rect'].x1, g['rect'].y1, 2) and 60 < g['rect'].width * g['rect'].height < 40000
              and key(g['fill']) not in {(0.89, 0.02, 0.08), (0.69, 0.68, 0.68)}]
for w in words:
    if not re.match(r'^R-\d+', w[4]):
        continue
    x = (w[0] + w[2]) / 2; y = (w[1] + w[3]) / 2
    if not inside(ROJO_RECT, x, y):
        continue
    cand = [g for g in rojo_fills if g['rect'].contains(pymupdf.Point(x, y))]
    if not cand or any(s['region'] == 'rojo' and s['codigo'] == w[4] for s in out['stands']):
        continue
    g = min(cand, key=lambda g: g['rect'].width * g['rect'].height); r = g['rect']
    inner = words_in(r)
    size = next((v[4].upper() for v in inner if re.match(r'^\d+[xX]\d+$', v[4])), '')
    out['stands'].append({'region': 'rojo', 'poly': [R3(rojo_m(px, py)) for px, py in path_points(g)], 'codigo': w[4],
                          'medida_rotulo': size, 'texto': ' '.join(v[4] for v in inner), 'bbox_pt': [r.width, r.height]})

# Salas abiertas: zona rosada con sillas adentro -> tapete bajo, no stand
chairs = [(s[0], s[1], s[3]) for s in out['sillas']]
for s in out['stands']:
    n = sum(1 for cxy in chairs if cxy[2] == s['region'] and pip(cxy[:2], s['poly']))
    s['sala'] = n >= 6

# Tarimas (rectangulo relleno mas pequeno que contiene el rotulo "tarima")
SKIPF = {STAND, (0.42, 0.71, 0.18), (0.91, 0.88, 0.07), (0.32, 0.76, 0.91), (0.76, 0.31, 0.59), (0.7, 0.61, 0.49),
         (0.48, 0.41, 0.33), (0.89, 0.02, 0.08)}
fills = [(g['rect'], g) for g in drawings if g.get('fill') and g['rect'].width * g['rect'].height > 150 and key(g['fill']) not in SKIPF]
seen = set()
for b in page.get_text('dict')['blocks']:
    for l in b.get('lines', []):
        t = ' '.join(s['text'] for s in l['spans'])
        if 'tarima' not in t.lower():
            continue
        x = (l['bbox'][0] + l['bbox'][2]) / 2; y = (l['bbox'][1] + l['bbox'][3]) / 2
        reg, T = region(x, y)
        if not reg:
            continue
        cand = [(r, g) for r, g in fills if r.contains(pymupdf.Point(x, y)) and r.width * r.height < 30000]
        if not cand:
            continue
        r, g = min(cand, key=lambda c: c[0].width * c[0].height)
        k2 = (round(r.x0), round(r.y0))
        if k2 in seen:
            continue
        seen.add(k2)
        out['tarimas'].append({'region': reg, 'poly': [R3(T(px, py)) for px, py in path_points(g)], 'texto': t.strip()})
out['caja_items'] = [c for c in out['caja_items'] if c['tipo'] != 'tarima']
# stands duplicados en el PDF (misma huella dibujada dos veces)
uniq = {}
for st in out['stands']:
    c = (round(sum(q[0] for q in st['poly']) / len(st['poly']), 1), round(sum(q[1] for q in st['poly']) / len(st['poly']), 1), st['region'])
    uniq.setdefault(c, st)
out['stands'] = list(uniq.values())

# Carros en exhibicion
for im in page.get_image_info():
    b = im['bbox']
    if 20 < b[2] - b[0] < 35 and 10 < b[3] - b[1] < 18:
        reg, T = region((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        if reg:
            out['carros'].append(R3(T((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)))


def rect_m(b, T=main_m):
    x0, y0, x1, y1 = b
    return [R3(T(x, y)) for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]


VERDE = [(2190.4, 1069.7), (2051.8, 1070.4), (2051.3, 1154.1), (1973.2, 1153.9), (1973.5, 1021.5), (1936.9, 1020.5),
         (1911.2, 966.7), (1878.4, 903.2), (1885.5, 900.8), (1852.7, 821.7), (1676.5, 771.6), (1641.9, 667.8),
         (1482.3, 663.0), (1483.6, 552.4), (1597.3, 552.7), (1512.0, 315.8), (1865.9, 175.6)]
VIP_VERDE = [(1489.3, 976.0), (1721.8, 886.2), (1749.7, 954.6), (1799.3, 933.5), (1771.8, 865.0), (1752.3, 816.0),
             (1757.5, 814.0), (1776.2, 859.1), (1855.6, 827.0), (1810.3, 716.0), (1680.0, 772.6), (1488.9, 893.9)]
# contorno del Auditorio Comunidades leido del dibujo (px del recorte a 80 dpi -> pagina)
COM_PX = [(15, 160), (100, 137), (185, 95), (205, 150), (300, 388), (175, 392), (175, 420), (100, 420), (133, 342), (40, 235)]
COM = [(2100 + x / 1.1111, 440 + y / 1.1111) for x, y in COM_PX]
mx0, my0 = multi_m(4093, 790); mx1, my1 = multi_m(4469, 1497)
out['edificios'] = {
    'Azul': rect_m(AZUL_RECT),
    'Rojo': rect_m(ROJO_RECT, rojo_m),
    'Verde': [R3(main_m(x, y)) for x, y in VERDE],
    'Zona_VIP_Verde': [R3(main_m(x, y)) for x, y in VIP_VERDE],
    'Hall': rect_m((1095, 1138, 1317, 1602)),
    'Blanco': rect_m((1314, 1208, 2202, 1526)),
    'Amarillo_A': rect_m((336, 1609, 783, 2014)),
    'Amarillo_B': rect_m((796, 1613, 1428, 2006)),
    'Sala_Grupo_Effi': rect_m((1099, 1139, 1318, 1263)),
    'Sala_Unmerco': rect_m((1099, 1314, 1302, 1424)),
    'Auditorio_Comunidades': [R3(com_m(x, y)) for x, y in COM],
    'Gran_Salon_sala': rect_m((3144, 1060, 3673, 1386), gs_m),
    'Gran_Salon_edificio': [R3(gs_m(x, y)) for x, y in ((2840, 913), (3740, 957), (3740, 1512), (2840, 1512))],
    'Caja_Madera': rect_m(CAJA_OUTER, caja_m),
    'Caja_vacio': rect_m(CAJA_VOID, caja_m),
    'Multi_bloque': [[round(mx0, 2), round(my0, 2)], [round(mx1, 2), round(my0, 2)], [round(mx1, 2), round(my1, 2)], [round(mx0, 2), round(my1, 2)]],
    'Multi_oficina': [R3(multi_m(4080 + x / 1.528, 640 + y / 1.528)) for x, y in ((20, 25), (770, 100), (770, 310), (20, 310))],
    'Multi_vacio': rect_m((4283, 921, 4433, 1343), multi_m),
    'Escalera_L3_L2': [[12.0, 184.9], [24.6, 184.9], [24.6, 188.3], [12.0, 188.3]],
    'Escalera_L2_L1': [[-0.9, 184.9], [9.7, 184.9], [9.7, 188.3], [-0.9, 188.3]],
    'Gradas_plazoleta': [[-29.6, 153.6], [35.9, 153.6], [35.9, 164.3], [-29.6, 164.3]],
}

(ROOT / 'plano_v03.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf8')

# ---------------------------------------------------------------- validacion
print('stands', len(out['stands']), '(salas abiertas', sum(s['sala'] for s in out['stands']), ') sillas', len(out['sillas']),
      'mesas', len(out['mesas']), 'tarimas', len(out['tarimas']), 'caja_items', len(out['caja_items']), 'filas', len(out['caja_filas']))
for n, e in out['edificios'].items():
    xs = [p[0] for p in e]; ys = [p[1] for p in e]
    print(f'  {n:24s} X {min(xs):7.1f}..{max(xs):7.1f} ({max(xs)-min(xs):5.1f} m)  Y {min(ys):7.1f}..{max(ys):7.1f} ({max(ys)-min(ys):5.1f} m)')
print('Validacion rotulo NxM vs dibujo (lado mayor y lado menor, en m):')
rows = []
for s in out['stands']:
    m = re.match(r'^(\d+)X(\d+)$', s['medida_rotulo'] or '')
    if not m:
        continue
    p = s['poly']
    e1 = math.dist(p[0], p[1]); e2 = math.dist(p[1], p[2]) if len(p) > 2 else 0
    a, b = sorted((int(m[1]), int(m[2])), reverse=True); d1, d2 = sorted((e1, e2), reverse=True)
    rows.append((s['region'], s['codigo'], a, b, d1, d2))
val = []
for reg in sorted({r[0] for r in rows}):
    rr = [r for r in rows if r[0] == reg]
    ok = [r for r in rr if abs(r[4] - r[2]) <= 0.12 * r[2] + .3 and abs(r[5] - r[3]) <= 0.12 * r[3] + .3]
    ra = statistics.median(r[4] / r[2] for r in rr); rb = statistics.median(r[5] / r[3] for r in rr)
    print(f'  {reg:12s} {len(rr):3d} stands con medida | coinciden (+-12%) {len(ok):3d} | razon mediana largo {ra:.2f} ancho {rb:.2f}')
    val.append({'region': reg, 'n': len(rr), 'ok': len(ok), 'razon_largo': round(ra, 3), 'razon_ancho': round(rb, 3),
                'difieren': [[r[1], f'{r[2]}x{r[3]}', round(r[4], 1), round(r[5], 1)] for r in rr if r not in ok]})
(ROOT / 'validacion_medidas_v03.json').write_text(json.dumps(val, ensure_ascii=False, indent=1), encoding='utf8')
