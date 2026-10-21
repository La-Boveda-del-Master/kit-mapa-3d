"""Agrega la leyenda de pines numerados a los renders del mapa (v03).

Uso: python componer_leyenda.py [sufijo]      (sufijo = tag de render, p. ej. r1; vacio = sin tag)
Entrada: renders_v03/<vista>[_tag].png + leyenda_v03.json     Salida: renders_v03/<vista>[_tag]_leyenda.png
"""
import json, pathlib, sys
from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
tag = ('_' + sys.argv[1]) if len(sys.argv) > 1 else ''
LEY = json.loads((R / 'leyenda_v03.json').read_text(encoding='utf8'))
# pines visibles en cada vista
VISTAS = {'mapa_iso': None, 'maqueta_iso': {'Nivel principal', 'Nivel superior'},
          'mapa_planta': {'Nivel principal', 'Nivel superior', 'Caja · piso 3'},
          'mapa_planta_inferior': {'Nivel principal', 'Nivel inferior', 'Convenciones · piso 1'},
          'mapa_planta_intermedia': {'Nivel principal', 'Nivel inferior', 'Convenciones · piso 2'},
          'mapa_niveles_caja': None, 'mapa_niveles_azul_verde': None}
TITULOS = {'mapa_iso': 'Mapa general · niveles separados', 'maqueta_iso': 'Vista exterior',
           'mapa_planta': 'Planta · nivel principal, superior y Caja de Madera (piso 3)',
           'mapa_planta_inferior': 'Planta · nivel inferior y Gran Salón (piso 1)',
           'mapa_planta_intermedia': 'Planta · Salón Multipropósito (piso 2)',
           'mapa_niveles_caja': 'Caja de Madera · Salón Multipropósito · Gran Salón',
           'mapa_niveles_azul_verde': 'Azul sobre Rojo · Verde sobre Auditorio Comunidades'}


def font(size, bold=True):
    return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', size)


def pin_icon(d, cx, cy, r, col, n, f):
    """Pin de mapa (gota con circulo blanco y numero)."""
    d.polygon([(cx - r * .82, cy + r * .45), (cx + r * .82, cy + r * .45), (cx, cy + r * 1.85)], fill=col)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    d.ellipse((cx - r * .64, cy - r * .64, cx + r * .64, cy + r * .64), fill='white')
    t = str(n); w = d.textlength(t, font=f)
    d.text((cx - w / 2, cy - f.size * .68), t, font=f, fill=tuple(int(c * .55) for c in col))


for vista, niveles in VISTAS.items():
    src = R / 'renders_v03' / f'{vista}{tag}.png'
    if not src.exists():
        continue
    im = Image.open(src).convert('RGB')
    W, H = im.size
    items = [e for e in LEY if niveles is None or e['nivel'] in niveles]
    PW = int(W * .27); u = H / 1960                   # panel lateral; u = unidad de escala
    out = Image.new('RGB', (W + PW, H), (250, 249, 246)); out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    x0 = W + int(34 * u); y = int(46 * u)
    d.text((x0, y), 'FERIA EFFIX 2026', font=font(int(50 * u)), fill=(20, 20, 22)); y += int(62 * u)
    d.text((x0, y), 'Plaza Mayor Medellín · 15 al 18 de octubre', font=font(int(25 * u), False), fill=(90, 90, 95)); y += int(40 * u)
    d.text((x0, y), TITULOS[vista], font=font(int(23 * u)), fill=(134, 15, 26)); y += int(52 * u)
    d.line((x0, y, W + PW - int(34 * u), y), fill=(205, 203, 198), width=max(1, int(2 * u))); y += int(22 * u)
    row = min(int(84 * u), int((H - y - 60 * u) / max(1, len(items))))
    r = int(row * .30); fn = font(int(r * 1.0)); f1 = font(int(row * .30)); f2 = font(int(row * .215), False); f3 = font(int(row * .19))
    for e in items:
        col = tuple(int(c ** (1 / 2.2) * 255) for c in e['color'])       # color lineal del material -> sRGB
        pin_icon(d, x0 + r, y + r + 2, r, col, e['n'], fn)
        tx = x0 + int(r * 2.9)
        d.text((tx, y - 2), e['nombre'], font=f1, fill=(22, 22, 25))
        d.text((tx, y + int(row * .36)), e['detalle'], font=f2, fill=(95, 95, 100))
        wn = d.textlength(e['nivel'].upper(), font=f3)
        d.text((W + PW - int(34 * u) - wn, y + int(row * .62)), e['nivel'].upper(), font=f3, fill=col)
        y += row
    d.text((x0, H - int(44 * u)), 'Escala según plano técnico (cuadrícula 1 m). Alturas y entorno aproximados.', font=font(int(17 * u), False), fill=(130, 130, 135))
    dst = R / 'renders_v03' / f'{vista}{tag}_leyenda.png'
    out.save(dst)
    print('leyenda', dst.name, out.size)
