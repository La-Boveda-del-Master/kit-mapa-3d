"""Crea la carpeta de un recinto nuevo con plantillas listas para llenar.

Uso: python pipeline/nuevo_proyecto.py <id-del-recinto> ["Nombre del recinto"]
Crea proyectos/<id>/ con entrada/ (ahi van el PDF, fotos y referencias), recinto.json y plano.json.
"""
import json, re, sys, pathlib

KIT = pathlib.Path(__file__).resolve().parent.parent
if len(sys.argv) < 2:
    raise SystemExit(__doc__)
pid = re.sub(r'[^a-z0-9-]+', '-', sys.argv[1].lower()).strip('-')
nombre = sys.argv[2] if len(sys.argv) > 2 else pid.replace('-', ' ').title()
P = KIT / 'proyectos' / pid
if (P / 'recinto.json').exists():
    raise SystemExit(f'Ya existe {P / "recinto.json"}; no lo sobrescribo.')
(P / 'entrada').mkdir(parents=True, exist_ok=True)

recinto = {
    'id': pid, 'nombre': nombre,
    'evento': {'titulo': nombre.upper(), 'subtitulo': 'Ciudad - fechas del evento', 'nota': 'Escala según plano técnico. Alturas y entorno aproximados.',
               'titulo_lista': 'Lugares'},
    'stands_desde': [],
    'terreno': {'margen': 80, 'material': 'concreto', 'vias': []},
    'niveles': [{'id': 'base', 'nombre': 'Nivel principal', 'z': 0}],
    'edificios': [{'id': 'pabellon_1', 'nombre': 'Pabellón 1', 'nivel': 'base', 'poligono': [[0, 0], [40, 0], [40, 60], [0, 60]],
                   'altura': 8, 'color': [0.08, 0.38, 0.82], 'piso': 'concreto_pulido', 'puertas': [{'lado': 0, 'centro': 20, 'ancho': 6}]}],
    'zonas': [], 'stands': [], 'objetos': [],
    'pines': [{'n': 1, 'nombre': 'Ingreso', 'detalle': 'Por dónde entra el público', 'nivel': 'base', 'pos': [20, -5, 4], 'color': [0.85, 0.2, 0.25]}],
}
plano = {
    'pdf': 'entrada/plano.pdf', 'pagina': 0,
    'regiones': [{'id': 'principal', 'nivel': 'base', 'escala_pt_m': [10, 10], 'origen_pt': [0, 0], 'origen_m': [0, 0], 'rotacion': 0}],
    'reglas': [{'tipo': 'stand', 'relleno': [0.95, 0.62, 0.64], 'tolerancia': 0.03, 'area_min_pt': 40, 'codigo': '^[A-Z]{1,3}[- ]?[0-9]'}],
}
(P / 'recinto.json').write_text(json.dumps(recinto, indent=2, ensure_ascii=False), encoding='utf8')
(P / 'plano.json').write_text(json.dumps(plano, indent=2, ensure_ascii=False), encoding='utf8')
print(f'Proyecto creado en {P}')
print('Siguiente: copia el plano a entrada/plano.pdf y corre  python pipeline/extraer_plano.py inspeccionar', P / 'entrada' / 'plano.pdf')
