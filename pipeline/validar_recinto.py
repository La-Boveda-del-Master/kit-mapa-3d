"""Revisa recinto.json antes de abrir Blender: errores de forma que harian fallar o verse mal el modelo.

Uso: python pipeline/validar_recinto.py proyectos/<recinto>/recinto.json
Sale con codigo 1 si hay errores. Los avisos no detienen nada, pero conviene leerlos.
"""
import json, re, sys, pathlib

MATERIALES = {'concreto', 'concreto_pulido', 'piedra_pulida', 'alfombra', 'madera', 'madera_clara', 'pav_plaza', 'pav_arenisca',
              'pav_oscuro', 'cesped', 'asfalto', 'agua', 'arenisca_muro', 'ladrillo', 'vidrio', 'blanco', 'negro', 'panel'}
OBJETOS = {'tarima', 'pantalla', 'sillas', 'sillas_puntos', 'carpa', 'arbol', 'caja'}
err, avi = [], []


def area(p):
    return .5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def poly(nombre, p):
    if not isinstance(p, list) or len(p) < 3 or any(len(q) != 2 for q in p):
        err.append(f'{nombre}: el poligono necesita 3 o mas puntos [x, y].'); return
    if abs(area(p)) < .5:
        err.append(f'{nombre}: el poligono no tiene area (puntos repetidos o en linea).')
    xs = [q[0] for q in p] + [q[1] for q in p]
    if max(abs(v) for v in xs) > 5000:
        avi.append(f'{nombre}: coordenadas de mas de 5 km: ¿quedaron en puntos PDF en vez de metros?')


def mat(nombre, m):
    if m is None or isinstance(m, list):
        return
    if m not in MATERIALES:
        err.append(f'{nombre}: material "{m}" no existe. Opciones: {", ".join(sorted(MATERIALES))} o un color [r, g, b].')


ruta = pathlib.Path(sys.argv[1]); C = json.loads(ruta.read_text(encoding='utf8'))
niv = {n['id']: n for n in C.get('niveles', [])}
if 'base' not in niv and not niv:
    err.append('Faltan "niveles".')
for n in C.get('niveles', []):
    if n.get('separacion', 0) and n.get('bajo_techo'):
        avi.append(f'Nivel {n["id"]}: tiene separacion y bajo_techo a la vez; normalmente el que flota es el de arriba y el bajo_techo es el de abajo.')
ids = set()
for e in C.get('edificios', []):
    k = f'Edificio {e.get("id")}'
    if e.get('id') in ids:
        err.append(f'{k}: id repetido.')
    ids.add(e.get('id'))
    poly(k, e.get('poligono'))
    if e.get('nivel', 'base') not in niv:
        err.append(f'{k}: nivel "{e.get("nivel")}" no esta en "niveles".')
    if not 2 <= float(e.get('altura', 0)) <= 60:
        avi.append(f'{k}: altura {e.get("altura")} m fuera de lo comun (2 a 60).')
    mat(k, e.get('piso')); mat(k, e.get('fachada'))
    for p in e.get('puertas', []):
        if p['lado'] >= len(e.get('poligono', [])):
            err.append(f'{k}: puerta en el lado {p["lado"]}, pero el poligono solo tiene {len(e["poligono"])} lados (se cuentan desde 0).')
for z in C.get('zonas', []):
    poly(f'Zona {z.get("id")}', z.get('poligono')); mat(f'Zona {z.get("id")}', z.get('material'))
cods = {}
for s in C.get('stands', []):
    poly(f'Stand {s.get("codigo")}', s.get('poligono'))
    if s.get('codigo'):
        cods[s['codigo']] = cods.get(s['codigo'], 0) + 1
rep = [c for c, n in cods.items() if n > 1]
if rep:
    avi.append(f'Codigos de stand repetidos: {", ".join(rep[:10])}{"..." if len(rep) > 10 else ""}')
for i, o in enumerate(C.get('objetos', [])):
    if o.get('tipo') not in OBJETOS:
        err.append(f'Objeto {i}: tipo "{o.get("tipo")}" no existe ({", ".join(sorted(OBJETOS))}).')
nums = [p.get('n') for p in C.get('pines', [])]
if len(nums) != len(set(nums)):
    err.append('Hay pines con el mismo numero "n".')
for p in C.get('pines', []):
    if p.get('nivel', 'base') not in niv:
        err.append(f'Pin {p.get("n")}: nivel "{p.get("nivel")}" no esta en "niveles".')
for rel in ([C['stands_desde']] if isinstance(C.get('stands_desde'), str) else C.get('stands_desde', [])):
    if not (ruta.parent / rel).exists():
        err.append(f'stands_desde: no existe {rel}. Corre antes pipeline/extraer_plano.py extraer.')
if not C.get('pines'):
    avi.append('No hay pines: el visor quedara sin lista de lugares.')

for a in avi:
    print('AVISO ', a)
for e in err:
    print('ERROR ', e)
print(f'{len(C.get("edificios", []))} edificios, {len(C.get("stands", []))} stands a mano, {len(C.get("pines", []))} pines, '
      f'{len(niv)} niveles -> {len(err)} errores, {len(avi)} avisos')
sys.exit(1 if err else 0)
