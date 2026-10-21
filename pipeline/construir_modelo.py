"""Construye el modelo 3D de un recinto en Blender a partir de recinto.json (1 unidad = 1 metro).

Uso:
  python pipeline/generar_texturas.py                                   # una sola vez
  blender -b --factory-startup --python pipeline/construir_modelo.py -- proyectos/<recinto>/recinto.json

Salida: proyectos/<recinto>/salida/modelo.blend

Mundo: +X Este, +Y Norte, Z arriba. Formato del JSON: docs/FORMATO-RECINTO.md.

Grupos (propiedad `grupo` de cada objeto, la usan el exportador y el visor):
  <nivel>        piso, muros bajos, stands, mobiliario del nivel. Se ve en los dos modos.
  techo_<nivel>  cubiertas y muros altos. El visor los oculta en el modo "Por niveles" para ver adentro.
  entorno        terreno, vias, arboles. Siempre visible.
Cada nivel con "separacion" > 0 cuelga de un vacio RAIZ_<nivel>; el visor lo sube esa cantidad de metros
en el modo "Por niveles" para que se vea lo que hay debajo.
"""
import bpy, bmesh, json, math, random, sys, pathlib
import numpy as np

KIT = pathlib.Path(__file__).resolve().parent.parent
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not argv:
    raise SystemExit('Falta la ruta de recinto.json:  blender -b --factory-startup --python pipeline/construir_modelo.py -- proyectos/x/recinto.json')
CFG_PATH = pathlib.Path(argv[0]).resolve()
CFG = json.loads(CFG_PATH.read_text(encoding='utf8'))
PROY = CFG_PATH.parent
OUT = PROY / 'salida'
OUT.mkdir(exist_ok=True)
TEX = KIT / 'texturas'
if not (TEX / 'concreto.jpg').exists():
    raise SystemExit('No hay texturas. Corre primero:  python pipeline/generar_texturas.py')
random.seed(CFG.get('semilla', 2026))

# stands extraidos del plano (pipeline/extraer_plano.py) que se suman a los escritos a mano
for rel in ([CFG['stands_desde']] if isinstance(CFG.get('stands_desde'), str) else CFG.get('stands_desde', [])):
    extra = json.loads((PROY / rel).read_text(encoding='utf8'))
    for k in ('stands', 'objetos', 'zonas'):
        CFG.setdefault(k, []).extend(extra.get(k, []))

NIV = {n['id']: n for n in CFG['niveles']}
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = CFG.get('id', 'recinto')
scene.unit_settings.system = 'METRIC'

# ---------------------------------------------------------------- colecciones y raices de nivel
COLL = {}


def coll(g):
    if g not in COLL:
        COLL[g] = bpy.data.collections.new(g)
        scene.collection.children.link(COLL[g])
    return COLL[g]


ROOT = {}
for n in CFG['niveles']:
    if n.get('separacion', 0) > 0:
        e = bpy.data.objects.new('RAIZ_' + n['id'], None)
        coll(n['id']).objects.link(e)
        e['grupo'] = n['id']
        ROOT[n['id']] = e
        scene['LIFT_' + n['id']] = float(n['separacion'])


def nivel_de_grupo(g):
    return g[6:] if g.startswith('techo_') else g


# ---------------------------------------------------------------- materiales
MATS, TILE, _IMG = {}, {}, {}


def bsdf(m):
    """Nodo Principled por tipo: el nombre del nodo cambia con el idioma de Blender."""
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def mat(name, col, rough=.75, metal=0., emit=None, alpha=1., strength=1.):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = bsdf(m)
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = strength
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*col, alpha)
    MATS[name] = m
    return m


def img(file, data=False):
    if file not in _IMG:
        im = bpy.data.images.load(str(TEX / (file + '.jpg')))
        if data:
            im.colorspace_settings.name = 'Non-Color'
        _IMG[file] = im
    return _IMG[file]


def tex_mat(name, file, tile, rough=.8, metal=0., normal=None, nstr=1.0, avg=(.6, .6, .6), tint=None):
    """Material PBR con textura repetida cada `tile` metros (exporta bien a glTF). `tint` multiplica el color."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = bsdf(m); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(file)
    if tint:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(t.outputs['Color'], mix.inputs['A']); mix.inputs['B'].default_value = (*tint, 1)
        nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    else:
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if normal:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img(normal, True)
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr
        nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (*(tint or avg), 1)
    MATS[name] = m; TILE[name] = tile
    return m


def led_mat(name, file, strength=2.2):
    """Pantalla LED: la textura va como emision, una vez por cara (sin repetir)."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = bsdf(m); b.inputs['Roughness'].default_value = .25
    b.inputs['Base Color'].default_value = (.02, .02, .03, 1)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(file); t.extension = 'EXTEND'
    nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = strength
    m.diffuse_color = (.35, .2, .8, 1)
    MATS[name] = m; TILE[name] = 1.0
    return m


# materiales por nombre que se pueden pedir desde recinto.json ("piso", "material", "fachada")
CATALOGO = {
    'concreto': lambda: tex_mat('concreto', 'concreto', 4.8, .8, avg=(.74, .73, .70)),
    'concreto_pulido': lambda: tex_mat('concreto_pulido', 'concreto_pulido', 6, .35, .05, avg=(.60, .60, .60)),
    'piedra_pulida': lambda: tex_mat('piedra_pulida', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50)),
    'alfombra': lambda: tex_mat('alfombra', 'alfombra', 3, .95, avg=(.42, .46, .52)),
    'madera': lambda: tex_mat('madera', 'madera', 2, .5, .35, avg=(.17, .12, .09)),
    'madera_clara': lambda: tex_mat('madera_clara', 'madera_clara', 3, .6, avg=(.70, .55, .35)),
    'pav_plaza': lambda: tex_mat('pav_plaza', 'pav_plaza', 4.8, .8, normal='pav_plaza_n', nstr=.6, avg=(.78, .72, .61)),
    'pav_arenisca': lambda: tex_mat('pav_arenisca', 'pav_arenisca', 4.8, .85, normal='pav_arenisca_n', nstr=.6, avg=(.74, .67, .55)),
    'pav_oscuro': lambda: tex_mat('pav_oscuro', 'pav_oscuro', 4.8, .85, avg=(.60, .54, .45)),
    'cesped': lambda: tex_mat('cesped', 'cesped', 9, .95, avg=(.30, .50, .16)),
    'asfalto': lambda: tex_mat('asfalto', 'asfalto', 7, .9, normal='asfalto_n', nstr=.5, avg=(.22, .23, .25)),
    'agua': lambda: tex_mat('agua', 'agua', 22, .08, 0, normal='agua_n', nstr=.8, avg=(.15, .40, .46)),
    'arenisca_muro': lambda: tex_mat('arenisca_muro', 'arenisca_muro', 4.8, .85, normal='arenisca_muro_n', nstr=.7, avg=(.76, .68, .54)),
    'ladrillo': lambda: tex_mat('ladrillo', 'ladrillo', 2.0, .85, normal='ladrillo_n', nstr=.8, avg=(.60, .29, .17)),
    'vidrio': lambda: mat('vidrio', (.55, .70, .78), .05, 0, None, .35),
    'blanco': lambda: mat('blanco', (.95, .95, .94), .5),
    'negro': lambda: mat('negro', (.06, .06, .07), .5),
}


def material(nombre, defecto='concreto'):
    nombre = nombre or defecto
    if isinstance(nombre, list):                      # color directo [r, g, b] (lineal 0..1)
        return mat('color_%.2f_%.2f_%.2f' % tuple(nombre), tuple(nombre), .65)
    if nombre not in CATALOGO:
        raise SystemExit(f'Material desconocido "{nombre}". Opciones: {", ".join(sorted(CATALOGO))} o un color [r, g, b].')
    return CATALOGO[nombre]()


M = {
    'stand_lado': mat('stand_panel', (.96, .95, .93), .6), 'silla': mat('silla', (.18, .19, .21), .6),
    'tarima': mat('tarima', (.08, .08, .09), .5), 'faldon': mat('faldon_tarima', (.04, .04, .05), .9),
    'tronco': mat('tronco', (.32, .22, .14), .9), 'copa': tex_mat('copa', 'follaje', 3.0, .9, avg=(.20, .45, .12)),
    'lona': mat('lona_carpa', (.96, .95, .92), .7), 'alu': mat('truss_aluminio', (.78, .80, .82), .3, .9),
    'rotulo': mat('rotulo', (.08, .08, .10), .6), 'rotulo_claro': mat('rotulo_claro', (.97, .97, .97), .6),
    'led': led_mat('pantalla_led', 'led_wide'),
}


def color_pab(c):
    """Fachada de panel y cubierta metalica tenidas con el color del edificio."""
    k = '%.2f_%.2f_%.2f' % tuple(c)
    return (tex_mat('muro_' + k, 'panel_gris', 4.8, .55, .25, normal='panel_n', nstr=.5, tint=tuple(min(1, v * 1.25) for v in c)),
            tex_mat('techo_' + k, 'techo_gris', 3.6, .4, .45, normal='techo_n', tint=tuple(min(1, v * 1.25) for v in c)))


# ---------------------------------------------------------------- geometria
def area(p):
    return .5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def ccw(p):
    return list(p) if area(p) > 0 else list(reversed(p))


def centroid(p):
    return sum(a for a, _ in p) / len(p), sum(b for _, b in p) / len(p)


class MB:
    """Acumula geometria en una sola malla (pocas mallas = pocas llamadas de dibujo en el celular)."""

    def __init__(s):
        s.v, s.f, s.m, s.mats, s.sm, s.uvs = [], [], [], [], [], {}

    def mi(s, m):
        if m not in s.mats:
            s.mats.append(m)
        return s.mats.index(m)

    def prism(s, poly, z0, h, m, top=None, side=None):
        poly = ccw(poly); n = len(poly); b = len(s.v)
        s.v += [(x, y, z0) for x, y in poly] + [(x, y, z0 + h) for x, y in poly]
        s.f.append(tuple(b + i for i in reversed(range(n)))); s.m.append(s.mi(m))
        s.f.append(tuple(b + n + i for i in range(n))); s.m.append(s.mi(top or m))
        for i in range(n):
            j = (i + 1) % n
            s.f.append((b + i, b + j, b + n + j, b + n + i)); s.m.append(s.mi(side or m))
        s.sm += [False] * (n + 2)

    def box(s, c, size, m, rz=0., top=None, side=None):
        hx, hy = size[0] / 2, size[1] / 2; co, si = math.cos(rz), math.sin(rz)
        s.prism([(c[0] + x * co - y * si, c[1] + x * si + y * co) for x, y in [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]],
                c[2], size[2], m, top, side)

    def seg(s, a, b, w, z0, h, m, top=None):
        L = math.dist(a, b)
        if L < 1e-3:
            return
        s.box(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z0), (L + w * .98, w, h), m, math.atan2(b[1] - a[1], b[0] - a[0]), top)

    def walls(s, poly, z0, h, t, m, gaps=None):
        """Muros por el contorno. gaps = {indice_lado: [(desde_m, hasta_m), ...]} deja vanos (puertas)."""
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            L = math.dist(a, b)
            cuts = sorted((gaps or {}).get(i, []))
            t0 = 0.0
            for g0, g1 in cuts + [(L, L)]:
                if g0 > t0 + .05:
                    s.seg(lerp(a, b, t0 / L), lerp(a, b, g0 / L), t, z0, h, m)
                t0 = max(t0, g1)

    def led(s, c, ancho, alto, z0, rz, grosor=.3):
        """Pantalla con contenido LED en la cara que mira hacia rz + 90 grados."""
        s.box((c[0], c[1], z0), (ancho, grosor, alto), M['tarima'], rz)
        co, si = math.cos(rz), math.sin(rz); nx, ny = -si, co
        b = len(s.v); hx = ancho / 2; off = grosor / 2 + .02
        for x, z in ((-hx, z0), (hx, z0), (hx, z0 + alto), (-hx, z0 + alto)):
            s.v.append((c[0] + x * co + nx * off, c[1] + x * si + ny * off, z))
        s.f.append((b, b + 1, b + 2, b + 3)); s.m.append(s.mi(M['led'])); s.sm.append(False)
        s.uvs[len(s.f) - 1] = [(1, 0), (0, 0), (0, 1), (1, 1)]

    def raw(s, verts, faces, m, off=(0, 0, 0), sc=(1, 1, 1), smooth=False):
        b = len(s.v)
        s.v += [(off[0] + x * sc[0], off[1] + y * sc[1], off[2] + z * sc[2]) for x, y, z in verts]
        for f in faces:
            s.f.append(tuple(b + i for i in f)); s.m.append(s.mi(m)); s.sm.append(smooth)

    def build(s, name, grupo):
        if not s.v:
            return None
        me = bpy.data.meshes.new(name); me.from_pydata(s.v, [], s.f)
        me.polygons.foreach_set('material_index', s.m)
        me.polygons.foreach_set('use_smooth', s.sm)
        for m in s.mats:
            me.materials.append(m)
        me.update()
        # UVs por proyeccion de caja, en metros / tamano de baldosa del material
        nl, npo = len(me.loops), len(me.polygons)
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        li = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', li)
        nrm = np.empty(npo * 3, np.float32); me.polygons.foreach_get('normal', nrm); nrm = np.abs(nrm.reshape(-1, 3))
        tot = np.empty(npo, np.int32); me.polygons.foreach_get('loop_total', tot)
        tile = np.array([TILE.get(m.name, 4.0) for m in s.mats], np.float32)[np.array(s.m, np.int32)]
        pn = np.repeat(nrm, tot, axis=0); pt = np.repeat(tile, tot); P = co[li]
        horiz = pn[:, 2] > .7; alongx = pn[:, 1] >= pn[:, 0]
        u = np.where(horiz | alongx, P[:, 0], P[:, 1]); v = np.where(horiz, P[:, 1], P[:, 2])
        uvarr = np.column_stack((u / pt, v / pt)).astype(np.float32)
        for fi, quad in s.uvs.items():
            ls = me.polygons[fi].loop_start
            for k, (uu, vv) in enumerate(quad):
                uvarr[ls + k] = (uu, vv)
        me.uv_layers.new(name='UVMap').data.foreach_set('uv', uvarr.ravel())
        return link(bpy.data.objects.new(name, me), grupo)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def link(ob, grupo):
    coll(grupo).objects.link(ob)
    ob['grupo'] = grupo
    root = ROOT.get(nivel_de_grupo(grupo))
    if root:
        ob.parent = root
    return ob


def texto(cuerpo, pos, z, tam, m, grupo, rz=0.0, nombre=None, extrude=0.0):
    cu = bpy.data.curves.new(nombre or 'Rotulo', 'FONT'); cu.body = cuerpo
    cu.size = tam; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = extrude
    ob = bpy.data.objects.new(nombre or ('Rotulo_' + cuerpo[:20]), cu)
    ob.location = (pos[0], pos[1], z + .03); ob.rotation_euler = (0, 0, rz)
    cu.materials.append(m)
    return link(ob, grupo)


def z_nivel(nid):
    return float(NIV[nid].get('z', 0)) if nid in NIV else 0.0


# ---------------------------------------------------------------- terreno
pts = [p for e in CFG.get('edificios', []) for p in e['poligono']] + [p for z in CFG.get('zonas', []) for p in z['poligono']]
if not pts:
    raise SystemExit('recinto.json no tiene edificios ni zonas.')
xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
T = CFG.get('terreno', {})
mg = float(T.get('margen', 80))
x0, x1, y0, y1 = min(xs) - mg, max(xs) + mg, min(ys) - mg, max(ys) + mg
zt = min(z_nivel(n) for n in NIV) - .05 if T.get('bajo_todo') else -.05
mb = MB()
mb.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], zt - .3, .3, material(T.get('material', 'concreto')))
for v in T.get('vias', []):                           # [[x, y], [x, y], ancho]
    mb.seg(v[0], v[1], v[2], zt, .04, material('asfalto'))
mb.build('Terreno', 'entorno')

# ---------------------------------------------------------------- zonas planas (plazas, jardines, tapetes, agua)
for z in CFG.get('zonas', []):
    g = z.get('nivel', 'base'); h = float(z.get('alto', .06))
    mb = MB(); mb.prism(z['poligono'], z_nivel(g) + float(z.get('z', 0)), h, material(z.get('material'), 'pav_plaza'))
    mb.build('Zona_' + z.get('id', 'x'), g)
    if z.get('rotulo'):
        c = centroid(z['poligono'])
        texto(z['rotulo'], c, z_nivel(g) + h, float(z.get('tam_rotulo', 2.4)), M['rotulo'], g, math.radians(z.get('rot_rotulo', 0)))

# ---------------------------------------------------------------- edificios
for e in CFG.get('edificios', []):
    g = e.get('nivel', 'base'); z0 = z_nivel(g) + float(e.get('z', 0)); H = float(e['altura'])
    poly = ccw(e['poligono'])
    col = tuple(e.get('color', (.6, .6, .62)))
    muro_m, techo_m = color_pab(col)
    if e.get('fachada') and e['fachada'] != 'panel':
        muro_m = material(e['fachada'])
    piso_m = material(e.get('piso'), 'concreto_pulido')
    bajo = min(H, float(e.get('muro_bajo', 3.2)))
    t = float(e.get('grosor_muro', .4))
    # vanos de puertas: lados contados desde el primer vertice del poligono ya en sentido antihorario
    gaps = {}
    for p in e.get('puertas', []):
        gaps.setdefault(int(p['lado']), []).append((p['centro'] - p['ancho'] / 2, p['centro'] + p['ancho'] / 2))
    mb = MB()
    mb.prism(poly, z0, .12, piso_m)                                  # losa de piso
    mb.walls(poly, z0, bajo, t, muro_m, gaps)                        # muro bajo: se ve en "Por niveles"
    mb.build('Edif_' + e['id'], g)
    if e.get('cubierta', True) and H > bajo:
        mb = MB()
        mb.walls(poly, z0 + bajo, H - bajo, t, muro_m)               # muro alto
        mb.prism(poly, z0 + H, .25, techo_m)                         # cubierta
        mb.build('Techo_' + e['id'], 'techo_' + g)
    if e.get('rotulo', True):
        c = centroid(poly); rz = math.radians(e.get('rot_rotulo', 0)); tam = float(e.get('tam_rotulo', 3.5))
        texto(e['nombre'], c, z0 + .12, tam, M['rotulo'], g, rz, 'Rotulo_piso_' + e['id'])
        if e.get('cubierta', True):
            texto(e['nombre'], c, z0 + H + .25, tam * 1.6, M['rotulo_claro'], 'techo_' + g, rz, 'Rotulo_techo_' + e['id'])

# ---------------------------------------------------------------- stands
por_nivel = {}
for s in CFG.get('stands', []):
    por_nivel.setdefault(s.get('nivel', 'base'), []).append(s)
for g, lista in por_nivel.items():
    mb = MB()
    for s in lista:
        z0 = z_nivel(g) + float(s.get('z', 0)); h = float(s.get('altura', 2.4))
        top = mat('stand_%.2f_%.2f_%.2f' % tuple(s['color']), tuple(s['color']), .55) if s.get('color') else mat('stand_tapa', (.92, .55, .58), .55)
        mb.prism(s['poligono'], z0, h, M['stand_lado'], top=top)
        if s.get('codigo'):
            c = centroid(s['poligono'])
            ancho = min(abs(area(s['poligono'])) ** .5, 6)
            texto(s['codigo'], c, z0 + h, max(.5, ancho * .28), M['rotulo'], g, math.radians(s.get('rot_rotulo', 0)), 'Txt_' + s['codigo'])
    mb.build('Stands_' + g, g)

# ---------------------------------------------------------------- objetos (tarimas, pantallas, sillas, carpas, arboles, cajas)
ICO = None


def ico():
    global ICO
    if ICO is None:
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        ICO = ([tuple(x.co) for x in bm.verts], [tuple(x.index for x in p.verts) for p in bm.faces]); bm.free()
    return ICO


def cyl(n=8):
    v = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), z) for z in (0, 1) for i in range(n)]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return v, f


por_grupo = {}
for i, o in enumerate(CFG.get('objetos', [])):
    g = o.get('nivel', 'base'); z0 = z_nivel(g) + float(o.get('z', 0))
    mb = por_grupo.setdefault(g, MB())
    rz = math.radians(o.get('rot', 0)); tipo = o['tipo']
    if tipo == 'tarima':
        c = o['centro']; w, d, h = o['ancho'], o['fondo'], o.get('alto', .6)
        mb.box((c[0], c[1], z0), (w, d, h), M['tarima'], rz, side=M['faldon'])
        if o.get('pantalla'):
            p = o['pantalla']; co, si = math.cos(rz), math.sin(rz)
            back = (c[0] - (-si) * (d / 2 + .4), c[1] - co * (d / 2 + .4))      # al fondo de la tarima
            mb.led(back, p['ancho'], p['alto'], z0 + h + float(p.get('base', .8)), rz)
    elif tipo == 'pantalla':
        mb.led(o['centro'], o['ancho'], o['alto'], z0 + float(o.get('base', 2)), rz)
    elif tipo == 'sillas':
        (ax, ay), (bx, by) = o['area']; px, py = o.get('paso', (.6, 1.0))
        co, si = math.cos(rz), math.sin(rz); cx, cy = (ax + bx) / 2, (ay + by) / 2
        nx = max(1, int(abs(bx - ax) / px)); ny = max(1, int(abs(by - ay) / py))
        for ix in range(nx):
            for iy in range(ny):
                lx = -abs(bx - ax) / 2 + (ix + .5) * px; ly = -abs(by - ay) / 2 + (iy + .5) * py
                mb.box((cx + lx * co - ly * si, cy + lx * si + ly * co, z0), (.45, .45, .85), M['silla'], rz)
    elif tipo == 'sillas_puntos':                          # sillas extraidas del plano: [x, y, rotacion_grados]
        for x, y, r in o['puntos']:
            mb.box((x, y, z0), (.45, .45, .85), M['silla'], math.radians(r))
    elif tipo == 'carpa':
        c = o['centro']; w, d, h = o['ancho'], o['fondo'], o.get('alto', 5)
        mb.box((c[0], c[1], z0 + h - .3), (w, d, .3), M['lona'], rz)
        co, si = math.cos(rz), math.sin(rz)
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx, ly = sx * (w / 2 - .2), sy * (d / 2 - .2)
                mb.box((c[0] + lx * co - ly * si, c[1] + lx * si + ly * co, z0), (.3, .3, h), M['alu'], rz)
    elif tipo == 'arbol':
        v, f = ico(); cv, cf = cyl()
        for x, y in o['puntos']:
            s_ = random.uniform(.85, 1.25) * float(o.get('escala', 1))
            mb.raw(cv, cf, M['tronco'], (x, y, z0), (.18 * s_, .18 * s_, 2.6 * s_))
            mb.raw(v, f, M['copa'], (x, y, z0 + 3.6 * s_), (2.0 * s_, 2.0 * s_, 1.7 * s_), smooth=True)
    elif tipo == 'caja':
        c = o['centro']; w, d, h = o['tam']
        m = material(o.get('material') or o.get('color'), 'blanco')
        mb.box((c[0], c[1], z0), (w, d, h), m, rz)
    else:
        raise SystemExit(f'Objeto {i}: tipo desconocido "{tipo}" (tarima, pantalla, sillas, sillas_puntos, carpa, arbol, caja).')
    if o.get('rotulo'):
        c = o.get('centro') or centroid(o['area'] if 'area' in o else o['puntos'])
        texto(o['rotulo'], c, z0 + float(o.get('alto', .6)), 1.2, M['rotulo'], g, rz)
for g, mb in por_grupo.items():
    mb.build('Objetos_' + g, g)

# ---------------------------------------------------------------- luz y camara de estudio (solo para abrir el .blend y para renders)
sol = bpy.data.objects.new('Sol', bpy.data.lights.new('Sol', 'SUN'))
sol.data.energy = 3.5; sol.rotation_euler = (math.radians(50), 0, math.radians(35)); coll('entorno').objects.link(sol)
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
scene['CENTRO'] = (cx, cy)
scene['RADIO'] = max(x1 - x0, y1 - y0) / 2
cam = bpy.data.objects.new('Cam_Iso', bpy.data.cameras.new('Cam_Iso'))
cam.data.lens = 40; coll('entorno').objects.link(cam); scene.camera = cam
d = scene['RADIO'] * 2.4
cam.location = (cx + d * .55, cy - d * .75, d * .65)
cam.rotation_euler = (math.radians(58), 0, math.radians(36))
world = bpy.data.worlds.new('Cielo'); world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs['Color'].default_value = (.62, .74, .88, 1)
scene.world = world

path = OUT / 'modelo.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print(f'MODELO OK {path} - {len(CFG.get("edificios", []))} edificios - {len(CFG.get("stands", []))} stands - {tris} triangulos')
