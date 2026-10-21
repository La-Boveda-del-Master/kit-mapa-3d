"""Genera entrada/plano.dxf: plano CAD de juguete de una oficina de 3 pisos, como lo entregaria un arquitecto.

Imita un DXF real: unidades en milimetros, los tres pisos dibujados uno al lado del otro (separados 40 m),
y capas separadas para el contorno del edificio, los muros interiores, los espacios (salas), los textos
y el mobiliario. Correr: python ejemplos/oficina-demo/entrada/generar_dxf_demo.py
"""
import pathlib
import ezdxf

AQUI = pathlib.Path(__file__).resolve().parent
doc = ezdxf.new('R2010', units=4)                  # 4 = milimetros ($INSUNITS)
msp = doc.modelspace()
for capa, color in (('A-EDIFICIO', 7), ('A-MUROS', 1), ('A-ESPACIOS', 3), ('A-TEXTOS', 2), ('A-MOBILIARIO', 8)):
    doc.layers.add(capa, color=color)
MM = 1000
W, H = 30, 20                                      # planta de 30 x 20 m


def rect(x0, y0, x1, y1, capa):
    msp.add_lwpolyline([(x0 * MM, y0 * MM), (x1 * MM, y0 * MM), (x1 * MM, y1 * MM), (x0 * MM, y1 * MM)], close=True, dxfattribs={'layer': capa})


def linea(a, b):
    msp.add_line((a[0] * MM, a[1] * MM), (b[0] * MM, b[1] * MM), dxfattribs={'layer': 'A-MUROS'})


def texto(t, x, y, h=.35):
    msp.add_text(t, height=h * MM, dxfattribs={'layer': 'A-TEXTOS'}).set_placement((x * MM, y * MM))


def sala(ox, x0, y0, x1, y1, codigo, nombre):
    rect(ox + x0 + .1, y0 + .1, ox + x1 - .1, y1 - .1, 'A-ESPACIOS')
    texto(codigo, ox + (x0 + x1) / 2 - .5, (y0 + y1) / 2 + .2)
    texto(nombre, ox + (x0 + x1) / 2 - 1.2, (y0 + y1) / 2 - .5, .3)


PISOS = {
    0: [(0, 0, 10, 8, 'P1-01', 'Recepcion'), (10, 0, 18, 8, 'P1-02', 'Sala de espera'), (18, 0, 30, 8, 'P1-03', 'Cafeteria'),
        (0, 12, 8, 20, 'P1-04', 'Sala de juntas'), (8, 12, 14, 20, 'P1-05', 'Banos'), (22, 12, 30, 20, 'P1-06', 'Showroom')],
    40: [(0, 0, 12, 8, 'P2-01', 'Oficina abierta'), (12, 0, 20, 8, 'P2-02', 'Sala creativa'), (20, 0, 30, 8, 'P2-03', 'Gerencia'),
         (0, 12, 8, 20, 'P2-04', 'Sala 1'), (8, 12, 14, 20, 'P2-05', 'Sala 2'), (14, 12, 22, 20, 'P2-06', 'Archivo'), (22, 12, 30, 20, 'P2-07', 'Sistemas')],
    80: [(0, 0, 18, 20, 'P3-01', 'Auditorio'), (18, 0, 30, 10, 'P3-02', 'Terraza'), (18, 10, 30, 20, 'P3-03', 'Sala VIP')],
}
for ox, salas in PISOS.items():
    rect(ox, 0, ox + W, H, 'A-EDIFICIO')
    for x0, y0, x1, y1, cod, nom in salas:
        sala(ox, x0, y0, x1, y1, cod, nom)
    # muros interiores: pasillo central (y 8-12) con vanos de puertas, y divisiones entre salas
    for y in (8, 12):
        xs = sorted({x for s in salas for x in (s[0], s[2]) if (s[1] if y == 12 else s[3]) == y})
        for a, b in zip(xs, xs[1:]):
            m = (a + b) / 2
            linea((ox + a, y), (ox + m - .5, y)); linea((ox + m + .5, y), (ox + b, y))   # puerta de 1 m en el medio
    for x0, y0, x1, y1, *_ in salas:
        if x0 > 0:
            linea((ox + x0, y0), (ox + x0, y1))
    texto(['PISO 1', 'PISO 2', 'PISO 3'][ox // 40], ox + 12, -2, .8)
# mobiliario: escritorios en la oficina abierta del piso 2 y mesa de juntas en el piso 1
for i in range(4):
    for j in range(2):
        rect(40 + 1.5 + i * 2.6, 1.5 + j * 3.2, 40 + 3.1 + i * 2.6, 2.3 + j * 3.2, 'A-MOBILIARIO')
rect(2, 14.5, 6, 17.5, 'A-MOBILIARIO')
doc.saveas(AQUI / 'plano.dxf')
print('plano.dxf listo (mm, 3 pisos lado a lado)')
