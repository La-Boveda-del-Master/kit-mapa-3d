"""Exporta el modelo a una carpeta web lista para publicar (visor three.js + mapa.glb con Draco + datos.json).

Uso: blender -b proyectos/<id>/salida/modelo.blend --python pipeline/exportar_web.py -- proyectos/<id>/mapa.json
Salida: proyectos/<id>/salida/web/   (index.html, app.js, estilos.css, draco/, mapa.glb, datos.json, logo si hay)

- Convierte los textos en mallas y une los codigos de los espacios de cada nivel en una sola malla (menos llamadas de dibujo).
- Cada objeto lleva en `extras.grupo` su grupo (nivel, techo_<nivel>, entorno); los niveles que se separan cuelgan
  de los vacios RAIZ_<nivel>. El visor lee eso para el modo "Por niveles".
- Escribe datos.json con marca, niveles, lugares (pines) y espacios (posicion 3D en metros: X este, Y norte, Z alto).
- Sella la version en index.html/app.js para que el navegador no use un modelo viejo en cache.
No guarda cambios en el .blend.
"""
import bpy, bmesh, json, pathlib, re, shutil, sys, time

KIT = pathlib.Path(__file__).resolve().parent.parent
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not argv:
    raise SystemExit('Falta la ruta de mapa.json')
CFG_PATH = pathlib.Path(argv[0]).resolve()
CFG = json.loads(CFG_PATH.read_text(encoding='utf8'))
PROY = CFG_PATH.parent
CFG.setdefault('espacios', []).extend(CFG.pop('stands', []))
for rel in ([CFG['importar']] if isinstance(CFG.get('importar'), str) else CFG.get('importar', [])):
    extra = json.loads((PROY / rel).read_text(encoding='utf8'))
    CFG['espacios'].extend(extra.get('espacios', []) + extra.get('stands', []))
WEB = PROY / 'salida' / 'web'
WEB.mkdir(parents=True, exist_ok=True)
s = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
NIV = {n['id']: n for n in CFG['niveles']}

# 1) fuera camaras, luces y el calco del plano (el visor pone sus luces)
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.get('grupo') == 'calco':
        bpy.data.objects.remove(o, do_unlink=True)

# 2) textos -> mallas. Codigos de espacios: una malla por nivel; rotulos de edificios: uno a uno
dg.update()
codes = {}
for o in [o for o in bpy.data.objects if o.type == 'FONT']:
    is_code = o.name.startswith('Txt_')
    dg.update()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    g = o.get('grupo', 'base'); coll = o.users_collection[0]
    if is_code:
        me.transform(o.matrix_world)
        bm = codes.setdefault(g, (bmesh.new(), coll, o.parent, o.data.materials[0]))[0]
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    else:
        n = bpy.data.objects.new(o.name + '_m', me); coll.objects.link(n)
        n.parent = o.parent; n.matrix_parent_inverse = o.matrix_parent_inverse.copy(); n.matrix_basis = o.matrix_basis.copy()
        n['grupo'] = g
    bpy.data.objects.remove(o, do_unlink=True)
for g, (bm, coll, parent, m) in codes.items():
    me = bpy.data.meshes.new('Codigos_' + g); bm.to_mesh(me); bm.free(); me.materials.append(m)
    n = bpy.data.objects.new('Codigos_' + g, me); coll.objects.link(n); n.parent = parent; n['grupo'] = g
    if parent:                                   # la malla ya esta en coordenadas de mundo
        n.matrix_parent_inverse = parent.matrix_world.inverted()

# 3) niveles en su sitio (sin separar) y exportacion
for o in bpy.data.objects:
    if o.name.startswith('RAIZ_'):
        o.location.z = 0.0
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = False
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
bpy.ops.export_scene.gltf(
    filepath=str(WEB / 'mapa.glb'), export_format='GLB', export_extras=True, export_cameras=False, export_lights=False,
    export_apply=True, export_yup=True, export_image_format='AUTO', export_animations=False,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=16, export_draco_normal_quantization=10, export_draco_texcoord_quantization=16)


# 4) datos del visor
def z_nivel(nid):
    return float(NIV.get(nid, {}).get('z', 0))


def centroid(p):
    return sum(a for a, _ in p) / len(p), sum(b for _, b in p) / len(p)


def clave(codigo):
    """Codigo normalizado para buscar y cruzar con una base de datos: letras + numero sin ceros + sufijo (A 05 -> A5)."""
    c = re.sub(r'[^A-Z0-9]', '', str(codigo or '').upper())
    m = re.match(r'^([A-Z]*)0*(\d+)([A-Z]*)$', c)
    return f'{m[1]}{int(m[2])}{m[3]}' if m else c


lugares = []
for i, p in enumerate(CFG.get('pines', []), 1):
    g = p.get('nivel', 'base'); pos = list(p['pos']) + [2.0] * (3 - len(p['pos']))
    lugares.append({'n': p.get('n', i), 'nombre': p['nombre'], 'detalle': p.get('detalle', ''),
                    'color': p.get('color', [.85, .2, .25]), 'nivel': NIV.get(g, {}).get('nombre', g), 'grupo': g,
                    'pos': [round(pos[0], 2), round(pos[1], 2), round(z_nivel(g) + pos[2], 2)]})
espacios, vistos = [], set()
for st in CFG.get('espacios', []):
    if not st.get('codigo') or clave(st['codigo']) in vistos:
        continue
    vistos.add(clave(st['codigo']))
    g = st.get('nivel', 'base'); c = centroid(st['poligono'])
    espacios.append({'codigo': str(st['codigo']), 'key': clave(st['codigo']), 'grupo': g, 'categoria': st.get('categoria', ''),
                     'nivel': NIV.get(g, {}).get('nombre', g), 'nombre': st.get('nombre', ''), 'detalle': st.get('detalle', ''),
                     'pos': [round(c[0], 2), round(c[1], 2), round(z_nivel(g) + float(st.get('z', 0)) + float(st.get('altura', 2.4)), 2)]})
mc = CFG.get('marca', CFG.get('evento', {}))
datos = {
    'meta': {'titulo': mc.get('titulo', CFG.get('nombre', 'Mapa 3D')), 'subtitulo': mc.get('subtitulo', ''),
             'nota': mc.get('nota', 'Escala según plano. Alturas y entorno aproximados.'),
             'lugares': mc.get('etiqueta_lugares', mc.get('titulo_lista', 'Lugares')),
             'espacios': mc.get('etiqueta_espacios', 'Espacios'),
             'color': mc.get('color', '#e11d2a'), 'logo': pathlib.Path(mc['logo']).name if mc.get('logo') else ''},
    'centro': list(s.get('CENTRO', (0, 0))), 'radio': float(s.get('RADIO', 200)),
    'z_min': min([z_nivel(n) for n in NIV] + [0]) - .5,
    'niveles': [{'id': n['id'], 'nombre': n.get('nombre', n['id']), 'separacion': float(n.get('separacion', 0)),
                 'bajo_techo': bool(n.get('bajo_techo', False))} for n in CFG['niveles']],
    'lift': {n['id']: float(n['separacion']) for n in CFG['niveles'] if n.get('separacion', 0) > 0},
    'raices': {n['id']: 'RAIZ_' + n['id'] for n in CFG['niveles'] if n.get('separacion', 0) > 0},
    'lugares': lugares, 'espacios': espacios,
}
(WEB / 'datos.json').write_text(json.dumps(datos, ensure_ascii=False), encoding='utf8')

# 5) plantilla del visor + logo + sello de version (salta la cache del navegador)
V = KIT / 'visor'
for f in ('index.html', 'app.js', 'estilos.css'):
    shutil.copy2(V / f, WEB / f)
shutil.copytree(V / 'draco', WEB / 'draco', dirs_exist_ok=True)
if mc.get('logo'):
    shutil.copy2(PROY / mc['logo'], WEB / datos['meta']['logo'])
ver = str(int(time.time()))
for f in ('index.html', 'app.js'):
    p = WEB / f; t = p.read_text(encoding='utf8')
    t = re.sub(r"const VER = '\d+';", f"const VER = '{ver}';", t)
    t = re.sub(r'(app\.js|estilos\.css)\?v=\d+', lambda m: f'{m[1]}?v={ver}', t)
    t = t.replace('__TITULO__', datos['meta']['titulo']).replace('__SUBTITULO__', datos['meta']['subtitulo'])
    t = t.replace('__COLOR__', datos['meta']['color'])
    p.write_text(t, encoding='utf8')
css = WEB / 'estilos.css'
css.write_text(re.sub(r'--acento: #[0-9a-fA-F]{3,8};', f"--acento: {datos['meta']['color']};", css.read_text(encoding='utf8')), encoding='utf8')
mb = (WEB / 'mapa.glb').stat().st_size / 1e6
print(f'EXPORT OK {WEB} - {tris} triangulos - {mb:.2f} MB - {len(lugares)} lugares - {len(espacios)} espacios')
if mb > 12:
    print('AVISO: el GLB pasa de 12 MB; en celular con datos tardara. Ver docs/PROBLEMAS.md (peso del modelo).')
