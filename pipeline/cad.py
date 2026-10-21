"""Lectura de planos CAD (DXF) para extraer_plano.py. Los DWG se convierten antes a DXF (ver docs/ENTRADAS.md).

En CAD el plano ya viene en unidades reales (mm, cm o m) y con el eje Y hacia arriba: no hay que calibrar escala,
solo saber la unidad y, si hay varios pisos dibujados lado a lado, separar regiones y llevarlas a su sitio.
"""
import fnmatch, json, math, re, pathlib
import ezdxf
from PIL import Image, ImageDraw

UNIDADES = {0: None, 1: .0254, 2: .3048, 4: .001, 5: .01, 6: 1.0}        # $INSUNITS -> metros


def polilineas(e, segs_arco=16):
    """Entidad DXF -> lista de (puntos [(x, y)], cerrada)."""
    t = e.dxftype()
    if t == 'LINE':
        return [([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]], False)]
    if t == 'LWPOLYLINE':
        return [([tuple(p[:2]) for p in e.get_points('xy')], bool(e.closed))]
    if t == 'POLYLINE':
        return [([tuple(v.dxf.location)[:2] for v in e.vertices], bool(e.is_closed))]
    if t in ('CIRCLE', 'ARC'):
        c = e.dxf.center; r = e.dxf.radius
        a0, a1 = (0, 360) if t == 'CIRCLE' else (e.dxf.start_angle, e.dxf.end_angle)
        if a1 <= a0:
            a1 += 360
        n = max(4, int(segs_arco * (a1 - a0) / 360))
        pts = [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
        return [(pts[:-1], True) if t == 'CIRCLE' else (pts, False)]
    if t == 'HATCH':
        out = []
        for p in e.paths:
            if hasattr(p, 'vertices'):
                out.append(([tuple(v[:2]) for v in p.vertices], True))
        return out
    return []


def textos(msp):
    out = []
    for e in msp.query('TEXT MTEXT'):
        txt = e.plain_text() if e.dxftype() == 'MTEXT' else e.dxf.text
        p = e.dxf.insert
        out.append({'texto': re.sub(r'\s+', ' ', txt).strip(), 'x': p[0], 'y': p[1], 'capa': e.dxf.layer})
    return out


def unidad(doc, forzada=None):
    if forzada:
        return float(forzada)
    u = UNIDADES.get(doc.header.get('$INSUNITS', 0))
    return u


def inspeccionar(ruta, out, fuente):
    out.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.readfile(ruta); msp = doc.modelspace()
    u = unidad(doc)
    capas = {}
    xs, ys = [], []
    for e in msp:
        c = capas.setdefault(e.dxf.layer, {'capa': e.dxf.layer, 'entidades': {}, 'cerradas': 0})
        c['entidades'][e.dxftype()] = c['entidades'].get(e.dxftype(), 0) + 1
        for pts, cerr in polilineas(e):
            c['cerradas'] += cerr
            xs += [p[0] for p in pts]; ys += [p[1] for p in pts]
    tx = textos(msp)
    for t in tx:
        capas.setdefault(t['capa'], {'capa': t['capa'], 'entidades': {}, 'cerradas': 0}).setdefault('ejemplos_texto', [])
        ej = capas[t['capa']]['ejemplos_texto']
        if len(ej) < 8:
            ej.append(t['texto'])
    lista = sorted(capas.values(), key=lambda c: -sum(c['entidades'].values()))
    ext = [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 0, 0]
    (out / 'capas.json').write_text(json.dumps({'unidad_m': u, 'extension': ext, 'capas': lista}, indent=1, ensure_ascii=False), encoding='utf8')
    (out / 'textos.json').write_text(json.dumps(tx, ensure_ascii=False), encoding='utf8')
    # vista del dibujo completo, con regla en unidades del dibujo
    if xs:
        W = 3000; esc = W / max(ext[2] - ext[0], 1e-6); H = int((ext[3] - ext[1]) * esc) + 1
        if H > 6000:
            esc *= 6000 / H; W = int((ext[2] - ext[0]) * esc) + 1; H = 6000
        im = Image.new('RGB', (W + 80, H + 80), 'white'); d = ImageDraw.Draw(im); f = fuente(16)
        T = lambda p: (40 + (p[0] - ext[0]) * esc, 40 + (ext[3] - p[1]) * esc)
        for e in msp:
            for pts, cerr in polilineas(e):
                q = [T(p) for p in pts] + ([T(pts[0])] if cerr else [])
                if len(q) > 1:
                    d.line(q, fill=(40, 40, 40), width=1)
        for t in tx:
            d.text(T((t['x'], t['y'])), t['texto'][:20], fill=(200, 30, 30), font=f)
        paso = 10 ** math.floor(math.log10(max(ext[2] - ext[0], 1) / 5))
        v = math.ceil(ext[0] / paso) * paso
        while v <= ext[2]:
            d.text((T((v, ext[3]))[0], 4), f'{v:g}', fill=(0, 90, 200), font=f); v += paso
        v = math.ceil(ext[1] / paso) * paso
        while v <= ext[3]:
            d.text((2, T((ext[0], v))[1]), f'{v:g}', fill=(0, 90, 200), font=f); v += paso
        im.save(out / 'dibujo.png')
    print(f'DXF {pathlib.Path(ruta).name}: unidad {"desconocida ($INSUNITS = 0): pregunta si es mm, cm o m" if u is None else f"{u} m"} - '
          f'extension {ext[2] - ext[0]:.0f} x {ext[3] - ext[1]:.0f} unidades - {len(lista)} capas - {len(tx)} textos')
    for c in lista[:20]:
        ents = ', '.join(f'{k} {v}' for k, v in sorted(c['entidades'].items(), key=lambda kv: -kv[1]))
        print(f"  {c['capa']:<28} {ents}{' - ' + str(c['cerradas']) + ' cerradas' if c['cerradas'] else ''}"
              f"{' - textos: ' + ', '.join(c['ejemplos_texto'][:4]) if c.get('ejemplos_texto') else ''}")
    print(f'Archivos en {out}: capas.json, textos.json, dibujo.png (regla azul en unidades del dibujo)')


def pip(pt, poly):
    x, y = pt; ins = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            ins = not ins
    return ins


def extraer(C, base, out, vista_previa):
    doc = ezdxf.readfile(base / C['dxf']); msp = doc.modelspace()
    u = unidad(doc, C.get('unidad_m'))
    if not u:
        raise SystemExit('El DXF no dice su unidad ($INSUNITS = 0). Pon "unidad_m" en plano.json (0.001 si es mm, 0.01 cm, 1 m).')
    regiones = []
    for r in C.get('regiones', [{'id': 'todo', 'nivel': 'base'}]):
        a = math.radians(r.get('rotacion', 0))
        regiones.append(dict(r, c=math.cos(a), s=math.sin(a), o=r.get('origen_dibujo', [0, 0]), om=r.get('origen_m', [0, 0])))

    def region(p):
        return next((r for r in regiones if 'bbox' not in r or (r['bbox'][0] <= p[0] <= r['bbox'][2] and r['bbox'][1] <= p[1] <= r['bbox'][3])), None)

    def a_m(r, p):
        dx = (p[0] - r['o'][0]) * u; dy = (p[1] - r['o'][1]) * u
        return [round(r['om'][0] + dx * r['c'] - dy * r['s'], 3), round(r['om'][1] + dx * r['s'] + dy * r['c'], 3)]

    tx = textos(msp)
    res = {'espacios': [], 'muros': [], 'edificios': [], 'zonas': [], 'objetos': [], 'sin_region': 0}
    pendientes = []                                  # (regla, nivel, poligono en dibujo, poligono en m)
    reg_de = {}                                      # poligono -> region (para ajustes por region, p. ej. "edificio": {"cubierta": true})
    for e in msp:
        capa = e.dxf.layer
        regla = next((g for g in C['reglas'] if fnmatch.fnmatch(capa.upper(), g['capa'].upper())), None)
        if not regla or regla['tipo'] == 'texto':
            continue
        for pts, cerr in polilineas(e):
            if len(pts) < 2:
                continue
            c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            r = region(c)
            if not r:
                res['sin_region'] += 1; continue
            nivel = regla.get('nivel', r.get('nivel', 'base')); pm = [a_m(r, p) for p in pts]
            t = regla['tipo']
            if t == 'muro':
                res['muros'].append({'nivel': nivel, 'puntos': pm, 'cerrado': cerr, 'alto': regla.get('alto', 2.6),
                                     'grosor': regla.get('grosor', .15), **({'material': regla['material']} if regla.get('material') else {})})
            elif cerr and len(pts) >= 3 and t in ('espacio', 'edificio', 'zona', 'caja'):
                pendientes.append((regla, nivel, pts, pm)); reg_de[id(pts)] = r
    for regla, nivel, pts, pm in pendientes:
        dentro = [t for t in tx if pip((t['x'], t['y']), pts) and
                  (not regla.get('capa_textos') or fnmatch.fnmatch(t['capa'].upper(), regla['capa_textos'].upper()))]
        t = regla['tipo']
        if t == 'espacio':
            patron = regla.get('codigo', r'^[A-Z]{0,3}[- ]?[0-9]')
            cod = next((d['texto'] for d in dentro if re.match(patron, d['texto'])), '')
            nombre = ' '.join(d['texto'] for d in dentro if d['texto'] != cod)
            esp = {'codigo': cod, 'nivel': nivel, 'poligono': pm, 'altura': regla.get('altura', .05)}
            if nombre:
                esp['nombre'] = nombre
                if regla.get('rotulo') == 'nombre':          # en el piso se lee el nombre de la sala en vez del codigo
                    esp['rotulo'] = nombre
            for k in ('color', 'categoria'):
                if regla.get(k):
                    esp[k] = regla[k]
            res['espacios'].append(esp)
        elif t == 'edificio':
            res['edificios'].append({'id': f'{regla.get("id", "edif")}_{len(res["edificios"])}', 'nombre': ' '.join(d['texto'] for d in dentro),
                                     'nivel': nivel, 'poligono': pm, 'altura': regla.get('altura', 3.5),
                                     'color': regla.get('color', [.6, .6, .62]), 'cubierta': regla.get('cubierta', True),
                                     **{k: regla[k] for k in ('piso', 'fachada', 'losa', 'muro_bajo', 'ventanas', 'muros_altos', 'rotulo_piso', 'tam_rotulo') if k in regla},
                                     **reg_de[id(pts)].get('edificio', {})})
        elif t == 'zona':
            res['zonas'].append({'id': f'{regla.get("id", "zona")}_{len(res["zonas"])}', 'nivel': nivel, 'poligono': pm,
                                 'material': regla.get('material') or regla.get('color', 'pav_plaza')})
        elif t == 'caja':
            xs = [p[0] for p in pm]; ys = [p[1] for p in pm]
            res['objetos'].append({'tipo': 'caja', 'nivel': nivel, 'centro': [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2],
                                   'tam': [max(xs) - min(xs), max(ys) - min(ys), regla.get('alto', .9)],
                                   'material': regla.get('material', 'blanco')})
    (out / 'plano_m.json').write_text(json.dumps(res, ensure_ascii=False), encoding='utf8')
    vista_previa(res, out / 'plano_m.png')
    sin = sum(1 for s in res['espacios'] if not s['codigo'])
    print(f"DXF a metros (1 unidad = {u} m): {len(res['edificios'])} edificios - {len(res['muros'])} muros - "
          f"{len(res['espacios'])} espacios ({sin} sin codigo) - {len(res['zonas'])} zonas - {len(res['objetos'])} objetos - "
          f"{res['sin_region']} fuera de toda region")
    print(f'Archivos: {out / "plano_m.json"} y {out / "plano_m.png"}')
