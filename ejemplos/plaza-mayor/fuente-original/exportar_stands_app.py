"""Genera public/mapa3d/datos.json para la app (pines de lugares + capa de stands con su posicion 3D).

Uso: python exportar_stands_app.py [ruta_app]
Lee leyenda_v04.json (pines) y plano_v03.json (stands con poligono en metros). La clave `key` es el codigo
normalizado (letras + numero sin ceros + sufijo; B -> BL) para cruzarlo con stands_publico.codigo en la app.
Coordenadas en el sistema de three.js del visor: (x, y_alto, z) = (X_este, Z, -Y_norte).
"""
import json, re, sys, pathlib

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
APP = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r'D:/Github/app_feria_effix')
D = json.loads((R / 'plano_v03.json').read_text(encoding='utf8'))
pins = json.loads((R / 'leyenda_v04.json').read_text(encoding='utf8'))
web = json.loads((R / 'web' / 'datos.json').read_text(encoding='utf8'))

Z_UP, Z_GS, Z_MULTI = 11.0, -9.0, -4.5
E = {k: [tuple(p) for p in v] for k, v in D['edificios'].items()}


def pip(pt, poly):
    x, y = pt; ins = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            ins = not ins
    return ins


def normalize(code):
    c = re.sub(r'[^A-Z0-9]', '', (code or '').upper())
    m = re.match(r'^([A-Z]+)0*(\d+)([A-Z]*)$', c)
    if not m:
        return c
    pre, num, suf = m.groups()
    if pre == 'B':
        pre = 'BL'
    return f'{pre}{int(num)}{suf}'


PAB = {'A': 'azul', 'BL': 'blanco', 'AM': 'amarillo', 'T': 'comidas', 'R': 'rojo', 'PL': 'plazoleta', 'GL': 'gran_salon', 'HV': 'verde'}
stands = []
for s in D['stands']:
    if not s['codigo'] or s.get('sala'):
        continue
    p = s['poly']; cx = sum(q[0] for q in p) / len(p); cy = sum(q[1] for q in p) / len(p)
    reg = s['region']
    up = pip((cx, cy), E['Azul']) or pip((cx, cy), E['Verde']) or pip((cx, cy), E['Zona_VIP_Verde']) or (-8.2 < cx < 5.7 and 72.8 < cy < 97.5)   # bloque Zona IA
    z = {'rojo': 0.0, 'gran_salon': Z_GS + 4.5, 'caja': 4.5, 'multi': Z_MULTI + 4.5}.get(reg, Z_UP if up else 0.0)
    if reg not in ('rojo', 'gran_salon', 'caja', 'multi') and not up:      # Hall, plancha de comidas, zona HV1/HV2 y terrazas del Blanco
        ZH_HALL = 4.5
        if (-1.2 < cx < 34.6 and -22.2 < cy < 1.8) or (-1.2 < cx < 47.2 and -34.4 < cy < -22.2) or (-12.9 < cx < 5.3 and 20.1 < cy < 37.7):
            z = ZH_HALL
        elif pip((cx, cy), E['Blanco']):
            z = ZH_HALL if cy < 31.35 else (ZH_HALL / 2 if cy < 44.85 else 0.0)
    grupo = {'rojo': 'inf', 'gran_salon': 'gs', 'caja': 'caja', 'multi': 'multi'}.get(reg, 'sup' if up else 'base')
    key = normalize(s['codigo'])
    pre = re.match(r'^[A-Z]+', key).group(0) if re.match(r'^[A-Z]+', key) else ''
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    stands.append({'codigo': s['codigo'], 'key': key, 'pabellon': PAB.get(pre, ''), 'grupo': grupo,
                   'pos': [round(cx, 2), round(cy, 2), round(z, 2)], 'alto': 2.6 if max(max(xs) - min(xs), max(ys) - min(ys)) < 9 else 3.2})
# un mismo codigo puede venir en varios poligonos (stands grandes dibujados por piezas): se deja uno, el mas grande
mejor = {}
for st in stands:
    k = st['key']
    if k not in mejor or st['alto'] > mejor[k]['alto']:
        mejor[k] = st
stands = list(mejor.values())
web['stands'] = stands
web['pines'] = pins
out = APP / 'public' / 'mapa3d' / 'datos.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(web, ensure_ascii=False), encoding='utf8')
print('stands', len(stands), '->', out)
