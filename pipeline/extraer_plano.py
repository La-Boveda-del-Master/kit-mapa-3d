"""Del plano (PDF vectorial o DXF de CAD) a metros: inspecciona, calibra la escala y extrae espacios, muros, sillas y zonas.

Uso:
  python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.pdf [--pagina 0] [--cuadricula 1]
  python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.dxf          (CAD: capas, unidades, textos)
      Escribe proyectos/<id>/salida/inspeccion/: pagina.png (con regla en puntos PDF), colores.json
      (rellenos usados, cuantos y de que tamano), textos.json (palabras con su posicion) y escala.json
      (escala medida por FFT sobre la cuadricula de fondo, si el PDF trae una imagen de cuadricula).
  python pipeline/extraer_plano.py extraer proyectos/<id>/plano.json
      Aplica las regiones y reglas de plano.json y escribe salida/plano_m.json (espacios, muros, edificios, objetos, zonas)
      y salida/plano_m.png (vista previa en metros para revisarla contra el PDF). Imprime la validacion de medidas.

Formato de plano.json: docs/FORMATO-MAPA.md (seccion "plano.json"). Para planos en imagen: pipeline/calibrar_imagen.py.
Mundo: +X Este, +Y Norte, metros. El PDF tiene y hacia abajo; aqui se invierte para que el norte quede arriba.
"""
import json, math, re, sys, pathlib
import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont


def ayuda():
    print(__doc__); sys.exit(1)


def salida_de(ruta):
    """proyectos/x/entrada/plano.pdf -> proyectos/x/salida ; proyectos/x/plano.json -> proyectos/x/salida"""
    p = pathlib.Path(ruta).resolve()
    base = p.parent.parent if p.parent.name == 'entrada' else p.parent
    out = base / 'salida'; out.mkdir(exist_ok=True)
    return out


def fuente(t):
    for f in ('C:/Windows/Fonts/segoeui.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if pathlib.Path(f).exists():
            return ImageFont.truetype(f, t)
    return ImageFont.load_default()


def path_points(g):
    """Vertices de un dibujo de PyMuPDF (lineas, rectangulos, cuadrilateros, curvas por sus extremos)."""
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


def periodo_fft(gris):
    """Periodo (en pixeles) de una cuadricula regular, por eje, con el pico del espectro del perfil medio."""
    res = []
    for eje in (0, 1):
        perfil = gris.mean(axis=eje) - gris.mean()
        n = len(perfil)
        if n < 32:
            res.append(None); continue
        esp = np.abs(np.fft.rfft(perfil)); f = np.fft.rfftfreq(n)
        ok = (f > 1 / 80) & (f < 1 / 3)
        if not ok.any():
            res.append(None); continue
        k = np.argmax(esp * ok)
        res.append(1 / f[k] if esp[k] > 4 * np.median(esp[ok]) else None)
    return res          # (periodo_x, periodo_y)


# ---------------------------------------------------------------- inspeccionar
def inspeccionar(pdf, pagina=0, cuadricula=1.0):
    out = salida_de(pdf) / 'inspeccion'; out.mkdir(exist_ok=True)
    doc = pymupdf.open(pdf); page = doc[pagina]
    W, H = page.rect.width, page.rect.height
    escala = min(4.0, 6000 / max(W, H))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(escala, escala), alpha=False)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    d = ImageDraw.Draw(im); f = fuente(max(12, int(10 * escala)))
    paso = 100 if max(W, H) < 3000 else 250
    for x in range(0, int(W) + 1, paso):                    # regla en puntos PDF para leer coordenadas en la imagen
        d.line([(x * escala, 0), (x * escala, 14 * escala)], fill=(220, 0, 0), width=2); d.text((x * escala + 3, 2), str(x), fill=(220, 0, 0), font=f)
    for y in range(0, int(H) + 1, paso):
        d.line([(0, y * escala), (14 * escala, y * escala)], fill=(220, 0, 0), width=2); d.text((3, y * escala + 3), str(y), fill=(220, 0, 0), font=f)
    im.save(out / 'pagina.png')

    colores = {}
    for g in page.get_drawings():
        c = g.get('fill')
        if not c:
            continue
        k = ','.join('%.2f' % v for v in c)
        r = g['rect']
        e = colores.setdefault(k, {'relleno': [round(v, 2) for v in c], 'cantidad': 0, 'ancho_pt': [], 'alto_pt': [], 'ejemplo_bbox_pt': [round(v, 1) for v in r]})
        e['cantidad'] += 1; e['ancho_pt'].append(r.width); e['alto_pt'].append(r.height)
    lista = []
    for e in colores.values():
        e['ancho_pt_mediana'] = round(float(np.median(e.pop('ancho_pt'))), 1); e['alto_pt_mediana'] = round(float(np.median(e.pop('alto_pt'))), 1)
        lista.append(e)
    lista.sort(key=lambda e: -e['cantidad'])
    (out / 'colores.json').write_text(json.dumps(lista, indent=1, ensure_ascii=False), encoding='utf8')

    palabras = [{'texto': w[4], 'x': round((w[0] + w[2]) / 2, 1), 'y': round((w[1] + w[3]) / 2, 1)} for w in page.get_text('words')]
    (out / 'textos.json').write_text(json.dumps(palabras, ensure_ascii=False), encoding='utf8')

    # escala por FFT sobre las imagenes raster (la cuadricula de fondo de muchos planos tecnicos es una imagen)
    medidas = []
    for info in page.get_image_info(xrefs=True):
        if not info.get('xref'):
            continue
        try:
            px = pymupdf.Pixmap(doc, info['xref'])
            if px.n - px.alpha > 1:
                px = pymupdf.Pixmap(pymupdf.csGRAY, px)
            a = np.frombuffer(px.samples, np.uint8).reshape(px.height, px.width, px.n)[..., 0].astype(float)
        except Exception as e:              # imagenes con mascara o formatos raros
            medidas.append({'xref': info['xref'], 'error': str(e)}); continue
        bb = info['bbox']; per = periodo_fft(a)
        m = {'xref': info['xref'], 'bbox_pt': [round(v, 1) for v in bb], 'pixeles': [px.width, px.height]}
        if per[0] and per[1]:
            ptx = per[0] * (bb[2] - bb[0]) / px.width; pty = per[1] * (bb[3] - bb[1]) / px.height
            m['pt_por_m'] = [round(ptx / cuadricula, 3), round(pty / cuadricula, 3)]
        medidas.append(m)
    (out / 'escala.json').write_text(json.dumps({'cuadricula_m': cuadricula, 'imagenes': medidas}, indent=1), encoding='utf8')

    print(f'Pagina {pagina}: {W:.0f} x {H:.0f} pt - {len(lista)} colores de relleno - {len(palabras)} palabras - {len(medidas)} imagenes')
    print('Rellenos mas usados (posibles espacios, sillas, zonas):')
    for e in lista[:12]:
        print(f"  {e['relleno']}  x{e['cantidad']}  ~{e['ancho_pt_mediana']} x {e['alto_pt_mediana']} pt")
    for m in medidas:
        if 'pt_por_m' in m:
            print(f"  Cuadricula en imagen {m['xref']} ({m['bbox_pt']}): {m['pt_por_m'][0]} pt/m en X, {m['pt_por_m'][1]} pt/m en Y")
    rotulos = [p for p in palabras if re.match(r'^\d+([.,]\d+)?\s*[xX]\s*\d+([.,]\d+)?$', p['texto'])]
    if rotulos:
        print(f'  {len(rotulos)} rotulos de medida tipo "6x3": sirven para validar la escala.')
    print(f'Archivos en {out}')


# ---------------------------------------------------------------- extraer
class Region:
    def __init__(s, r, W, H):
        s.id = r['id']; s.bbox = r.get('bbox_pt', [0, 0, W, H])
        s.sx, s.sy = (r['escala_pt_m'] if isinstance(r['escala_pt_m'], list) else [r['escala_pt_m']] * 2)
        s.o = r.get('origen_pt', s.bbox[:2]); s.om = r.get('origen_m', [0, 0])
        a = math.radians(r.get('rotacion', 0)); s.c, s.s = math.cos(a), math.sin(a)
        s.nivel = r.get('nivel', 'base'); s.mover = r.get('mover_m', [0, 0])

    def dentro(s, x, y, m=0):
        b = s.bbox
        return b[0] - m <= x <= b[2] + m and b[1] - m <= y <= b[3] + m

    def a_m(s, x, y):
        dx = (x - s.o[0]) / s.sx; dy = -(y - s.o[1]) / s.sy
        return (round(s.om[0] + s.mover[0] + dx * s.c - dy * s.s, 3), round(s.om[1] + s.mover[1] + dx * s.s + dy * s.c, 3))


def color_igual(a, b, tol):
    return a is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def extraer(cfg_path):
    cfg_path = pathlib.Path(cfg_path).resolve(); C = json.loads(cfg_path.read_text(encoding='utf8'))
    out = salida_de(cfg_path)
    if C.get('dxf'):
        import cad
        return cad.extraer(C, cfg_path.parent, out, vista_previa)
    doc = pymupdf.open(cfg_path.parent / C['pdf']); page = doc[C.get('pagina', 0)]
    W, H = page.rect.width, page.rect.height
    regiones = [Region(r, W, H) for r in C['regiones']]       # la primera que contenga el punto gana: pon las pequenas primero
    words = page.get_text('words')
    res = {'espacios': [], 'objetos': [], 'zonas': [], 'sin_region': 0}
    sillas = {}

    def region(x, y):
        return next((r for r in regiones if r.dentro(x, y)), None)

    def palabras_en(r, m=1):
        w = [v for v in words if r.x0 - m <= (v[0] + v[2]) / 2 <= r.x1 + m and r.y0 - m <= (v[1] + v[3]) / 2 <= r.y1 + m]
        w.sort(key=lambda v: (round(v[3]), v[0]))
        return w

    for g in page.get_drawings():
        f = g.get('fill'); r = g['rect']
        if not f:
            continue
        for regla in C['reglas']:
            if not color_igual(f, regla['relleno'], regla.get('tolerancia', .02)):
                continue
            reg = region((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
            if not reg:
                res['sin_region'] += 1; break
            pts = path_points(g)
            if len(pts) < 3:
                break
            poly = [list(reg.a_m(x, y)) for x, y in pts]
            nivel = regla.get('nivel', reg.nivel)
            t = regla['tipo']
            if t in ('espacio', 'stand') and r.width * r.height >= regla.get('area_min_pt', 40):
                txt = palabras_en(r)
                patron = regla.get('codigo', r'^[A-Z]{1,3}[- ]?\d')
                cod = next((w[4] for w in txt if re.match(patron, w[4]) and not re.match(r'^\d+[xX]\d+$', w[4])), '')
                med = next((w[4].upper() for w in txt if re.match(r'^\d+([.,]\d+)?[xX]\d+([.,]\d+)?$', w[4])), '')
                st = {'codigo': cod, 'nivel': nivel, 'poligono': poly, 'region': reg.id}
                if med:
                    st['medida_rotulo'] = med
                if regla.get('color'):
                    st['color'] = regla['color']
                res['espacios'].append(st)
            elif t == 'silla' and max(r.width, r.height) <= regla.get('lado_max_pt', 15):
                c = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
                e = (poly[1][0] - poly[0][0], poly[1][1] - poly[0][1])
                sillas.setdefault(nivel, []).append([round(c[0], 2), round(c[1], 2), round(math.degrees(math.atan2(e[1], e[0])), 1)])
            elif t == 'zona':
                res['zonas'].append({'id': f"{regla.get('id', 'zona')}_{len(res['zonas'])}", 'nivel': nivel, 'material': regla.get('material', 'pav_plaza'), 'poligono': poly})
            elif t == 'caja':
                c = ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
                res['objetos'].append({'tipo': 'caja', 'nivel': nivel, 'centro': list(reg.a_m(*c)),
                                       'tam': [round(r.width / reg.sx, 2), round(r.height / reg.sy, 2), regla.get('alto', 1)],
                                       'material': regla.get('material', 'blanco')})
            break
    for nivel, pts in sillas.items():
        res['objetos'].append({'tipo': 'sillas_puntos', 'nivel': nivel, 'puntos': pts})

    # espacios repetidos (mismo codigo dibujado dos veces): queda el mas grande
    vistos = {}
    for st in res['espacios']:
        a = abs(area(st['poligono']))
        if not st['codigo'] or st['codigo'] not in vistos or a > abs(area(vistos[st['codigo']]['poligono'])):
            vistos[st['codigo'] or id(st)] = st
    res['espacios'] = list(vistos.values())

    # validacion: espacios rotulados "AxB" contra su medida dibujada
    ok = tot = 0
    for st in res['espacios']:
        m = re.match(r'^(\d+(?:[.,]\d+)?)[xX](\d+(?:[.,]\d+)?)$', st.get('medida_rotulo', ''))
        if not m:
            continue
        a, b = sorted(float(v.replace(',', '.')) for v in m.groups())
        p = st['poligono']; xs = [q[0] for q in p]; ys = [q[1] for q in p]
        lados = sorted(lado_mayor_menor(p))
        tot += 1; ok += abs(lados[0] - a) / a < .12 and abs(lados[1] - b) / b < .12
    res['validacion'] = {'espacios_con_rotulo': tot, 'coinciden_12pct': ok}
    sin_cod = sum(1 for s in res['espacios'] if not s['codigo'])
    (out / 'plano_m.json').write_text(json.dumps(res, ensure_ascii=False), encoding='utf8')
    vista_previa(res, out / 'plano_m.png')
    print(f"{len(res['espacios'])} espacios ({sin_cod} sin codigo) - {sum(len(o['puntos']) for o in res['objetos'] if o['tipo'] == 'sillas_puntos')} sillas - "
          f"{len(res['zonas'])} zonas - {res['sin_region']} dibujos fuera de toda region")
    if tot:
        print(f'Validacion de escala: {ok} de {tot} espacios rotulados coinciden con su medida dibujada (+/-12 %).'
              + ('' if ok / tot > .9 else '  REVISA la escala o la region: menos del 90 % coincide.'))
    print(f'Archivos: {out / "plano_m.json"} y {out / "plano_m.png"}')


def area(p):
    return .5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def lado_mayor_menor(p):
    """Ancho y largo de un poligono casi rectangular (por sus dos lados mas largos distintos)."""
    lados = sorted(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p)))
    return (lados[-3] if len(lados) >= 4 else lados[0]), lados[-1]


def vista_previa(res, ruta, px_m=6):
    pts = [q for s in res['espacios'] for q in s['poligono']] + [q for z in res['zonas'] for q in z['poligono']] +           [q for e in res.get('edificios', []) for q in e['poligono']] + [q for m in res.get('muros', []) for q in m['puntos']] + \
          [q[:2] for o in res['objetos'] if o['tipo'] == 'sillas_puntos' for q in o['puntos']]
    if not pts:
        print('Nada extraido: revisa los colores de relleno de las reglas (mira salida/inspeccion/colores.json).'); return
    x0 = min(p[0] for p in pts) - 5; y1 = max(p[1] for p in pts) + 5
    w = int((max(p[0] for p in pts) + 5 - x0) * px_m); h = int((y1 - min(p[1] for p in pts) + 5) * px_m)
    esc = min(1, 8000 / max(w, h)); px_m *= esc; w, h = int(w * esc), int(h * esc)
    im = Image.new('RGB', (w, h), 'white'); d = ImageDraw.Draw(im); f = fuente(max(9, int(px_m * 1.2)))
    T = lambda q: ((q[0] - x0) * px_m, (y1 - q[1]) * px_m)
    for gx in range(int(x0) // 10 * 10, int(x0 + w / px_m) + 10, 10):     # cuadricula de 10 m
        d.line([T((gx, y1)), T((gx, y1 - h / px_m))], fill=(235, 235, 235))
    for gy in range(int(y1 - h / px_m) // 10 * 10, int(y1) + 10, 10):
        d.line([T((x0, gy)), T((x0 + w / px_m, gy))], fill=(235, 235, 235))
    for z in res['zonas']:
        d.polygon([T(q) for q in z['poligono']], fill=(210, 230, 210), outline=(120, 160, 120))
    for o in res['objetos']:
        if o['tipo'] == 'sillas_puntos':
            for q in o['puntos']:
                c = T(q); d.rectangle([c[0] - 1, c[1] - 1, c[0] + 1, c[1] + 1], fill=(90, 90, 110))
    for e in res.get('edificios', []):
        d.polygon([T(q) for q in e['poligono']], fill=(225, 232, 245), outline=(60, 80, 140))
    for s in res['espacios']:
        d.polygon([T(q) for q in s['poligono']], fill=(246, 190, 192), outline=(160, 60, 70))
        if s['codigo']:
            c = T((sum(q[0] for q in s['poligono']) / len(s['poligono']), sum(q[1] for q in s['poligono']) / len(s['poligono'])))
            d.text(c, s['codigo'], fill=(40, 40, 40), font=f, anchor='mm')
    for m in res.get('muros', []):
        q = m['puntos'] + ([m['puntos'][0]] if m.get('cerrado') else [])
        d.line([T(v) for v in q], fill=(30, 30, 30), width=max(2, int(px_m * m.get('grosor', .15))))
    d.text((8, 8), 'Cuadricula: 10 m - Norte arriba', fill=(120, 120, 120), font=f)
    im.save(ruta)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2:
        ayuda()
    if a[0] == 'inspeccionar' and a[1].lower().endswith('.dxf'):
        import cad
        cad.inspeccionar(a[1], salida_de(a[1]) / 'inspeccion', fuente)
    elif a[0] == 'inspeccionar':
        pag = int(a[a.index('--pagina') + 1]) if '--pagina' in a else 0
        cua = float(a[a.index('--cuadricula') + 1]) if '--cuadricula' in a else 1.0
        inspeccionar(a[1], pag, cua)
    elif a[0] == 'extraer':
        extraer(a[1])
    else:
        ayuda()
