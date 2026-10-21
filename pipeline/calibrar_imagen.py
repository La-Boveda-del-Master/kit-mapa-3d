"""Planos en imagen (JPG/PNG, escaneos, capturas, renders de arquitecto): calibrar la escala y dibujar encima en metros.

Paso 1 - regla en pixeles, para leer las coordenadas de dos puntos de medida conocida:
  python pipeline/calibrar_imagen.py proyectos/<id>/entrada/plano.jpg
      -> salida/inspeccion/imagen_pixeles.png

Paso 2 - con dos puntos y su distancia real, cuadricula en metros sobre la imagen:
  python pipeline/calibrar_imagen.py proyectos/<id>/entrada/plano.jpg --puntos 120,340,860,340 --distancia 42.5 [--origen 120,900]
      -> salida/inspeccion/imagen_metros.png  (cuadricula cada 5 m con coordenadas del mundo: X este, Y norte)
      -> imprime px_por_m y el bloque "calco" para pegar en mapa.json

--origen: pixel que sera el (0, 0) del mundo (por defecto la esquina inferior izquierda de la imagen).
Con imagen_metros.png abierta se leen las esquinas de edificios, muros y espacios directamente en metros
para escribirlas en mapa.json. El "calco" pone la imagen bajo el modelo para comprobar en los renders (--calco).
Supone que la imagen tiene el norte arriba y la misma escala en X y Y (planos escaneados torcidos: enderezar antes).
"""
import math, sys, pathlib
from PIL import Image, ImageDraw, ImageFont


def fuente(t):
    for f in ('C:/Windows/Fonts/segoeui.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if pathlib.Path(f).exists():
            return ImageFont.truetype(f, t)
    return ImageFont.load_default()


a = sys.argv[1:]
if not a:
    raise SystemExit(__doc__)
ruta = pathlib.Path(a[0]).resolve()
base = ruta.parent.parent if ruta.parent.name == 'entrada' else ruta.parent
out = base / 'salida' / 'inspeccion'; out.mkdir(parents=True, exist_ok=True)
im = Image.open(ruta).convert('RGB'); W, H = im.size
opt = {a[i].lstrip('-'): a[i + 1] for i in range(1, len(a) - 1) if a[i].startswith('--')}
d = ImageDraw.Draw(im); f = fuente(max(12, W // 120))

if 'puntos' not in opt:
    paso = 10 ** math.floor(math.log10(max(W, H) / 10)) * (5 if max(W, H) / 10 ** math.floor(math.log10(max(W, H) / 10)) > 50 else 1)
    for x in range(0, W, paso):
        d.line([(x, 0), (x, H)], fill=(255, 0, 0) if x % (paso * 5) == 0 else (255, 170, 170), width=1)
        d.text((x + 2, 2), str(x), fill=(200, 0, 0), font=f)
    for y in range(0, H, paso):
        d.line([(0, y), (W, y)], fill=(255, 0, 0) if y % (paso * 5) == 0 else (255, 170, 170), width=1)
        d.text((2, y + 2), str(y), fill=(200, 0, 0), font=f)
    im.save(out / 'imagen_pixeles.png')
    print(f'Imagen {W} x {H} px. Regla en pixeles: {out / "imagen_pixeles.png"}')
    print('Busca dos puntos de medida conocida (una cota, el largo de un muro, la cuadricula) y corre con --puntos x1,y1,x2,y2 --distancia metros')
    sys.exit(0)

x1, y1, x2, y2 = map(float, opt['puntos'].split(','))
dist = float(opt['distancia'])
ppm = math.dist((x1, y1), (x2, y2)) / dist
ox, oy = map(float, opt['origen'].split(',')) if 'origen' in opt else (0.0, float(H))
to_m = lambda px, py: ((px - ox) / ppm, (oy - py) / ppm)
to_px = lambda mx, my: (ox + mx * ppm, oy - my * ppm)
mx0, my1 = to_m(0, 0); mx1, my0 = to_m(W, H)
paso = 5 if max(mx1 - mx0, my1 - my0) < 300 else 20
capa = Image.new('RGBA', im.size, (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
for v in range(math.floor(mx0 / paso) * paso, math.ceil(mx1) + 1, paso):
    x = to_px(v, 0)[0]
    dc.line([(x, 0), (x, H)], fill=(0, 110, 255, 170 if v % (paso * 2) == 0 else 90), width=2 if v == 0 else 1)
    dc.text((x + 3, 3), f'{v} m', fill=(0, 70, 200, 255), font=f)
for v in range(math.floor(my0 / paso) * paso, math.ceil(my1) + 1, paso):
    y = to_px(0, v)[1]
    dc.line([(0, y), (W, y)], fill=(0, 110, 255, 170 if v % (paso * 2) == 0 else 90), width=2 if v == 0 else 1)
    dc.text((3, y + 3), f'{v} m', fill=(0, 70, 200, 255), font=f)
dc.line([(x1, y1), (x2, y2)], fill=(255, 0, 0, 255), width=3)
dc.text(((x1 + x2) / 2, (y1 + y2) / 2 - 18), f'{dist} m', fill=(220, 0, 0, 255), font=f)
Image.alpha_composite(im.convert('RGBA'), capa).convert('RGB').save(out / 'imagen_metros.png')
rel = ruta.relative_to(base).as_posix()
print(f'Escala: {ppm:.3f} px por metro. La imagen cubre {mx1 - mx0:.1f} x {my1 - my0:.1f} m.')
print(f'Cuadricula en metros (cada {paso} m): {out / "imagen_metros.png"}')
print('Para ver la imagen bajo el modelo en los renders (--calco), agrega a mapa.json:')
print(f'  "calco": {{ "imagen": "{rel}", "px_por_m": {ppm:.4f}, "origen_px": [{ox:g}, {oy:g}], "origen_m": [0, 0] }}')
