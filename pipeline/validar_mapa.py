"""Revisa mapa.json antes de abrir Blender: errores de forma que harian fallar o verse mal el modelo.

Uso: python pipeline/validar_mapa.py proyectos/<id>/mapa.json
Sale con codigo 1 si hay errores. Los avisos no detienen nada, pero conviene leerlos.
"""
import json, re, sys, pathlib

MATERIALES = {'concreto', 'concreto_pulido', 'piedra_pulida', 'alfombra', 'madera', 'madera_clara', 'pav_plaza', 'pav_arenisca',
              'pav_oscuro', 'cesped', 'asfalto', 'agua', 'arenisca_muro', 'ladrillo', 'vidrio', 'blanco', 'negro', 'panel', 'muro_interior'}
OBJETOS = {'tarima', 'pantalla', 'sillas', 'sillas_puntos', 'mesas', 'carpa', 'arbol', 'escalera', 'caja'}
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
ids = set()
for e in C.get('edificios', []):
    k = f'Edificio {e.get("id")}'
    if e.get('id') in ids:
        err.append(f'{k}: id repetido.')
    ids.add(e.get('id'))
    poly(k, e.get('poligono'))
    if e.get('nivel', 'base') not in niv:
        err.append(f'{k}: nivel "{e.get("nivel")}" no esta en "niveles".')
    if not 2 <= float(e.get('altura', 0)) <= 300:
        avi.append(f'{k}: altura {e.get("altura")} m fuera de lo comun (2 a 300).')
    mat(k, e.get('piso')); mat(k, e.get('fachada'))
    for p in e.get('puertas', []):
        if p['lado'] >= len(e.get('poligono', [])):
            err.append(f'{k}: puerta en el lado {p["lado"]}, pero el poligono solo tiene {len(e["poligono"])} lados (se cuentan desde 0).')
for z in C.get('zonas', []):
    poly(f'Zona {z.get("id")}', z.get('poligono')); mat(f'Zona {z.get("id")}', z.get('material'))
for w in C.get('muros', []):
    if len(w.get('puntos', [])) < 2:
        err.append('Muro con menos de 2 puntos.')
    mat('Muro', w.get('material'))
cods = {}
for s in C.get('espacios', []) + C.get('stands', []):
    poly(f'Espacio {s.get("codigo")}', s.get('poligono'))
    if s.get('codigo'):
        cods[s['codigo']] = cods.get(s['codigo'], 0) + 1
rep = [c for c, n in cods.items() if n > 1]
if rep:
    avi.append(f'Codigos de espacio repetidos: {", ".join(rep[:10])}{"..." if len(rep) > 10 else ""}')
for i, o in enumerate(C.get('objetos', [])):
    if o.get('tipo') not in OBJETOS:
        err.append(f'Objeto {i}: tipo "{o.get("tipo")}" no existe ({", ".join(sorted(OBJETOS))}).')
nums = [p.get('n') for p in C.get('pines', [])]
if len(nums) != len(set(nums)):
    err.append('Hay pines con el mismo numero "n".')
for p in C.get('pines', []):
    if p.get('nivel', 'base') not in niv:
        err.append(f'Pin {p.get("n")}: nivel "{p.get("nivel")}" no esta en "niveles".')
for rel in ([C['importar']] if isinstance(C.get('importar'), str) else C.get('importar', [])):
    if not (ruta.parent / rel).exists():
        err.append(f'importar: no existe {rel}. Corre antes pipeline/extraer_plano.py extraer.')
if C.get('calco') and not (ruta.parent / C['calco'].get('imagen', '')).exists():
    err.append('calco: no existe la imagen.')
if C.get('marca', {}).get('logo') and not (ruta.parent / C['marca']['logo']).exists():
    err.append('marca.logo: no existe el archivo del logo.')
if not C.get('pines'):
    avi.append('No hay pines: el visor quedara sin lista de lugares.')

for a in avi:
    print('AVISO ', a)
for e in err:
    print('ERROR ', e)
print(f'{len(C.get("edificios", []))} edificios, {len(C.get("espacios", []))} espacios a mano, {len(C.get("muros", []))} muros, {len(C.get("pines", []))} pines, '
      f'{len(niv)} niveles -> {len(err)} errores, {len(avi)} avisos')
sys.exit(1 if err else 0)
