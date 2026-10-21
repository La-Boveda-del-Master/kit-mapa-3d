"""Genera entrada/plano.pdf: un plano tecnico de juguete para probar pipeline/extraer_plano.py.

Imita lo que trae un plano real: cuadricula de fondo de 1 m como imagen, contorno del pabellon,
locales rellenos de rosado con su codigo y su medida ("5x6"), y sillas como cuadritos grises.
Escala: 10 pt = 1 m. El punto (100, 900) del PDF es el origen (0, 0) del mundo.
"""
import pathlib
import numpy as np
import pymupdf

AQUI = pathlib.Path(__file__).resolve().parent
S, OX, OY = 10.0, 100.0, 900.0
P = lambda x, y: (OX + x * S, OY - y * S)          # metros -> puntos PDF (y del PDF hacia abajo)

doc = pymupdf.open(); page = doc.new_page(width=700, height=1000)
# cuadricula de 1 m como imagen (2 px por punto -> periodo de 20 px)
g = np.full((2000, 1400), 255, np.uint8); g[::20, :] = 205; g[:, ::20] = 205
pix = pymupdf.Pixmap(pymupdf.csGRAY, 1400, 2000, g.tobytes(), False)
page.insert_image(page.rect, pixmap=pix)
# contorno del Pabellon A (42 x 70 m)
x0, y0 = P(0, 70); x1, y1 = P(42, 0)
page.draw_rect(pymupdf.Rect(x0, y0, x1, y1), color=(0, 0, 0), width=2)
page.insert_text((x0 + 4, y0 + 14), 'EDIFICIO A', fontsize=10)
# fila de locales A10..A15 (5 x 6 m)
for i in range(6):
    a = P(4 + i * 6, 20); b = P(9 + i * 6, 14)
    r = pymupdf.Rect(a[0], a[1], b[0], b[1])
    page.draw_rect(r, color=(.5, .2, .2), fill=(.95, .62, .64), width=.5)
    page.insert_text((r.x0 + 6, r.y0 + 22), f'A{10 + i}', fontsize=9)
    page.insert_text((r.x0 + 10, r.y0 + 40), '5x6', fontsize=7)
# sillas frente a la tarima de demostraciones
for ix in range(30):
    for iy in range(6):
        c = P(9 + ix * .6, 22.5 + iy * 1.0)
        page.draw_rect(pymupdf.Rect(c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2), color=None, fill=(.69, .68, .68))
doc.save(AQUI / 'plano.pdf')
print('plano.pdf listo')
