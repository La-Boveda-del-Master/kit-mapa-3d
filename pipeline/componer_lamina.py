"""Compone la lamina final a partir de un render: titulo, pines numerados, leyenda, norte, escala grafica y nota.

Uso:
  python pipeline/componer_lamina.py proyectos/<id>/salida/renders/axo_realista.png [--sin-pines] [--leyenda=derecha|abajo]
Entrada: el PNG y su .json (los deja renders.py) + el mapa.json del proyecto (marca y colores).
Salida:  junto al render, lamina_<vista>_<estilo>.png y .pdf (el PDF a 300 ppp, listo para imprenta).
"""
import json, math, sys, pathlib
from PIL import Image, ImageDraw, ImageFont

a = sys.argv[1:]
if not a:
    raise SystemExit(__doc__)
REN = pathlib.Path(a[0]).resolve()
META = json.loads(REN.with_suffix('.json').read_text(encoding='utf8'))
PROY = REN.parent.parent.parent
cfg_path = PROY / 'mapa.json' if (PROY / 'mapa.json').exists() else next(PROY.glob('*.json'))
CFG = json.loads(cfg_path.read_text(encoding='utf8'))
MC = CFG.get('marca', CFG.get('evento', {}))
op = {x.split('=')[0].lstrip('-'): (x.split('=', 1)[1] if '=' in x else True) for x in a[1:]}


def fuente(t, negrita=False):
    cands = (['C:/Windows/Fonts/segoeuib.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
             if negrita else ['C:/Windows/Fonts/segoeui.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])
    for f in cands:
        if pathlib.Path(f).exists():
            return ImageFont.truetype(f, int(t))
    return ImageFont.load_default()


def srgb(c):
    return tuple(int(round(min(1, max(0, v)) ** (1 / 2.2) * 255)) for v in c[:3])


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


render = Image.open(REN).convert('RGBA')
W, H = render.size
u = W / 1000                                              # unidad de diseno: todo escala con el ancho
pines = [p for p in META['pines'] if p['visible']] if not op.get('sin-pines') else []
todos = META['pines']
acento = hexrgb(MC.get('color', '#e11d2a'))
tinta = (22, 24, 30)
lado = op.get('leyenda', 'derecha' if W >= H else 'abajo')

# ---------------------------------------------------------------- pines sobre el render
d = ImageDraw.Draw(render)
r = 11 * u; fn = fuente(12 * u, True)
for p in sorted(pines, key=lambda q: q['y']):
    x, y = p['x'], p['y']; c = srgb(p['color'])
    d.ellipse((x - r * .28, y - r * .12, x + r * .28, y + r * .12), fill=(0, 0, 0, 90))            # sombra en el piso
    d.polygon([(x - r * .78, y - r * 1.7), (x + r * .78, y - r * 1.7), (x, y)], fill=c)
    d.ellipse((x - r, y - r * 2.85, x + r, y - r * .85), fill=c, outline=(255, 255, 255), width=max(2, int(u * 1.6)))
    d.text((x, y - r * 1.85), str(p['n']), font=fn, fill=(255, 255, 255), anchor='mm')

# norte (arriba a la derecha del render)
cx, cy, rn = W - 46 * u, 46 * u, 22 * u
d.ellipse((cx - rn, cy - rn, cx + rn, cy + rn), fill=(255, 255, 255, 225), outline=(0, 0, 0, 40), width=max(1, int(u)))
ang = math.radians(META.get('norte_grados', 0))
rot = lambda dx, dy: (cx + dx * math.cos(ang) - dy * math.sin(ang), cy + dx * math.sin(ang) + dy * math.cos(ang))
d.polygon([rot(0, -rn * .78), rot(rn * .3, 0), rot(-rn * .3, 0)], fill=acento)
d.polygon([rot(0, rn * .78), rot(rn * .3, 0), rot(-rn * .3, 0)], fill=(150, 154, 162))
d.text(rot(0, -rn * 1.32), 'N', font=fuente(11 * u, True), fill=tinta, anchor='mm')

# escala grafica (solo en planta, donde es exacta)
if META.get('px_por_m'):
    ppm = META['px_por_m']
    largo = next(v for v in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000) if v * ppm >= W * .12)
    x0, y0 = 28 * u, H - 30 * u; L = largo * ppm; h = 5 * u
    d.rectangle((x0 - 8 * u, y0 - 24 * u, x0 + L + 40 * u, y0 + 12 * u), fill=(255, 255, 255, 215))
    for k in range(4):
        d.rectangle((x0 + L * k / 4, y0, x0 + L * (k + 1) / 4, y0 + h), fill=tinta if k % 2 == 0 else (255, 255, 255), outline=tinta)
    f = fuente(9 * u)
    for k, t in ((0, '0'), (2, f'{largo / 2:g}'), (4, f'{largo:g} m')):
        d.text((x0 + L * k / 4, y0 - 4 * u), t, font=f, fill=tinta, anchor='md')

# ---------------------------------------------------------------- lienzo con titulo y leyenda
m = 34 * u
ft, fs, fl, fln, fn2 = fuente(30 * u, True), fuente(14 * u), fuente(12.5 * u, True), fuente(11 * u), fuente(9.5 * u)
cab = 92 * u                                                   # alto de la cabecera
filas = [(p['n'], p['nombre'], p.get('detalle') or p.get('nivel', ''), srgb(p['color'])) for p in todos]
fila_h = 34 * u
if lado == 'derecha':
    ley_w = 300 * u
    lienzo = Image.new('RGB', (int(W + ley_w + m * 3), int(H + cab + m * 3)), (248, 247, 244))
    rx, ry = m, cab + m * 1.5
    lx, ly = W + m * 2, cab + m * 1.5
    ley_max_h = H
else:
    cols = 2 if W >= 1400 else 1
    ley_rows = math.ceil(len(filas) / cols)
    lienzo = Image.new('RGB', (int(W + m * 2), int(H + cab + m * 3 + ley_rows * fila_h + 40 * u)), (248, 247, 244))
    rx, ry = m, cab + m * 1.5
    lx, ly = m, cab + m * 2.5 + H
    ley_w = (W - m) / cols; ley_max_h = 10 ** 9
D = ImageDraw.Draw(lienzo)
fondo = Image.new('RGBA', render.size, (248, 247, 244, 255))
lienzo.paste(Image.alpha_composite(fondo, render).convert('RGB'), (int(rx), int(ry)))
D.rectangle((rx, ry, rx + W, ry + H), outline=(220, 218, 212), width=max(1, int(u)))

# cabecera: barra de acento, titulo, subtitulo
D.rectangle((m, m, m + 6 * u, m + cab - 14 * u), fill=acento)
D.text((m + 20 * u, m - 2 * u), MC.get('titulo', CFG.get('nombre', '')), font=ft, fill=tinta)
D.text((m + 21 * u, m + 42 * u), MC.get('subtitulo', ''), font=fs, fill=(95, 98, 106))
vista = {'axo': 'Vista axonométrica', 'aerea': 'Vista aérea', 'planta': 'Planta', 'niveles': 'Por niveles', 'corte': 'Interiores'}.get(META['vista'], META['vista'])
D.text((lienzo.width - m, m + 6 * u), vista.upper(), font=fuente(11 * u, True), fill=(140, 142, 150), anchor='ra')

# leyenda
if filas:
    D.text((lx, ly - 4 * u), MC.get('etiqueta_lugares', 'Lugares').upper(), font=fuente(11 * u, True), fill=(140, 142, 150))
    y = ly + 24 * u; x = lx; col = 0
    for n, nombre, det, c in filas:
        if lado == 'derecha' and y + fila_h > ly + ley_max_h:
            break
        rr = 11 * u
        D.ellipse((x, y, x + rr * 2, y + rr * 2), fill=c)
        D.text((x + rr, y + rr), str(n), font=fuente(10.5 * u, True), fill=(255, 255, 255), anchor='mm')
        D.text((x + rr * 2 + 10 * u, y - 1 * u), nombre[:42], font=fl, fill=tinta)
        D.text((x + rr * 2 + 10 * u, y + 15 * u), det[:56], font=fn2, fill=(110, 112, 120))
        y += fila_h
        if lado != 'derecha' and (filas.index((n, nombre, det, c)) + 1) % math.ceil(len(filas) / max(1, round((W - m) / ley_w))) == 0:
            col += 1; x = lx + col * ley_w; y = ly + 24 * u
# nota al pie
D.text((m, lienzo.height - m * .55), MC.get('nota', ''), font=fn2, fill=(130, 132, 140), anchor='ls')
D.text((lienzo.width - m, lienzo.height - m * .55), 'Hecho con Kit Mapa 3D', font=fn2, fill=(170, 172, 178), anchor='rs')

dest = REN.parent / f"lamina_{REN.stem}"
lienzo.save(dest.with_suffix('.png'))
lienzo.save(dest.with_suffix('.pdf'), resolution=300)
print(f'LAMINA {dest.with_suffix(".png")} ({lienzo.width} x {lienzo.height} px) y .pdf - {len(pines)} pines visibles de {len(todos)}')
