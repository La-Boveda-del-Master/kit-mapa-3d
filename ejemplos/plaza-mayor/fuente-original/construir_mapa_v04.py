"""Mapa 3D de Feria Effix 2026 en Plaza Mayor (v04: acabados con texturas, base del mapa web y del video) a escala 1 u = 1 m, organizado por NIVELES.

Uso: python generar_texturas.py ; blender -b --factory-startup --python construir_mapa_v04.py
Datos: plano_v03.json (extraer_plano_v03.py). Mundo: +X Este, +Y Norte, Z arriba.

Niveles
  Nivel principal (z 0): Amarillo, Blanco, Hall, Zona de Comidas, Plazoleta Interamericana, plaza de la Caja.
  Nivel superior (z +7.5): Pabellon Azul, Zona VIP y Pabellon Verde.
  Nivel inferior (z 0, debajo del superior): Pabellon Rojo (bajo el Azul) y Auditorio Comunidades (bajo el Verde).
  Convenciones: Gran Salon piso 1 (z -9, se baja por las gradas de la plazoleta), Salon Multiproposito piso 2
  (z -4.5, mas pequeno) y Caja de Madera piso 3 (z 0: portico de ingreso, registro y taquillas ADENTRO).
En modo mapa los niveles superiores FLOTAN sobre los inferiores (misma posicion en planta) para dejarlos ver.
Las alturas son aproximadas (el PDF no trae cortes); la planta sale del PDF tecnico (cuadricula = 1 m).
"""
import bpy, bmesh, json, math, random, pathlib
import numpy as np
from collections import defaultdict
from mathutils import Vector

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
D = json.loads((R / 'plano_v03.json').read_text(encoding='utf8'))
REF = json.loads((R / 'referencias' / 'referencias_bbox.json').read_text())
random.seed(2026)

Z_UP, H_LOW = 11.0, 10.5            # Rojo h libre 4.5 m (plano oficial) + entrepiso; el Azul (h 4.7) va encima
Z_GS, Z_MULTI = -9.0, -4.5
DZ_CONV = 4.5                       # el edificio de Convenciones se sube completo al final (Plazoleta = piso 2)
LIFT = {'sup': 34.0, 'multi': 16.5, 'caja': 30.0, 'shell': 52.0}   # separacion expositiva (modo mapa)
WALL_LOW = 3.2

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = 'Effix2026_PlazaMayor'
scene.unit_settings.system = 'METRIC'
FONT = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf')
FONT_REG = bpy.data.fonts.load('C:/Windows/Fonts/segoeui.ttf')

# ---------------------------------------------------------------- colecciones
CNAMES = {'ref': '00_Referencia_PDF', 'terreno': '01_Terreno', 'vias': '02_Vias', 'rio': '03_Rio',
          'base': '04_Nivel_principal', 'ext_base': '05_EXT_muros_y_techos', 'sup': '06_Nivel_superior_Azul_Verde',
          'ext_sup': '07_EXT_superior', 'inf': '08_Nivel_inferior_Rojo_Comunidades', 'gs': '09_Gran_Salon_piso1',
          'multi': '10_Salon_Multiproposito_piso2', 'caja': '11_Caja_Madera_piso3_registro', 'shell': '12_Caja_Madera_caparazon',
          'losa': '13_Plaza_sobre_Gran_Salon', 'mob': '14_Mobiliario', 'veg': '15_Vegetacion', 'veh': '16_Vehiculos',
          'entorno': '18_Entorno', 'pins_base': '19a_Pines_principal', 'pins_sup': '19b_Pines_superior',
          'pins_inf': '19c_Pines_inferior', 'pins_gs': '19d_Pines_Gran_Salon', 'pins_multi': '19e_Pines_Multiproposito',
          'pins_caja': '19f_Pines_Caja', 'ctx': '20_Rotulos_contexto', 'guias': '21_Guias_niveles', 'huella': '22_Huella_celosia_Caja'}
COLL = {}
for k, n in CNAMES.items():
    COLL[k] = bpy.data.collections.new(n)
    scene.collection.children.link(COLL[k])


def empty(name, loc=(0, 0, 0), c='base'):
    e = bpy.data.objects.new(name, None); e.location = loc
    COLL[c].objects.link(e)
    return e


ROOT = {'sup': empty('RAIZ_nivel_superior', c='sup'), 'multi': empty('RAIZ_multiproposito', c='multi'),
        'caja': empty('RAIZ_caja_piso3', c='caja'), 'shell': empty('RAIZ_caja_caparazon', c='shell')}
PARENT = {'sup': 'sup', 'ext_sup': 'sup', 'pins_sup': 'sup', 'multi': 'multi', 'pins_multi': 'multi',
          'caja': 'caja', 'pins_caja': 'caja', 'shell': 'shell', 'huella': 'caja'}
orient = empty('Orientacion_rotulos', c='ctx')

# ---------------------------------------------------------------- materiales
MATS = {}


def mat(name, col, rough=.75, metal=0., emit=None, alpha=1., strength=1.):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
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


TEX = R / 'texturas'
TILE = {}          # metros que cubre una repeticion de la textura de cada material
_IMG = {}


def img(file, data=False):
    if file not in _IMG:
        im = bpy.data.images.load(str(TEX / (file + '.jpg')))
        if data:
            im.colorspace_settings.name = 'Non-Color'
        _IMG[file] = im
    return _IMG[file]


def tex_mat(name, file, tile, rough=.8, metal=0., normal=None, nstr=1.0, avg=(.6, .6, .6)):
    """Material PBR con textura de color (y normales) repetida cada `tile` metros; exporta bien a glTF."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(file)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if normal:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img(normal, True)
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr
        nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (*avg, 1)
    MATS[name] = m; TILE[name] = tile
    return m


def led_mat(name, file, strength=2.2):
    # Pantalla LED: textura de contenido como emision (UV 0..1 por cara, sin repetir)
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = .25
    b.inputs['Base Color'].default_value = (.02, .02, .03, 1)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(file); t.extension = 'EXTEND'
    nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = strength
    m.diffuse_color = (.35, .2, .8, 1)
    MATS[name] = m; TILE[name] = 1.0
    return m


def noise_mat(name, c1, c2, scale=40., rough=.8):
    m = mat(name, c1, rough); nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = scale; tex.inputs['Detail'].default_value = 3
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], tex.inputs['Vector']); nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return m


def tiles_mat(name, c1, c2, size=1.0):
    m = mat(name, c1, .85); nt = m.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1)
    br.inputs['Mortar'].default_value = (c1[0] * .82, c1[1] * .82, c1[2] * .82, 1)
    br.inputs['Scale'].default_value = 1 / size; br.inputs['Mortar Size'].default_value = .012
    br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = .5
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return m


M = {
    'suelo': tex_mat('suelo_ciudad', 'concreto', 14, .9, avg=(.6, .6, .58)),
    'pav': tex_mat('pavimento_arenisca', 'pav_arenisca', 4.8, .85, normal='pav_arenisca_n', nstr=.6, avg=(.74, .67, .55)),
    'pav_plaza': tex_mat('pavimento_plaza', 'pav_plaza', 4.8, .8, normal='pav_plaza_n', nstr=.6, avg=(.78, .72, .61)),
    'pav_osc': tex_mat('pavimento_franja', 'pav_oscuro', 4.8, .85, avg=(.60, .54, .45)),
    'cesped': tex_mat('cesped', 'cesped', 9, .95, avg=(.30, .50, .16)),
    'asfalto': tex_mat('asfalto', 'asfalto', 7, .9, normal='asfalto_n', nstr=.5, avg=(.22, .23, .25)),
    'asfalto_brt': tex_mat('asfalto_metroplus', 'asfalto_brt', 7, .9, avg=(.44, .42, .40)),
    'linea': mat('linea_vial', (.95, .95, .92), .6), 'linea_am': mat('linea_amarilla', (.95, .75, .10), .6),
    'agua': tex_mat('agua_rio', 'agua', 22, .08, 0, normal='agua_n', nstr=.8, avg=(.15, .40, .46)), 'talud': mat('talud_rio', (.45, .48, .30), .9),
    'concreto': tex_mat('concreto', 'concreto', 4.8, .8, avg=(.74, .73, .70)), 'concreto_osc': mat('concreto_oscuro', (.45, .45, .44), .8),
    'arenisca': tex_mat('arenisca_muro', 'arenisca_muro', 4.8, .85, normal='arenisca_muro_n', nstr=.7, avg=(.76, .68, .54)),
    'tronco': mat('tronco', (.32, .22, .14), .9),
    'copa1': tex_mat('copa_1', 'follaje', 3.0, .9, avg=(.20, .45, .12)), 'copa2': tex_mat('copa_2', 'follaje', 2.2, .9, avg=(.27, .52, .14)),
    'copa3': tex_mat('copa_3', 'follaje', 4.0, .9, avg=(.16, .38, .12)), 'palma': mat('copa_palma', (.25, .48, .14), .85),
    'vidrio': mat('vidrio', (.55, .70, .78), .05, 0, None, .35), 'vidrio_brt': mat('vidrio_estacion', (.70, .85, .90), .05, 0, None, .4),
    'ladrillo': tex_mat('ladrillo_teatro', 'ladrillo', 2.0, .85, normal='ladrillo_n', nstr=.8, avg=(.60, .29, .17)),
    'techo_gris': tex_mat('techo_metalico', 'techo_gris', 3.6, .4, .5, normal='techo_n', avg=(.62, .64, .66)),
    'arco': mat('estructura_flotante_verde', (.70, .82, .62), .4, .3), 'poste': mat('poste_blanco', (.92, .92, .90), .5),
    'stand_lado': mat('stand_panel', (.96, .95, .93), .6), 'silla': mat('silla', (.18, .19, .21), .6),
    'tarima': mat('tarima', (.08, .08, .09), .5), 'pantalla': mat('pantalla_led', (.05, .08, .12), .2, 0, (.35, .65, 1.0), 2.0),
    'faldon': mat('faldon_tarima', (.04, .04, .05), .9), 'luz_movil': mat('cabeza_movil', (.30, .18, .55), .35, .6),
    'vip': mat('piso_vip', (.24, .24, .26), .5), 'blanco': mat('blanco', (.98, .98, .98), .5), 'negro': mat('negro', (.06, .06, .07), .5),
    'carpa': mat('carpa_blanca', (.97, .97, .96), .6), 'carpa_roja': mat('carpa_roja', (.85, .18, .16), .6),
    'guia': mat('guia_punteada', (.15, .15, .15), .5), 'mesa': mat('mesa', (.55, .40, .28), .6),
    'ciudad1': tex_mat('edif_ciudad_1', 'fachada_1', 9, .8, avg=(.80, .78, .74)), 'ciudad2': tex_mat('edif_ciudad_2', 'fachada_2', 9, .8, avg=(.70, .67, .62)),
    'ciudad3': tex_mat('edif_ciudad_3', 'fachada_3', 9, .8, avg=(.64, .44, .34)), 'ciudad4': tex_mat('edif_ciudad_4', 'fachada_4', 9, .8, avg=(.84, .84, .82)),
    'azotea': mat('azotea', (.62, .61, .58), .9), 'rueda': mat('rueda', (.05, .05, .06), .8),
    'ventana': mat('ventanas', (.30, .38, .45), .2, .2), 'alu': mat('truss_aluminio', (.78, .80, .82), .3, .9),
    'lona': mat('lona_carpa', (.96, .95, .92), .7), 'acero': mat('acero_columnas', (.82, .84, .86), .3, .8),
    'efx_r': mat('effix_rojo', (.86, .06, .10), .45), 'efx_n': mat('effix_negro', (.05, .05, .06), .5),
    'escalera': mat('escalera_electrica', (.30, .31, .33), .35, .6),
}
PAV = {'Amarillo': ((.96, .70, .06), (.98, .93, .70), (.98, .80, .25)), 'Blanco': ((.90, .91, .92), (.95, .95, .95), (.94, .56, .60)),
       'Azul': ((.08, .38, .82), (.82, .90, .98), (.30, .58, .95)), 'Rojo': ((.78, .10, .08), (.97, .85, .83), (.92, .35, .32)),
       'Verde': ((.40, .68, .16), (.86, .94, .78), (.55, .80, .30)), 'Hall': ((.78, .76, .74), (.95, .86, .93), (.80, .40, .66)),
       'GS': ((.62, .56, .48), (.93, .89, .82), (.70, .55, .40)), 'Caja': ((.24, .12, .06), (.83, .74, .60), (.60, .40, .25)),
       'Multi': ((.70, .56, .25), (.94, .90, .80), (.80, .62, .28)), 'Com': ((.22, .45, .14), (.80, .88, .74), (.45, .70, .30)),
       'Plaza': ((.8, .8, .8), (.9, .9, .9), (.92, .33, .30))}
TINTE = {'Amarillo': 'amarillo', 'Blanco': 'blanco', 'Azul': 'azul', 'Verde': 'verde', 'Rojo': 'rojo', 'Hall': 'hall', 'GS': 'gs', 'Multi': 'multi'}
for k, (c, f, s) in PAV.items():
    if k in TINTE:      # fachada de panel metalico nervado y cubierta de junta alzada, en el color del pabellon
        tex_mat('muro_' + k, 'panel_' + TINTE[k], 4.8, .55, .25, normal='panel_n', nstr=.5, avg=c)
        tex_mat('techo_' + k, 'techo_' + TINTE[k], 3.6, .4, .45, normal='techo_n', avg=c)
    else:
        mat('muro_' + k, c, .6)
    mat('piso_' + k, f, .7); mat('stand_' + k, s, .55)
tex_mat('muro_Verde_bajo', 'panel_verde_osc', 4.8, .6, .2, normal='panel_n', nstr=.5, avg=(.30, .52, .12))
tex_mat('madera_caja', 'madera', 2.0, .5, .35, avg=(.17, .12, .09))
# pisos interiores reales (recorrido 360): concreto pulido en pabellones, piedra pulida en lobbies, alfombra en Gran Salon y comisiones
for _k in ('Amarillo', 'Blanco', 'Azul', 'Rojo', 'Verde'):
    tex_mat('int_' + _k, 'concreto_pulido', 6, .35, .05, avg=(.60, .60, .60))
tex_mat('int_Hall', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50)); tex_mat('int_Caja', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50))
tex_mat('int_Multi', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50)); tex_mat('int_GS', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50))
tex_mat('alfombra_gs', 'alfombra', 3, .95, avg=(.42, .46, .52)); tex_mat('madera_clara', 'madera_clara', 3, .6, avg=(.70, .55, .35))
tex_mat('fachada_pab', 'fachada_pab', 12, .45, .1, avg=(.62, .64, .66))
tex_mat('solar', 'solar', 8, .25, .5, avg=(.10, .14, .26))

# ---------------------------------------------------------------- geometria


def area(p):
    return .5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def ccw(p):
    return list(p) if area(p) > 0 else list(reversed(p))


def pip(pt, poly):
    x, y = pt; ins = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            ins = not ins
    return ins


def bbox(p):
    xs = [a for a, _ in p]; ys = [b for _, b in p]
    return min(xs), min(ys), max(xs), max(ys)


def centroid(p):
    return sum(a for a, _ in p) / len(p), sum(b for _, b in p) / len(p)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


class MB:
    """Acumula geometria en una sola malla."""

    def __init__(s):
        s.v, s.f, s.m, s.mats, s.sm = [], [], [], [], []

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

    def walls(s, poly, z0, h, t, m, top=None, skip=()):
        n = len(poly)
        for i in range(n):
            if i not in skip:
                s.seg(poly[i], poly[(i + 1) % n], t, z0, h, m, top)

    def dashed(s, a, b, z0, h, w, m, on=1.2, off=.8):
        L = math.dist(a, b); n = int(L / (on + off))
        for j in range(n + 1):
            t0 = j * (on + off) / L; t1 = min(1, t0 + on / L)
            if t0 < 1:
                s.seg((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1), w, z0, h, m)

    def raw(s, verts, faces, m, off=(0, 0, 0), sc=(1, 1, 1), smooth=False):
        b = len(s.v)
        s.v += [(off[0] + x * sc[0], off[1] + y * sc[1], off[2] + z * sc[2]) for x, y, z in verts]
        for f in faces:
            s.f.append(tuple(b + i for i in f)); s.m.append(s.mi(m)); s.sm.append(smooth)

    def build(s, name, c):
        if not s.v:
            return None
        me = bpy.data.meshes.new(name); me.from_pydata(s.v, [], s.f)
        me.polygons.foreach_set('material_index', s.m)
        me.polygons.foreach_set('use_smooth', s.sm)
        for m in s.mats:
            me.materials.append(m)
        me.update()
        # UVs por proyeccion de caja en metros / tamano de baldosa del material
        nl, npo = len(me.loops), len(me.polygons)
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        li = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', li)
        nrm = np.empty(npo * 3, np.float32); me.polygons.foreach_get('normal', nrm); nrm = np.abs(nrm.reshape(-1, 3))
        tot = np.empty(npo, np.int32); me.polygons.foreach_get('loop_total', tot)
        tile = np.array([TILE.get(m.name, 4.0) for m in s.mats], np.float32)[np.array(s.m, np.int32)]
        pn = np.repeat(nrm, tot, axis=0); pt = np.repeat(tile, tot); P = co[li]
        horiz = pn[:, 2] > .7; alongx = pn[:, 1] >= pn[:, 0]
        u = np.where(horiz | alongx, P[:, 0], P[:, 1]); v = np.where(horiz, P[:, 1], P[:, 2])
        uvl = me.uv_layers.new(name='UVMap')
        uvarr = np.column_stack((u / pt, v / pt)).astype(np.float32)
        for fi, quad in getattr(s, 'uvs', {}).items():            # caras con UV explicito (pantallas LED)
            ls = me.polygons[fi].loop_start
            for k, (uu, vv) in enumerate(quad):
                uvarr[ls + k] = (uu, vv)
        uvl.data.foreach_set('uv', uvarr.ravel())
        ob = bpy.data.objects.new(name, me); COLL[c].objects.link(ob)
        if c in PARENT:
            ob.parent = ROOT[PARENT[c]]
        return ob


def ico(subdiv):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    v = [tuple(x.co) for x in bm.verts]; f = [tuple(x.index for x in p.verts) for p in bm.faces]
    bm.free()
    return v, f


def cyl(n):
    v = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), z) for z in (0, 1) for i in range(n)]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return v, f


ICO1, ICO2, ICO3, CYL6, CYL8, CYL12 = ico(1), ico(2), ico(3), cyl(6), cyl(8), cyl(12)


def cone(n, r_top):
    """Tronco de cono (radio 1 abajo, r_top arriba, alto 1)."""
    v = [(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z) for z, r in ((0, 1), (1, r_top)) for i in range(n)]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return v, f


CONE6, TORSO = cone(6, .55), cone(6, 1.25)


def rot_pts(pts, c, ang):
    co, si = math.cos(ang), math.sin(ang)
    return [(c[0] + x * co - y * si, c[1] + x * si + y * co, c[2] + z) for x, y, z in pts]


BOXF = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def beam(mb, p0, p1, w, m):
    d = Vector(p1) - Vector(p0); a = d.normalized(); u = a.cross(Vector((0, 0, 1)))
    if u.length < 1e-4:
        u = Vector((1, 0, 0))
    u = u.normalized() * w / 2; v = a.cross(u).normalized() * w / 2
    P0, P1 = Vector(p0), Vector(p1)
    vs = [P0 - u - v, P0 + u - v, P0 + u + v, P0 - u + v, P1 - u - v, P1 + u - v, P1 + u + v, P1 - u + v]
    mb.raw([tuple(q) for q in vs], [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], m)


def truss(mb, p0, p1, w=.4, step=.9, m=None):
    m = m or M['alu']
    P0, P1 = Vector(p0), Vector(p1); d = P1 - P0; a = d.normalized()
    u = a.cross(Vector((0, 0, 1))) if abs(a.z) < .9 else a.cross(Vector((1, 0, 0)))
    u = u.normalized() * w / 2; v = a.cross(u).normalized() * w / 2
    cs = [u + v, -u + v, -u - v, u - v]
    for c in cs:
        beam(mb, P0 + c, P1 + c, .05, m)
    n = max(1, int(d.length / step))
    for i in range(n):
        q0 = P0 + d * (i / n); q1 = P0 + d * ((i + 1) / n)
        for k in range(4):
            beam(mb, q0 + cs[k], q1 + cs[(k + 1) % 4], .035, m)


def escalera_electrica(mb, x_top, x_bot, y0, y1, z_top, z_bot):
    """Par de escaleras electricas inclinadas (a lo largo de X) con pasamanos."""
    ym = (y0 + y1) / 2
    for ya, yb in ((y0, ym - .1), (ym + .1, y1)):
        v = [(x_top, ya, z_top), (x_top, yb, z_top), (x_bot, yb, z_bot), (x_bot, ya, z_bot)]
        v += [(x, y, z - .6) for x, y, z in v]
        mb.raw(v, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['escalera'])
        for yy in (ya, yb):
            beam(mb, (x_top, yy, z_top + 1.0), (x_bot, yy, z_bot + 1.0), .12, M['negro'])
            beam(mb, (x_top, yy, z_top + .5), (x_bot, yy, z_bot + .5), .06, M['vidrio'])


G = defaultdict(MB)     # mallas acumuladas: G[(coleccion, nombre)]


def flat_text(body, loc, size, m, c, rz=math.pi / 2):
    cu = bpy.data.curves.new('txt', 'FONT'); cu.body = body; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.extrude = .02; cu.font = FONT
    ob = bpy.data.objects.new('Txt_' + body, cu); ob.location = loc; ob.rotation_euler = (0, 0, rz)
    ob.data.materials.append(m); COLL[c].objects.link(ob)
    if c in PARENT:
        ob.parent = ROOT[PARENT[c]]
    return ob


def wall_text(body, loc, size, m, c, rz, extrude=.04):
    """Texto vertical (aviso sobre un muro). rz = giro en planta; por defecto mira hacia -Y."""
    cu = bpy.data.curves.new('aviso', 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude; cu.font = FONT
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('Aviso_' + body[:10], cu); ob.data.materials.append(m)
    ob.location = loc; ob.rotation_euler = (math.pi / 2, 0, rz); COLL[c].objects.link(ob)
    if c in PARENT:
        ob.parent = ROOT[PARENT[c]]
    return ob


# ---------------------------------------------------------------- datos del plano
E = {k: [tuple(p) for p in v] for k, v in D['edificios'].items()}
AZUL, ROJO, VERDE, VIPV = E['Azul'], E['Rojo'], E['Verde'], E['Zona_VIP_Verde']
ANEXO = rect(-12.9, 20.1, 5.3, 37.7)          # zona verde entre Azul y Blanco (HV1, cafe)
COM = E['Auditorio_Comunidades']
GS_ED, GS_SALA, CAJA, VOID = E['Gran_Salon_edificio'], E['Gran_Salon_sala'], E['Caja_Madera'], E['Caja_vacio']
GRADAS = E['Gradas_plazoleta']
cx0, cy0, cx1, cy1 = bbox(CAJA); vx0, vy0, vx1, vy1 = bbox(VOID)
gx0, gy0, gx1, gy1 = bbox(GS_ED)
PX0, PY0, PX1, PY1 = -30.1, 162.8, gx1 + 1.0, gy1 + 1.0     # foso del Gran Salon (piso 1)
sx0, sy0, sx1, sy1 = bbox(GRADAS); sy1 = 162.8


def river_x(y):
    return -205 - (y + 46) * 0.277


def regional_edge(y):
    return river_x(y) + 84


PLANCHA_COMIDAS = [(-1.2, -34.4), (47.2, -34.4), (47.2, -22.2), (-1.2, -22.2)]
HALL_ALTO = [(-1.2, -22.2), (34.6, -22.2), (34.6, 1.8), (-1.2, 1.8)]     # el extremo oriental del Hall queda al nivel del Amarillo
Z_MEZ = 9.6                                    # mezanine de Grupo Effi en el Hall
ZH_HALL = 4.5                                  # el Hall queda 1.2 m sobre Rojo / Amarillo / Zona de Comidas


BLOQUE_IA = [(-8.2, 72.8), (5.7, 72.8), (5.7, 97.5), (-8.2, 97.5)]     # enfermeria, banos y auditorio HV3 (nivel alto del Verde)


def z_blanco(y):
    # el Blanco baja en dos lineas de gradas desde el nivel del Hall (sur) hasta el nivel de la Plazoleta (norte)
    return ZH_HALL if y < 31.35 else (ZH_HALL / 2 if y < 44.85 else 0.)


def is_up(c):
    return pip(c, AZUL) or pip(c, VERDE) or pip(c, VIPV) or pip(c, BLOQUE_IA)


def group_of(c, reg):
    return {'rojo': 'inf', 'comunidades': 'inf', 'gran_salon': 'gs', 'multi': 'multi', 'caja': 'caja'}.get(reg) or ('sup' if is_up(c) else 'base')


def z_of(c, reg):
    return {'rojo': 0., 'comunidades': 0., 'gran_salon': Z_GS, 'multi': Z_MULTI, 'caja': 0.}.get(reg, Z_UP if is_up(c) else (ZH_HALL if (pip(c, HALL_ALTO) or pip(c, PLANCHA_COMIDAS) or pip(c, ANEXO)) else (z_blanco(c[1]) if pip(c, E['Blanco']) else 0.)))


# ================================================================ TERRENO
mb = G[('terreno', 'Terreno_y_plazas')]
HX0, HY0, HX1, HY1 = -41.5, sy0, PX1, PY1
for poly in (rect(-340, -240, 300, HY0), rect(-340, HY1, 300, 390), rect(-340, HY0, HX0, HY1), rect(HX1, HY0, 300, HY1)):
    mb.prism(poly, -0.6, .5, M['suelo'])
mb.prism(rect(sx1, sy0, PX1, PY0), Z_GS - .6, -Z_GS + .5, M['arenisca'])           # macizo al oriente de las gradas
mb.prism([(regional_edge(-240), -240), (-60, -240), (-60, -150), (-90, -136), (-112, -40), (-122, -10), (-122, 170), (-185, 170),
          (-185, 230), (regional_edge(230), 230)], -.1, .1, M['cesped'])
SITE = [(-90, -134), (97, -134), (97, 166), (PX1, 166), (PX1, PY0), (sx1, PY0), (sx1, sy0), (sx0, sy0), (sx0, 166), (-118, 166),
        (-118, -10), (-110, -40)]
mb.prism(SITE, -.1, .12, M['pav'])
for poly in (rect(-62, 166, -41.5, 300), rect(-41.5, PY1, PX0, 300), rect(PX1, 166, 97, 300), rect(PX0, PY1, PX1, 300)):
    mb.prism(poly, -.1, .12, M['pav_plaza'])
mb.prism(rect(-41.5, sy0, PX0 - .3, 172.0), -.6, .62, M['pav_plaza'])
mb.prism(rect(47, 169, 93, 212), .02, .5, M['cesped'])                       # jardin de bambu al oriente de la Caja (recorrido 360)
for poly in (rect(-118, 96, -102, 140), [(-90, -134), (-60, -134), (-60, -100), (-95, -110)]):
    mb.prism(poly, .0, .15, M['cesped'])
# foso del Gran Salon (piso 1) y gradas desde la Plazoleta Interamericana (dos tramos con descanso, PDF)
mb = G[('terreno', 'Foso_Gran_Salon_y_gradas')]
mb.prism(rect(PX0, PY0, PX1, PY1), Z_GS - .6, .6, MATS['piso_GS'])
for a, b in (((-21.4, PY1 + .3), (PX1 + .3, PY1 + .3)), ((PX1 + .3, PY1 + .3), (PX1 + .3, 262.0)), ((PX1 + .3, 222.0), (PX1 + .3, PY0))):
    mb.seg(a, b, .6, Z_GS, -Z_GS + .02, M['arenisca'])
mb.seg((PX1 + .3, 262.0), (PX1 + .3, 222.0), .6, Z_GS, -Z_GS - DZ_CONV + 2.6, M['arenisca'])
n1, yl0, yl1 = 15, sy0 + 4.6, sy0 + 6.1           # tramo 1, descanso, tramo 2
for i in range(n1):
    ya = sy0 + (yl0 - sy0) * i / n1; yb = sy0 + (yl0 - sy0) * (i + 1) / n1
    mb.prism(rect(sx0, ya, sx1, yb), Z_GS - .6, .6 - Z_GS + Z_MULTI, M['arenisca'] if i % 2 else M['pav_osc'])
mb.prism(rect(sx0, yl0, sx1, yl1), Z_GS - .6, .6 - Z_GS + Z_MULTI, M['pav'])
for i in range(n1):
    ya = yl1 + (sy1 - yl1) * i / n1; yb = yl1 + (sy1 - yl1) * (i + 1) / n1
    mb.prism(rect(sx0, ya, sx1, yb), Z_GS - .6, .6 + (Z_MULTI - Z_GS) * (1 - (i + 1) / n1), M['arenisca'] if i % 2 else M['pav_osc'])
for x in [sx0 + 8 * k for k in range(1, 8)]:        # pasamanos centrales (foto)
    beam(mb, (x, yl1, Z_MULTI + 1.0), (x, sy1, Z_GS + 1.0), .08, M['acero'])
# plaza sobre el Gran Salon (se oculta en modo mapa para dejar ver el piso 1)
mb = G[('losa', 'Losa_plaza_sobre_Gran_Salon')]
LX0 = -19.9


def fxw(y):
    # linea diagonal del muro que separa el pasillo exterior del interior (y del borde de la plaza encima)
    return -23.6 + (y - 172.0) * .0705


FX0 = -23.9
for rc in (rect(FX0, 168.0, PX1, 172.0), [(fxw(172.0), 172.0), (PX1, 172.0), (PX1, cy0), (fxw(cy0), cy0)],
           [(fxw(cy1), cy1), (PX1 - 11.0, cy1), (PX1 - 11.0, PY1), (fxw(PY1), PY1)], rect(PX1 - 11.0, cy1, PX1, 222.0), rect(PX1 - 11.0, 262.0, PX1, PY1), [(fxw(cy0), cy0), (cx0, cy0), (cx0, cy1), (fxw(cy1), cy1)], rect(cx1, cy0, PX1, cy1)):   # sin tapar el piso 3 de la Caja
    mb.prism(rc, -.4, .52, M['pav_plaza'])
FY = 167.8                                   # linea de fachada (borde del voladizo del piso 2)
RET = 2.6                                    # retranqueo de la vidriera del Gran Salon
Z1T = Z_GS + 4.6                             # cara superior de la losa del balcon (piso 2)
Z2T = -0.6                                   # losa de la plaza (piso 3)
PERS = mat('persiana_madera', (.20, .12, .07), .7)
LED = mat('pantalla_fachada', (.05, .08, .14), .3, 0, (.30, .55, 1.0), 1.6)
# --- piso 1: porche con pilares redondos, vidriera retranqueada con puertas, piso de piedra
xp = FX0 + 3.0
while xp < PX1 - 1:
    mb.raw(*CYL12, M['concreto'], (xp, FY + .6, Z_GS), (.45, .45, Z1T - .7 - Z_GS)); xp += 7.2
mb.prism(rect(FX0, FY + RET, PX1, FY + RET + .1), Z_GS, Z1T - .7 - Z_GS, M['vidrio'])
for xm in range(int(FX0) + 2, int(PX1), 2):
    mb.box((xm, FY + RET + .05, Z_GS), (.1, .18, Z1T - .7 - Z_GS), M['concreto_osc'])
for xd in (FX0 + 12, FX0 + 24, FX0 + 36):
    mb.box((xd, FY + RET + .02, Z_GS), (4.2, .3, 3.0), M['negro']); mb.box((xd, FY + RET - .05, Z_GS + .1), (3.9, .1, 2.8), M['vidrio_brt'])
mb.prism(rect(FX0, FY - .4, PX1, FY + RET), Z_GS - .3, .32, M['pav_plaza'])                # piso del porche
mb.prism(rect(FX0, FY, PX1, FY + RET + .3), Z1T - .7, .7, M['concreto'])                   # losa del voladizo
# --- piso 2: balcon corrido con baranda de acero, antepecho de concreto, ventanales, pantalla LED, persianas de madera al occidente
mb.prism(rect(FX0, FY - .3, PX1, FY + .1), Z1T, .9, M['concreto'])                         # antepecho
for xm in range(int(FX0) + 1, int(PX1), 2):
    mb.box((xm, FY - .1, Z1T + .9), (.05, .05, .5), M['acero'])
mb.box(((FX0 + PX1) / 2, FY - .1, Z1T + 1.35), (PX1 - FX0, .06, .06), M['acero'])
mb.prism(rect(FX0, FY + 1.8, PX1, FY + 1.9), Z1T, Z2T - 1.2 - Z1T, M['vidrio'])            # ventanales
for xm in range(int(FX0) + 2, int(PX1), 3):
    mb.box((xm, FY + 1.85, Z1T), (.14, .25, Z2T - 1.2 - Z1T), M['concreto_osc'])
mb.prism(rect(FX0, FY - .3, PX1, FY + 1.9), Z2T - 1.2, 1.2, M['concreto'])                 # viga/losa superior en voladizo
mb.prism(rect(FX0 + 2, FY - .2, FX0 + 22, FY + 1.9), Z1T + .9, Z2T - 1.2 - Z1T - .9, PERS)  # volumen de persianas (occidente)
for zz in [Z1T + 1.1 + k * .32 for k in range(int((Z2T - 1.2 - Z1T - 1.1) / .32))]:
    mb.box((FX0 + 12, FY - .22, zz), (20, .05, .1), M['negro'])
mb.box((FX0 + 34, FY - .25, Z1T + 1.6), (10, .12, 4.2), LED)                               # pantalla LED
mb.box((FX0 + 34, FY - .2, Z1T + 1.6), (10.3, .08, 4.5), M['negro'])
wall_text('PLAZA MAYOR  ·  CONVENCIONES Y EXPOSICIONES', (FX0 + 48, FY - .33, Z2T - .6), .45, M['blanco'], 'losa', 0.0)
# --- muros laterales de piedra (contencion de la plaza alta) y pasamanos de la escalinata
for a_, b_ in (((sx0 - .4, sy0), (sx0 - .4, FY)), ((sx1 + .4, sy0), (sx1 + .4, FY))):
    mb.seg(a_, b_, 1.0, Z_GS, Z_MULTI - Z_GS + .9, M['arenisca'])
for x in [sx0 + 8 * k for k in range(1, 8)]:
    beam(mb, (x, yl1, Z_MULTI + 1.0), (x, sy1, Z_GS + 1.0), .06, M['acero'])
# --- totem negro de senalizacion frente al acceso
mb.box((sx0 + 20, sy0 - 2.5, Z_MULTI), (.7, 1.2, 6.0), M['negro']); mb.box((sx0 + 20, sy0 - 3.12, Z_MULTI + 2.0), (.5, .02, 3.5), mat('totem_rojo', (.75, .05, .08), .4))

# ================================================================ VIAS Y RIO
mb = G[('vias', 'Vias_y_andenes')]; mk = G[('vias', 'Demarcacion_vial')]
YS, YN = -240, 390
for x0, x1, m, z in ((97, 103, 'pav', .02), (103, 114, 'asfalto', .02), (114, 115.5, 'cesped', .05), (115.5, 119, 'asfalto_brt', .02),
                     (119, 122.5, 'cesped', .05), (122.5, 126, 'asfalto_brt', .02), (126, 127.5, 'cesped', .05),
                     (127.5, 138.5, 'asfalto', .02), (138.5, 146, 'pav', .02)):
    mb.prism(rect(x0, YS, x1, YN), z - .06, .06, M[m])
for x in (106.7, 110.3, 131.2, 134.8):
    for y in range(YS, YN, 9):
        mk.box((x, y + 2, .03), (.15, 4, .02), M['linea'])
for x in (115.6, 125.9):
    mk.box((x, (YS + YN) / 2, .03), (.15, YN - YS, .02), M['linea_am'])


for x0, x1, m, z in ((-82, -64, 'cesped', .06), (-64, -56, 'asfalto', .04), (-56, -50, 'cesped', .08), (-50, -42, 'asfalto', .04),
                     (-42, -41.4, 'cesped', .06)):                # Carrera 57: zona verde, calzada, separador, calzada, zona verde
    mb.prism(rect(x0, 166, x1, 300), z - .06 + .1, .06, M[m])
mb.prism(rect(-64, 136, -42, 166.2), .0, .08, M['asfalto'])                    # empalme de las dos calzadas con la via transversal
mb.prism(rect(-56, 150, -50, 166.2), .02, .12, M['cesped'])
mb.raw(*CYL12, M['cesped'], (-53, 150, .02), (3.0, 3.0, .12))
for _cx, _sg in ((-78.0, 1), (-28.0, -1)):                                     # esquinas en curva (radio 14 m)
    _arc = [(_cx + _sg * 14 * math.cos(math.radians(a_)), 151.0 - 14 * math.sin(math.radians(a_))) for a_ in range(0, 91, 9)]
    _pol = [(_cx + _sg * 14, 137.0)] + _arc
    mb.prism(_pol if _sg > 0 else list(reversed(_pol)), .0, .08, M['asfalto'])
    for a_ in range(10, 90, 20):                                              # demarcacion de la curva
        mk.box((_cx + _sg * 17.5 * math.cos(math.radians(a_)), 151.0 - 17.5 * math.sin(math.radians(a_)), .1), (.15, 2.6, .02), M['linea'], -_sg * math.radians(a_))
for x in (-60, -46):
    for y in range(168, 300, 9):
        mk.box((x, y + 2, .15), (.15, 4, .02), M['linea'])


def oblique(mbx, o0, o1, m, z=.02, h=.06, y0=-240, y1=260):
    mbx.prism([(river_x(y0) + o0, y0), (river_x(y0) + o1, y0), (river_x(y1) + o1, y1), (river_x(y1) + o0, y1)], z - h, h, M[m])


for o0, o1, m, z in ((32, 42, 'cesped', .05), (42, 56, 'asfalto', .02), (56, 60, 'cesped', .05), (60, 74, 'asfalto', .02), (74, 84, 'pav', .02),
                     (-42, -32, 'cesped', .05), (-72, -42, 'asfalto', .02), (-80, -72, 'pav', .02)):
    oblique(mb, o0, o1, m, z)
for off in (46.7, 51.3, 64.7, 69.3, -62, -52):
    for y in range(-240, 260, 9):
        mk.box((river_x(y) + off, y + 2, .03), (.15, 4, .02), M['linea'], math.radians(15.5))
mb.prism([(regional_edge(124) - 2, 124), (-28, 124), (-28, 137), (regional_edge(137) - 2, 137)], -.04, .08, M['asfalto'])
mb.prism([(regional_edge(-152), -152), (146, -152), (146, -140), (regional_edge(-140), -140)], -.04, .08, M['asfalto'])
mb.prism(rect(97, 124, 146, 137), -.03, .08, M['asfalto'])
for x in range(-150, -30, 9):
    mk.box((x, 130.5, .05), (4, .15, .02), M['linea'])
for x in range(-80, 140, 9):
    mk.box((x, -146, .05), (4, .15, .02), M['linea'])
mb.prism(rect(46, 16, 95, 106), -.02, .08, M['asfalto'])                           # parqueadero
for i in range(16):
    for xx in (52, 70, 76, 94):
        mk.box((xx - 3, 20 + i * 5.2, .07), (6, .12, .02), M['linea'])
mb = G[('rio', 'Rio_Medellin')]
oblique(mb, -32, 32, 'agua', -1.2, .06, -240, 390)
oblique(mb, -29, 29, 'agua', .0, .1, -240, 390)
oblique(mb, -33, -29, 'cesped', .25, .3, -240, 390); oblique(mb, 29, 33, 'cesped', .25, .3, -240, 390)
oblique(mb, -34, -30, 'talud', -1.2, 1.2, -240, 390); oblique(mb, 30, 34, 'talud', -1.2, 1.2, -240, 390)

# ================================================================ PABELLONES


def walls_gaps(mb, poly, z0, h, t, m, gaps=(), skip=()):
    # muros por tramos dejando vanos: gaps = [(x, y, ancho)] con el centro de cada puerta sobre (o cerca de) el muro
    n = len(poly)
    for i in range(n):
        if i in skip:
            continue
        a, b = poly[i], poly[(i + 1) % n]; L = math.dist(a, b)
        if L < 1e-3:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        cuts = []
        for gx, gy, gw in gaps:
            s_ = (gx - a[0]) * ux + (gy - a[1]) * uy
            if abs((gx - a[0]) * uy - (gy - a[1]) * ux) < 1.3 and -gw / 2 < s_ < L + gw / 2:
                cuts.append((max(0., s_ - gw / 2), min(L, s_ + gw / 2)))
        pos = 0.
        for c0, c1 in sorted(cuts) + [(L, L)]:
            if c0 - pos > .6:
                mb.seg((a[0] + ux * (pos + t / 2), a[1] + uy * (pos + t / 2)), (a[0] + ux * (c0 - t / 2), a[1] + uy * (c0 - t / 2)), t, z0, h, m)
            pos = max(pos, c1)


# vanos (x, y, ancho): Hall <-> Blanco / Amarillo / Azul (gradas) / Rojo / Zona de Comidas; Blanco -> Plazoleta;
# Azul <-> Verde (2 accesos con panel azul, foto); Rojo -> Hall y salida a Zona de Comidas (foto)
PUERTAS_HALL = [(1.4, 1.8, 3.0), (12.0, 1.8, 6.0), (30.5, 1.8, 6.0), (46.3, -14.0, 8.0), (-1.2, -5.45, 8.5), (-1.2, -16.3, 5.0), (2.5, -22.2, 3.0), (13.5, -22.2, 6.0), (30.5, -22.2, 4.6)]
PUERTAS_BLANCO = [(12.0, 1.8, 6.0), (30.5, 1.8, 6.0), (22.5, 98.0, 18.0), (5.9, 27.7, 3.2)]
PASOS_DIV_AM = [(49.6, -55.2, 4.0), (86.0, -55.2, 4.0), (59.3, -55.2, 1.8), (76.9, -55.2, 1.8)]   # salida, ingreso y 2 accesos VIP
PUERTAS_AMARILLO = [(46.9, -14.0, 8.0), (47.4, -51.0, 3.5)] + PASOS_DIV_AM      # al Hall y a la Zona de Comidas
PUERTAS_AZUL_VERDE = [(-55.5, 19.7, 6.0), (-22.0, 19.7, 6.0)]
PUERTAS_ROJO = [(-9.2, -17.5, 6.0), (-15.0, -22.2, 5.0)]


def nave(poly, z0, H, key, ext, abre=()):
    # parte alta de una nave de exposicion: vidrio, cubierta, columnas en los costados largos, cerchas y ventiladores
    poly = ccw(poly); x0, y0, x1, y1 = bbox(poly)
    G[(ext, 'Muros_altos')].walls(poly, z0 + WALL_LOW, H - WALL_LOW, .12, M['vidrio'], skip=abre)
    G[(ext, 'Cubiertas')].prism(poly, z0 + H, 1.5, MATS.get('techo_' + key, MATS['muro_' + key]), side=MATS['muro_' + key])
    st = G[(ext, key + '_estructura')]
    zt = z0 + H - 1.1
    largo_y = (y1 - y0) >= (x1 - x0)
    n = max(2, round(((y1 - y0) if largo_y else (x1 - x0)) / 9.5))
    for i in range(n + 1):
        u = i / n
        if largo_y:
            yc = y0 + 2.5 + u * (y1 - y0 - 5); a, b = (x0 + 1.6, yc), (x1 - 1.6, yc)
        else:
            xc = x0 + 2.5 + u * (x1 - x0 - 5); a, b = (xc, y0 + 1.6), (xc, y1 - 1.6)
        for p_ in (a, b):
            if pip(p_, poly):
                st.raw(*CYL12, M['concreto'], (p_[0], p_[1], z0), (.42, .42, H - 1.6))
        truss(st, (a[0], a[1], zt), (b[0], b[1], zt), 1.1, 2.4, m=M['acero'])
    for k in (.25, .75):
        cx, cy = ((x0 + x1) / 2, y0 + k * (y1 - y0)) if largo_y else (x0 + k * (x1 - x0), (y0 + y1) / 2)
        st.raw(*CYL8, M['acero'], (cx, cy, zt - 1.6), (.35, .35, 1.0))
        for a_ in range(3):
            st.box((cx, cy, zt - 1.7), (6.4, .32, .05), M['blanco'], a_ * math.pi / 3)
    return st


def pavilion(poly, z0, h_total, key, grp, ext, roofed=True, low_h=WALL_LOW, t=.5, gaps=()):
    poly = ccw(poly)
    G[(grp, 'Pisos')].prism(poly, z0 - .45 if z0 > .1 else z0 - .25, .5 if z0 > .1 else .3, MATS.get('int_' + key, MATS['piso_' + key]))
    walls_gaps(G[(grp, 'Muros_bajos')], poly, z0, low_h, t, MATS['muro_' + key], gaps)
    if ext:
        walls_gaps(G[(ext, 'Muros_altos')], poly, z0 + low_h, h_total - low_h, t, MATS['fachada_pab'] if key in ('Amarillo', 'Blanco', 'Azul', 'Verde', 'Hall') else MATS['muro_' + key], [g_ for g_ in gaps if g_[2] > 8])
        if roofed:
            G[(ext, 'Cubiertas')].prism(poly, z0 + h_total, 1.5, MATS.get('techo_' + key, MATS['muro_' + key]), side=MATS['muro_' + key])   # cornisa del color del pabellon


pavilion(E['Amarillo_A'], 0, 19.0, 'Amarillo', 'base', None, gaps=[(47.0, -98.0, 3.0), (47.0, -75.0, 3.0)] + PASOS_DIV_AM)
_aA = ccw(E['Amarillo_A']); _aB = ccw(E['Amarillo_B'])
nave(E['Amarillo_A'], 0, 19.0, 'Amarillo', 'ext_base',
     abre=tuple(i for i in range(len(_aA)) if min(_aA[i][1], _aA[(i + 1) % len(_aA)][1]) > bbox(_aA)[3] - 1.5))
G[('ext_base', 'Cubiertas')].prism(rect(bbox(_aB)[0], bbox(_aA)[3] - .3, bbox(_aB)[2], bbox(_aB)[1] + .3), 19.0, 1.5,
                                   MATS.get('techo_Amarillo', MATS['muro_Amarillo']), side=MATS['muro_Amarillo'])
for _xw in (bbox(_aB)[0], bbox(_aB)[2]):                     # vidrio alto en el tramo de union
    G[('ext_base', 'Muros_altos')].seg((_xw, bbox(_aA)[3]), (_xw, bbox(_aB)[1]), .12, WALL_LOW, 19.0 - WALL_LOW, M['vidrio'])
G[('base', 'Muros_bajos')].box(((bbox(_aB)[0] + bbox(_aB)[2]) / 2, (bbox(_aA)[3] + bbox(_aB)[1]) / 2, WALL_LOW), (bbox(_aB)[2] - bbox(_aB)[0], 1.6, 2.6),
                               mat('division_temporal', (.05, .05, .06), .9))
DORADO_VIP = mat('catenaria_vip', (.80, .62, .28), .35, .6)


def zona_vip(nombre, x0, y0, x1, y1, z, grp='base', cortes=()):
    # zona VIP exclusiva (descanso y networking): tapete, catenarias doradas en el perimetro, salas lounge y rotulo
    zv = G[(grp, 'Zona_VIP_' + nombre)]
    zv.prism(rect(x0, y0, x1, y1), z + .03, .05, M['vip'])
    r = rect(x0, y0, x1, y1)
    for k in range(4):
        a, b = r[k], r[(k + 1) % 4]; L = math.dist(a, b); n = max(1, int(L / 1.6))
        for i in range(n + 1):
            px_, py_ = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
            if any(abs(py_ - c_) < .9 for c_ in cortes):
                continue
            zv.raw(*CYL6, DORADO_VIP, (px_, py_, z), (.05, .05, .95))
        zv.seg(a, b, .05, z + .85, .07, mat('cordon_vip', (.45, .04, .08), .6))
    for i in range(int((x1 - x0) / 6)):                    # salas lounge: sofas y mesas bajas
        xs_ = x0 + 3 + i * 6
        for ys_, sg in ((y0 + 1.6, 1), (y1 - 1.6, -1)):
            zv.box((xs_, ys_, z), (2.2, .9, .7), M['negro']); zv.box((xs_, ys_ + sg * 1.3, z), (.9, .9, .4), M['blanco'])
    flat_text('ZONA VIP', ((x0 + x1) / 2, (y0 + y1) / 2 + (y1 - y0) / 4, z + .12), 1.3, M['blanco'], grp)
    return zv


zona_vip('Amarillo', 54.5, -60.4, 82.8, -50.7, 0, cortes=(-55.2,))
_fin_vip = None   # division temporal (telon negro) del Auditorio Marketing     # h 10.7 m (plano oficial) + cubierta
pavilion(E['Amarillo_B'], 0, 19.0, 'Amarillo', 'base', None, gaps=PUERTAS_AMARILLO)
am = nave(E['Amarillo_B'], 0, 19.0, 'Amarillo', 'ext_base',
          abre=tuple(i for i in range(len(_aB)) if max(_aB[i][1], _aB[(i + 1) % len(_aB)][1]) < bbox(_aB)[1] + 1.5))
_amx0 = bbox(E['Amarillo_B'])[0]
am.box((_amx0 + .9, -12.0, 3.6), (1.4, 12.0, 1.1), MATS['muro_Amarillo'])          # franja amarilla sobre el acceso al Hall
am.box((_amx0 + 1.1, -12.0, 4.7), (1.8, 12.0, 3.0), M['vidrio'])                    # oficina acristalada encima
for ys_ in (-16.0, -13.3, -10.7, -8.0):
    am.box((_amx0 + .3, ys_, 0), (.14, .14, 3.6), M['acero'])                       # montantes de las puertas de vidrio
G[('base', 'Pisos')].prism(rect(47.2, -56.2, 88, -54.3), -.25, .3, MATS['piso_Amarillo'])
pavilion(E['Blanco'], 0, 18.0, 'Blanco', 'base', None, gaps=PUERTAS_BLANCO)
_b = bbox(E['Blanco']); PISO_BL = MATS.get('int_Blanco', MATS['piso_Blanco'])
G[('base', 'Pisos')].prism(rect(_b[0], _b[1], _b[2], 30.0), 0, ZH_HALL, M['concreto'], top=PISO_BL)
G[('base', 'Pisos')].prism(rect(_b[0], 30.0, _b[2], 43.5), 0, ZH_HALL / 2, M['concreto'], top=PISO_BL)
gb = G[('base', 'Gradas_Blanco')]
for _y0, _zb in ((30.0, ZH_HALL / 2), (43.5, 0.)):
    for i in range(12):
        gb.prism(rect(_b[0], _y0 + i * .225, _b[2] - 3.4, _y0 + (i + 1) * .225 + .01), 0, _zb + ZH_HALL / 2 * (12 - i) / 13, M['arenisca'] if i % 2 else M['concreto'])
    _r = [(_b[2] - 3.4, _y0, _zb + ZH_HALL / 2), (_b[2], _y0, _zb + ZH_HALL / 2), (_b[2], _y0 + 6.0, _zb + .03), (_b[2] - 3.4, _y0 + 6.0, _zb + .03)]
    _r += [(x, y, 0) for x, y, z in _r]
    gb.raw(_r, [(3, 2, 1, 0), (4, 5, 6, 7), (1, 5, 4, 0), (2, 6, 5, 1), (3, 7, 6, 2), (0, 4, 7, 3)], mat('rampa_blanco', (.62, .66, .50), .8))
    for _x in (_b[0] + 8.0, (_b[0] + _b[2]) / 2, _b[2] - 3.4):
        beam(gb, (_x, _y0, _zb + ZH_HALL / 2 + .9), (_x, _y0 + 2.7, _zb + .9), .04, M['acero'])   # muros bajos y piso; lo alto va aparte
HB = 18.0
_bp = ccw(E['Blanco']); bx0, by0, bx1, by1 = bbox(E['Blanco'])
_norte = tuple(i for i in range(len(_bp)) if min(_bp[i][1], _bp[(i + 1) % len(_bp)][1]) > by1 - 1.5)
G[('ext_base', 'Muros_altos')].walls(_bp, WALL_LOW, HB - WALL_LOW, .12, M['vidrio'], skip=_norte)
G[('ext_base', 'Cubiertas')].prism(_bp, HB, 1.5, MATS.get('techo_Blanco', MATS['muro_Blanco']), side=MATS['muro_Blanco'])
bl = G[('ext_base', 'Blanco_estructura')]
ZT = HB - 1.1                                            # eje de las cerchas
xs_col = (bx0 + 1.8, bx1 - 1.8)
ys_col = []
y = by0 + 3.0
while y < by1 - 2:
    ys_col.append(y); y += (by1 - by0 - 6.0) / 9
for yc in ys_col:
    for xc in xs_col:
        if pip((xc, yc), _bp):
            bl.raw(*CYL12, M['concreto'], (xc, yc, 0), (.42, .42, ZT - .5))      # columna redonda de concreto
    truss(bl, (xs_col[0], yc, ZT), (xs_col[1], yc, ZT), 1.1, 2.4, m=M['acero'])        # cercha transversal
for xc in (xs_col[0], (bx0 + bx1) / 2, xs_col[1]):
    truss(bl, (xc, ys_col[0], ZT), (xc, ys_col[-1], ZT), .7, 3.2, m=M['acero'])        # correas longitudinales
for xw in (bx0 + .12, bx1 - .12):                         # montantes y cables del cerramiento de vidrio
    yv = by0 + 2.4
    while yv < by1 - 1:
        bl.box((xw, yv, WALL_LOW), (.14, .14, HB - WALL_LOW - .2), M['acero']); yv += 4.8
    for zr in (WALL_LOW + 2.2, WALL_LOW + 4.6, WALL_LOW + 7.0):
        bl.box((xw, (by0 + by1) / 2, zr), (.07, by1 - by0 - 1.0, .07), M['acero'])
for yf in (by0 + (by1 - by0) * k for k in (.2, .5, .8)):  # ventiladores de techo de gran formato
    xf = (bx0 + bx1) / 2
    bl.raw(*CYL8, M['acero'], (xf, yf, ZT - 1.6), (.35, .35, 1.0))
    for a_ in range(3):
        bl.box((xf, yf, ZT - 1.7), (6.4, .32, .05), M['blanco'], a_ * math.pi / 3)
pavilion(E['Hall'], 0, 18.0, 'Hall', 'base', None, gaps=PUERTAS_HALL)
HH = 18.0
_hp = ccw(E['Hall']); hx0, hy0, hx1, hy1 = bbox(E['Hall'])
_plat = HALL_ALTO
G[('base', 'Pisos')].prism(_plat, 0, ZH_HALL, M['concreto'], top=MATS.get('int_Hall', MATS['piso_Hall']))
gh = G[('base', 'Gradas_Hall')]


def gradas(mb, x0, y0, x1, y1, hacia, zh, n=26):
    # gradas que bajan desde zh hasta 0 hacia 'E', 'O', 'N' o 'S' dentro del rectangulo dado
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n; h = zh * (n - i) / (n + 1)
        if hacia == 'E':
            r = rect(x0 + (x1 - x0) * u0, y0, x0 + (x1 - x0) * u1, y1)
        elif hacia == 'O':
            r = rect(x1 - (x1 - x0) * u1, y0, x1 - (x1 - x0) * u0, y1)
        elif hacia == 'N':
            r = rect(x0, y0 + (y1 - y0) * u0, x1, y0 + (y1 - y0) * u1)
        else:
            r = rect(x0, y1 - (y1 - y0) * u1, x1, y1 - (y1 - y0) * u0)
        mb.prism(r, 0, h, M['concreto'] if i % 2 else M['arenisca'])


def rampa(mb, x0, y0, x1, y1, hacia, zh, m_=None):
    # rampa que baja de zh a 0 hacia 'E' o 'S' dentro del rectangulo
    if hacia == 'E':
        v = [(x0, y0, zh), (x0, y1, zh), (x1, y1, .03), (x1, y0, .03)]
    else:
        v = [(x0, y1, zh), (x1, y1, zh), (x1, y0, .03), (x0, y0, .03)]
    v = v + [(x, y, 0) for x, y, z in v]
    mb.raw(v, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], m_ or M['concreto'])


RAMPA_M = mat('rampa_hall', (.62, .66, .50), .8)
gradas(gh, 34.6, -17.8, 40.4, -2.3, 'E', ZH_HALL)                 # gradas anchas que bajan al nivel del Amarillo (plano tecnico)
rampa(gh, 34.6, -20.2, 41.0, -18.2, 'E', ZH_HALL, RAMPA_M)
for _yb in (-17.8, -10.0, -2.3):
    beam(gh, (34.6, _yb, ZH_HALL + .9), (40.4, _yb, .9), .04, M['acero'])
for _ya, _yb in ((hy0 + .3, -20.2), (-2.3, hy1 - .3)):            # baranda del borde alto
    beam(gh, (34.6, _ya, ZH_HALL + .9), (34.6, _yb, ZH_HALL + .9), .05, M['acero'])
G[('base', 'Tapetes')].prism(rect(.2, -14.2, 11.2, 1.2), ZH_HALL + .01, .05, mat('tapete_grupo_effi', (.05, .22, .55), .9))
flat_text('AUDITORIO GRUPO EFFI', (5.7, -6.5, ZH_HALL + .08), 1.0, M['blanco'], 'base')
G[('base', 'Tarimas')].box((5.4, .2, ZH_HALL), (5.0, 2.2, .4), M['negro'])   # tarima pequena del Auditorio Grupo Effi            # bajan al Pabellon Amarillo
gradas(gh, hx0 - 6.6, -18.8, hx0 - .2, -13.8, 'O', ZH_HALL)       # bajan al Pabellon Rojo
G[('base', 'Pisos')].prism(PLANCHA_COMIDAS, 0, ZH_HALL, M['concreto'], top=M['pav'])      # plancha de comidas al nivel del Hall
gradas(gh, 1.7, -39.8, 47.2, -34.4, 'S', ZH_HALL, 26)
for _xr in (-1.2, 20.2, 34.8):                                    # rampas junto a las gradas (rayadas en el plano)
    rampa(gh, _xr, -46.5, _xr + 2.9, -34.4, 'S', ZH_HALL, RAMPA_M)                 # gradas a todo el ancho: bajan a la Zona de Comidas
beam(gh, (hx0, -22.4, ZH_HALL + .9), (hx0, -34.4, ZH_HALL + .9), .05, M['acero'])
_sin_gradas_blanco = None          # paso al Pabellon Blanco (2 accesos)
_sin_gradas_blanco = None
for _x in (1.8, 10.5, 20.1, 23.2, 29.0, 34.7, 37.8, 47.0):                # pasamanos de las gradas a la Zona de Comidas
    beam(gh, (_x, -34.4, ZH_HALL + .9), (_x, -39.8, .9), .04, M['acero'])
G[('ext_base', 'Muros_altos')].walls(_hp, WALL_LOW, HH - WALL_LOW, .12, M['vidrio'])
G[('ext_base', 'Cubiertas')].prism(_hp, HH, 1.5, MATS.get('techo_Hall', MATS['muro_Hall']), side=MATS['muro_Hall'])
hl = G[('ext_base', 'Hall_estructura')]
xh = hx0 + 3.0
while xh < hx1 - 1:                                      # cerchas de la cubierta del Hall
    truss(hl, (xh, hy0 + .6, HH - 1.0), (xh, hy1 - .6, HH - 1.0), 1.1, 2.4, m=M['acero']); xh += 6.9
for yh in (hy0 + 1.2, (hy0 + hy1) / 2, hy1 - 1.2):
    truss(hl, (hx0 + 1, yh, HH - 1.0), (hx1 - 1, yh, HH - 1.0), .7, 3.2, m=M['acero'])
AVISO = mat('aviso_negro', (.03, .03, .04), .5)
aviso_h = lambda mb, texto, c, largo, z, *a_, **k_: aviso(mb, texto, c, largo, z + 4.3, *a_, **k_)   # avisos del Hall: suben con el piso


def aviso(mb, texto, c, largo, z, rz, alto=1.1, size=.62, grp='ext_base'):
    # banda negra colgada con el nombre en blanco; rz = hacia donde mira (0 = sur, pi = norte, pi/2 = oriente, -pi/2 = occidente)
    mb.box((c[0], c[1], z), (largo if abs(math.sin(rz)) < .5 else .16, .16 if abs(math.sin(rz)) < .5 else largo, alto), AVISO)
    dx, dy = math.sin(rz) * .1, -math.cos(rz) * .1
    wall_text(texto, (c[0] + dx, c[1] + dy, z + alto / 2), size, M['blanco'], grp, rz)


aviso_h(hl, 'PABELLÓN BLANCO', (22.5, hy1 - .5), 26, 6.2, 0)                       # pared norte: acceso al Blanco
aviso_h(hl, 'SALIDA · EXIT', (3.0, hy1 - .5), 7.5, 6.2, 0, size=.5)
aviso_h(hl, 'PABELLÓN AMARILLO', (hx1 - .5, -12), 14, 5.2, -math.pi / 2)           # pared oriente: acceso al Amarillo
aviso_h(hl, 'PABELLÓN AZUL', (hx0 + .5, -5.45), 8.5, 7.4, math.pi / 2)               # sobre las gradas que suben al Azul
aviso_h(hl, 'PABELLÓN ROJO', (hx0 + .6, -16.3), 5, 4.6, math.pi / 2, .8, .42)      # acceso bajo al Rojo
aviso_h(hl, 'ZONA DE COMIDAS', (21.5, hy0 + .5), 24, 4.4, math.pi, .9, .5)             # pared sur: salida a la Zona de Comidas
hl.box((hx0 - 2.2, -11.6, 0), (2.6, 2.6, HH - 1.6), MATS['muro_Azul'])           # bloque azul del ascensor
hl.box((hx0 - .85, -11.6, ZH_HALL), (.12, 1.6, 2.3), M['acero'])                        # puerta del ascensor
n_g = 40                                                 # gradas anchas Hall -> Pabellon Azul (suben hacia el occidente)
for i in range(n_g):
    xa = hx0 - (i + 1) * (13.0 / n_g)
    gh.prism(rect(xa, -9.7, xa + 13.0 / n_g + .02, -1.2), 0, ZH_HALL + (i + 1) * (Z_UP - ZH_HALL) / n_g, M['concreto'])
for yb in (-9.7, -5.45, -1.2):                        # barandas de las gradas
    beam(gh, (hx0, yb, ZH_HALL + 1.0), (hx0 - 13.0, yb, Z_UP + 1.0), .05, M['acero'])
# mezanine (2o piso) del costado sur: Grupo Effi. Va en el nivel superior ('sup'): en el modo por niveles sube con el Azul.
mz = G[('sup', 'Hall_mezanine_Grupo_Effi')]
MX0, MX1, MY0, MY1 = hx0 + 6.0, hx1 - .6, hy0 + .5, hy0 + 9.6
mz.prism([(MX0, MY0), (MX1, MY0), (MX1, MY1), (MX0, MY1), (MX0, -15.0), (10.4, -15.0), (10.4, -19.4), (MX0, -19.4)], Z_MEZ - .5, .5, M['concreto'], top=mat('piso_grupo_effi', (.10, .12, .16), .55))
mz.box(((MX0 + MX1) / 2, MY1, Z_MEZ - .5), (MX1 - MX0, .22, 1.7), M['blanco'])                 # antepecho blanco del mezanine
aviso(mz, 'HALL PRINCIPAL  ·  EXHIBITION CENTER MAIN HALL', ((MX0 + MX1) / 2, MY1 + .05), MX1 - MX0, Z_MEZ - 1.5, math.pi, 1.0, .5, 'sup')
flat_text('GRUPO EFFI', ((MX0 + MX1) / 2, (MY0 + MY1) / 2, Z_MEZ + .03), 2.2, M['blanco'], 'sup', 0.0)
for xm in (MX0 + 9.5, (MX0 + MX1) / 2 - 4, (MX0 + MX1) / 2 + 6, MX1 - 4):                        # salas y lounges de Grupo Effi
    mz.box((xm, MY0 + 2.2, Z_MEZ), (5.0, 3.0, 2.6), M['stand_lado'])
    mz.box((xm, MY0 + 3.75, Z_MEZ + 1.9), (5.0, .12, .7), mat('grupo_effi_marca', (.05, .35, .75), .5))
xc_ = MX0 + 3.0
while xc_ < MX1:                                         # columnas del mezanine (se quitan con las cubiertas)
    hl.box((xc_, MY1 - .5, 0), (.7, .9, Z_MEZ - .5), M['concreto']); xc_ += 9.0
n_e = 24                                                 # escalera al mezanine (extremo occidental, sube hacia el oriente)
for i in range(n_e):
    xe = 16.0 - (i + 1) * 10.0 / n_e                  # escalera al mezanine: arranca junto a la Sala Unmerco y sube al occidente
    _h = ZH_HALL + (i + 1) * (Z_MEZ - ZH_HALL) / n_e; _p = 4.6 / (n_e // 2)
    if i < n_e // 2:                                       # tramo 1: sube hacia el occidente por el costado sur
        _xa = 10.4 - (i + 1) * _p
        gh.prism(rect(_xa, -19.4, _xa + _p + .02, -17.3), 0, _h, M['concreto'])
        if i == n_e // 2 - 1:
            gh.prism(rect(4.3, -19.4, 5.8, -15.0), 0, _h, M['concreto'])                      # descanso
    else:                                                  # tramo 2: regresa hacia el oriente por el costado norte
        _xb = 5.8 + (i - n_e // 2) * _p
        gh.prism(rect(_xb, -17.1, _xb + _p + .02, -15.0), 0, _h, M['concreto'])
for _ys in (-19.4, -17.2, -15.0):
    beam(gh, (10.4, _ys, ZH_HALL + 1.0), (5.8, _ys, (ZH_HALL + Z_MEZ) / 2 + 1.0), .04, M['acero'])
for _ys in (-19.75, -14.65):                               # accesos VIP a lado y lado
    gh.box((9.8, _ys, ZH_HALL), (1.4, .25, 1.1), mat('acceso_vip_verde', (.15, .65, .2), .5))
for k in ():
    G[('base', 'Muros_bajos')].walls(ccw(E[k]), ZH_HALL, 3.6, .25, M['stand_lado'])
# nivel superior: Azul + Zona VIP + Verde (+ anexo)
AZUL_N = [(-61.6, -22.2), (-1.9, -22.2), (-1.9, -9.7), (-14.2, -9.7), (-14.2, -1.2), (-1.9, -1.2), (-1.9, 19.6), (-61.6, 19.6)]   # vano de la escalera
pavilion(AZUL_N, Z_UP, 9.5, 'Azul', 'sup', None, gaps=PUERTAS_AZUL_VERDE + [(-14.2, -5.45, 8.5)])
HA = 9.5
_ap = ccw(AZUL); zx0, zy0, zx1, zy1 = bbox(AZUL)
_oriente = tuple(i for i in range(len(_ap)) if min(_ap[i][0], _ap[(i + 1) % len(_ap)][0]) > zx1 - 1.5)
G[('ext_sup', 'Muros_altos')].walls(_ap, Z_UP + WALL_LOW, HA - WALL_LOW, .12, M['vidrio'], skip=_oriente)
G[('ext_sup', 'Cubiertas')].prism(_ap, Z_UP + HA, 1.5, MATS.get('techo_Azul', MATS['muro_Azul']), side=MATS['muro_Azul'])
az = G[('ext_sup', 'Azul_estructura')]
ZA = Z_UP + HA - .9
xa_ = zx0 + 3.0
while xa_ < zx1 - 1:
    for ya_ in (zy0 + 1.6, (zy0 + zy1) / 2, zy1 - 1.6):
        if pip((xa_, ya_), _ap):
            az.raw(*CYL12, M['concreto'], (xa_, ya_, Z_UP), (.36, .36, HA - 1.3))
    truss(az, (xa_, zy0 + 1.6, ZA), (xa_, zy1 - 1.6, ZA), .9, 2.4, m=M['acero']); xa_ += 9.0
for ya_ in (zy0 + 1.6, (zy0 + zy1) / 2, zy1 - 1.6):
    truss(az, (zx0 + 3.0, ya_, ZA), (zx1 - 2.0, ya_, ZA), .6, 3.2, m=M['acero'])
for yw in (zy0 + .12, zy1 - .12):                        # montantes del vidrio en los costados largos
    xv = zx0 + 2.4
    while xv < zx1 - 1:
        az.box((xv, yw, Z_UP + WALL_LOW), (.14, .14, HA - WALL_LOW - .2), M['acero']); xv += 4.8
for xf in (zx0 + (zx1 - zx0) * k for k in (.25, .7)):    # ventiladores de techo
    yf = (zy0 + zy1) / 2 + 6
    az.raw(*CYL8, M['acero'], (xf, yf, ZA - 1.4), (.3, .3, .9))
    for a_ in range(3):
        az.box((xf, yf, ZA - 1.5), (5.6, .3, .05), M['blanco'], a_ * math.pi / 3)
for gx, gy, gw in PUERTAS_AZUL_VERDE:                    # accesos Azul <-> Verde: panel azul sobre puerta doble de vidrio
    az.box((gx, gy - .1, Z_UP + 2.7), (gw + 3.0, .3, 2.6), MATS['muro_Azul'])
    for s_ in (-gw / 2, 0, gw / 2):
        az.box((gx + s_, gy, Z_UP), (.12, .12, 2.7), M['acero'])
    G[('sup', 'Pisos')].prism(rect(gx - gw / 2, gy - .6, gx + gw / 2, gy + 1.6), Z_UP - .45, .5, M['concreto'])   # umbral / pasarela
pavilion(VERDE, Z_UP, 24.0 - Z_UP + .6, 'Verde', 'sup', 'ext_sup', gaps=PUERTAS_AZUL_VERDE + [(-36.2, 50.25, 19.4), (-29.55, 61.55, 8.4), (-8.95, 72.8, 5.5), (-8.2, 88.8, 15.2), (-3.9, 81.25, 8.8), (0.4, 77.0, 8.6)])
vd = G[('ext_sup', 'Verde_estructura')]
_vp = ccw(VERDE); wx0_, wy0_, wx1_, wy1_ = bbox(VERDE)
MONT_AM = mat('montante_amarillo', (.90, .74, .05), .5)
ZS_V = Z_UP + 8.4
_xv = wx0_ + 6.0
while _xv < wx1_ - 3:                                    # arcos transversales (cerchas tubulares blancas)
    _ys = [wy0_ + .5 * j for j in range(int((wy1_ - wy0_) / .5) + 1) if pip((_xv, wy0_ + .5 * j), _vp)]
    if len(_ys) > 20:
        _ya, _yb = _ys[0] + 1.0, _ys[-1] - 1.0
        for k in range(8):
            p0 = (_xv, _ya + (_yb - _ya) * k / 8, ZS_V + 3.0 * math.sin(math.pi * k / 8))
            p1 = (_xv, _ya + (_yb - _ya) * (k + 1) / 8, ZS_V + 3.0 * math.sin(math.pi * (k + 1) / 8))
            truss(vd, p0, p1, .9, 2.4, m=M['blanco'])
        truss(vd, (_xv, _ya, ZS_V), (_xv, _yb, ZS_V), .5, 3.2, m=M['blanco'])               # tirante inferior
        for _ye in (_ya, _yb):
            vd.raw(*CYL12, M['blanco'], (_xv, _ye, Z_UP), (.3, .3, 8.4))
        if int(_xv) % 2 == 0:                               # ventilador de techo
            for a_ in range(3):
                vd.box((_xv + 5, (_ya + _yb) / 2, ZS_V + 1.5), (6.0, .3, .05), M['blanco'], a_ * math.pi / 3)
    _xv += 11.0
for k in range(len(_vp)):                                # montantes amarillos del cerramiento de vidrio
    a_, b_ = _vp[k], _vp[(k + 1) % len(_vp)]; n_ = max(1, int(math.dist(a_, b_) / 3.2))
    for i in range(n_):
        vd.box((a_[0] + (b_[0] - a_[0]) * (i + .5) / n_, a_[1] + (b_[1] - a_[1]) * (i + .5) / n_, Z_UP), (.16, .16, WALL_LOW + 1.4), MONT_AM)
_fin = None   # h total 13.3 m desde el suelo
G[('base', 'Pisos')].prism(ANEXO, 0, ZH_HALL, M['concreto'], top=MATS['piso_Verde'])
G[('base', 'Pisos')].prism(rect(-.2, 1.8, 5.6, 20.1), 0, ZH_HALL, M['concreto'], top=mat('tapete_grupo_effi', (.05, .22, .55), .9))   # pasillo Grupo Effi
beam(G[('base', 'Gradas_Hall')], (-.2, 2.0, ZH_HALL + .95), (-.2, 20.0, ZH_HALL + .95), .05, M['acero'])
flat_text('GRUPO EFFI', (2.7, 11.0, ZH_HALL + .06), .9, M['blanco'], 'base')
pu = G[('base', 'Puentes_Verde_Blanco')]
P1X0, P1X1, P2X0, P2X1, PY0_, PY1_ = -11.7, -6.2, -3.2, .75, 37.7, 72.8
_w = [(P1X0, PY0_, ZH_HALL), (P1X1, PY0_, ZH_HALL), (P1X1, PY1_, Z_UP), (P1X0, PY1_, Z_UP)]
_w += [(x, y, max(0, z - .45)) for x, y, z in _w]
pu.raw(_w, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['concreto'])        # puente 1: a nivel, zona verde HV1/HV2 <-> Verde alto
for _xr in (P1X0 + .1, P1X1 - .1):
    beam(pu, (_xr, PY0_, ZH_HALL + 1.05), (_xr, PY1_, Z_UP + 1.05), .06, M['acero'])
    for k in range(13):
        pu.box((_xr, PY0_ + (PY1_ - PY0_) * k / 12, ZH_HALL + (Z_UP - ZH_HALL) * k / 12), (.06, .06, 1.05), M['acero'])
_v = [(P2X0, PY0_, ZH_HALL), (P2X1, PY0_, ZH_HALL), (P2X1, PY1_, .46), (P2X0, PY1_, .46)]   # puente 2: baja a la planta baja del Verde
_v += [(x, y, z - .45) for x, y, z in _v]
pu.raw(_v, [(3, 2, 1, 0), (4, 5, 6, 7), (1, 5, 4, 0), (2, 6, 5, 1), (3, 7, 6, 2), (0, 4, 7, 3)], M['concreto'])
for _xr in (P2X0 + .1, P2X1 - .1):
    beam(pu, (_xr, PY0_, ZH_HALL + 1.05), (_xr, PY1_, 1.5), .06, M['acero'])
    for k in range(13):
        u = k / 12; pu.box((_xr, PY0_ + (PY1_ - PY0_) * u, ZH_HALL + (.46 - ZH_HALL) * u), (.06, .06, 1.05), M['acero'])
for k in range(1, 4):                                     # apoyos de los dos puentes
    yc = PY0_ + (PY1_ - PY0_) * k / 4
    for _xr in (P1X0 + .7, P1X1 - .7):
        pu.raw(*CYL8, M['concreto'], (_xr, yc, 0), (.28, .28, max(.2, Z_UP * k / 4 - .45)))
    zc = 0
    if zc > .4:
        for _xr in (P2X0 + .5, P2X1 - .5):
            pu.raw(*CYL8, M['concreto'], (_xr, yc, 0), (.25, .25, zc))
_sin_escalera = None           # descanso y escalera de la zona verde al Blanco
_sin_escalera = None
_sin_escalera = None
# bloque de la Zona IA (nivel alto del Verde, junto al Blanco): enfermeria, banos y auditorio HV3 Lucid Bot
ia = G[('sup', 'Zona_IA_bloque')]
G[('sup', 'Pisos')].prism(BLOQUE_IA, Z_UP - .45, .5, MATS['piso_Verde'])
for a_, b_ in (((5.7, 72.8), (5.7, 97.5)), ((5.7, 97.5), (-8.2, 97.5)), ((-8.2, 97.5), (-8.2, 96.3)), ((.4, 72.8), (5.7, 72.8))):
    G[('sup', 'Muros_bajos')].seg(a_, b_, .5, Z_UP, WALL_LOW, MATS['muro_Verde'])
    G[('ext_sup', 'Muros_altos')].seg(a_, b_, .5, Z_UP + WALL_LOW, 24.0 - Z_UP + .6 - WALL_LOW, MATS['fachada_pab'])
G[('ext_sup', 'Cubiertas')].prism(BLOQUE_IA, 24.6, 1.5, MATS.get('techo_Verde', MATS['muro_Verde']), side=MATS['muro_Verde'])
for _c in ((5.2, 73.3), (5.2, 85.0), (5.2, 97.0), (-7.7, 85.0), (-7.7, 97.0), (.9, 73.3)):
    G[('ext_base', 'Cerramiento_nivel_inferior')].raw(*CYL8, M['concreto'], (_c[0], _c[1], 0), (.4, .4, Z_UP - .45))
ia.walls(rect(.9, 73.3, 5.4, 81.0), Z_UP, 2.8, .15, M['blanco'], skip=(3,))                    # enfermeria
ia.box((3.1, 77.1, Z_UP + 2.8), (4.5, 7.7, .12), M['blanco'])
wall_text('ENFERMERÍA', (.75, 77.1, Z_UP + 2.1), .42, mat('cruz_roja', (.75, .05, .08), .5), 'sup', math.pi / 2)
ia.box((1.1, 84.8, Z_UP), (9.0, 6.4, 2.9), M['concreto'])                                       # banos
wall_text('BAÑOS', (-3.5, 84.8, Z_UP + 2.0), .5, M['negro'], 'sup', math.pi / 2)
aviso(ia, 'AUDITORIO ZONA IA  ·  LUCID BOT', (-3.6, 92.6), 9.0, Z_UP + 2.7, math.pi / 2, .9, .42, 'sup')
aviso(pu, 'AUDITORIO COMUNIDADES', (-1.2, 72.5), 4.2, 3.3, 0, .8, .26, 'base')
G[('sup', 'Pisos')].prism(VIPV, Z_UP - .45, .8, M['vip'])
G[('ext_sup', 'Cubiertas')].prism(VIPV, Z_UP + 8, .5, M['vip'])
zvp = G[('sup', 'Zona_VIP_puente_catenarias')]
_vv = ccw(VIPV)
for k in range(len(_vv)):
    a, b = _vv[k], _vv[(k + 1) % len(_vv)]; L = math.dist(a, b)
    if max(a[1], b[1]) < 21.0 or L < 1.0:                # paso libre hacia el Azul
        continue
    n = max(1, int(L / 1.6))
    for i in range(n + 1):
        zvp.raw(*CYL6, DORADO_VIP, (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, Z_UP + .35), (.05, .05, .95))
    zvp.seg(a, b, .05, Z_UP + 1.2, .07, mat('cordon_vip', (.45, .04, .08), .6))
flat_text('ZONA VIP', (-31.0, 38.0, Z_UP + .42), 1.6, M['blanco'], 'sup')
# nivel inferior: Rojo (bajo el Azul) y Auditorio Comunidades (bajo el Verde)
G[('inf', 'Pisos')].prism(ccw(ROJO), -.25, .3, MATS['piso_Rojo'])
walls_gaps(G[('inf', 'Muros_bajos')], ccw(ROJO), 0, WALL_LOW, .5, MATS['muro_Rojo'], PUERTAS_ROJO)
# Pabellon Rojo (fotos): vestibulo de vidrio en la esquina suroriental con avisos de salida, columnas cuadradas y ducto
rj = G[('inf', 'Rojo_vestibulo')]
rx0, ry0, rx1, ry1 = bbox(ROJO)
rj.seg((rx1 - 9.0, ry0 + 8.2), (rx1 - 2.6, ry0 + 8.2), .08, 0, 2.9, M['vidrio'])
rj.seg((rx1 - 9.0, ry0 + .6), (rx1 - 9.0, ry0 + 5.6), .08, 0, 2.9, M['vidrio'])
SALIDA_R = mat('salida_verde', (.1, .5, .2), .4, emit=(.2, 1.0, .4), strength=2.5)
rj.box((rx1 - 5.5, ry0 + 8.2, 2.3), (3.0, .12, .5), SALIDA_R); rj.box((rx1 - .5, ry0 + 4.7, 2.3), (.12, 3.0, .5), SALIDA_R)
rj.box((rx0 + 37.6, ry0 + .5, 2.3), (3.0, .12, .5), SALIDA_R)
rr = G[('ext_base', 'Rojo_estructura')]
xr = rx0 + 9.0
while xr < rx1 - 4:
    for yr in (ry0 + 10.5, ry0 + 21.0, ry0 + 31.5):
        rr.box((xr, yr, 0), (.6, .6, H_LOW), M['concreto'])
    xr += 9.0
rr.box(((rx0 + rx1) / 2, ry0 + 15.8, H_LOW - 1.5), (rx1 - rx0 - 6, .9, .9), M['acero'])   # ducto de ventilacion
G[('inf', 'Pisos')].prism(ccw(COM), .02, .12, MATS['piso_Com'])
G[('inf', 'Muros_bajos')].walls(ccw(COM), .1, 2.2, .3, MATS['muro_Com'], skip=(3,))
ax0, ay0, ax1, ay1 = bbox(AZUL)
ex = G[('ext_base', 'Cerramiento_nivel_inferior')]
ex.walls(ccw(ROJO), WALL_LOW, H_LOW - WALL_LOW, .5, MATS['muro_Rojo'])
walls_gaps(ex, ccw(VERDE), 0, H_LOW, .5, MATS['muro_Verde_bajo'], [(-1.2, 72.8, 4.0)])
walls_gaps(ex, ANEXO, 0, WALL_LOW, .4, MATS['muro_Verde_bajo'], [(-8.95, 37.7, 5.5), (-1.2, 37.7, 4.0), (5.3, 27.7, 3.2), (2.7, 20.1, 5.4)])
for x in (ax0 + .6, ax0 + 7.6, ax0 + 14.6):
    for y in (ay0 + .6, (ay0 + ay1) / 2, ay1 - .6):
        ex.raw(*CYL8, M['concreto'], (x, y, 0), (.45, .45, H_LOW))
# zonas VIP del plano (dentro de pabellones)
for v in D['vip']:
    p = [tuple(q) for q in v['poly']]; c = centroid(p)
    g = group_of(c, v['region'])
    G[(g, 'Pisos')].prism(p, z_of(c, v['region']) + .02, .28, M['vip'])
# Gran Salon piso 1
gsm = G[('gs', 'Gran_Salon_muros')]
_gp = ccw(GS_ED)
gsm.walls(_gp, Z_GS, 4.0, .5, MATS['muro_GS'], skip=tuple(i for i in range(len(_gp)) if max(_gp[i][1], _gp[(i + 1) % len(_gp)][1]) < 169 or (_gp[i][0] + _gp[(i + 1) % len(_gp)][0]) / 2 < -15))
GS_SALA = [(x, (269.5 if y > 250 else y)) for x, y in GS_SALA]                    # fondo detras de la tarima (PDF: tarima en Y 261-268.5)
gsm.walls(ccw(GS_SALA), Z_GS, 4.5, .4, MATS['madera_clara'])                     # muros de madera clara del auditorio
G[('gs', 'Pisos')].prism(ccw(GS_SALA), Z_GS + .01, .08, MATS['alfombra_gs'])         # alfombra gris azulada
ZC_GS = -1.6                                             # cielo del auditorio: 7.4 m libres bajo la losa de la plaza
gc = G[('losa', 'Gran_Salon_cielo')]
gc.walls(ccw(GS_SALA), Z_GS + 4.5, ZC_GS - (Z_GS + 4.5), .4, MATS['madera_clara'])           # muros de madera hasta el cielo
gc.prism(ccw(GS_SALA), ZC_GS, .2, mat('cielo_gs', (.008, .008, .010), .95))
PANEL_GS = [mat('panel_gs_amarillo', (.86, .68, .02), .6), mat('panel_gs_verde', (.20, .52, .08), .6),
            mat('panel_gs_naranja', (.86, .26, .08), .6), mat('panel_gs_amarillo2', (.80, .62, .03), .6),
            mat('panel_gs_verde2', (.30, .56, .10), .6), mat('panel_gs_naranja2', (.80, .34, .10), .6)]
FOCO_GS = mat('foco_gs', (1, 1, 1), .3, emit=(1.0, .95, .85), strength=9.0)
rg = random.Random(26)
gx0, gy0, gx1, gy1 = bbox(GS_SALA)


def blob(cx, cy, rx, ry, rot, k=22):
    # panel acustico organico: elipse deformada (lobulos suaves) como los de la foto
    a2, a3 = rg.uniform(.10, .26), rg.uniform(.06, .16); f2, f3 = rg.uniform(0, 6.28), rg.uniform(0, 6.28)
    pts = []
    for i in range(k):
        th = 2 * math.pi * i / k
        r = 1 + a2 * math.cos(2 * th + f2) + a3 * math.cos(3 * th + f3)
        x, y = rx * r * math.cos(th), ry * r * math.sin(th)
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts


nx_, ny_ = 5, 13
for iy in range(ny_):
    for ix in range(nx_):
        cx = gx0 + (ix + .5 + rg.uniform(-.22, .22)) * (gx1 - gx0) / nx_
        cy = gy0 + (iy + .5 + rg.uniform(-.25, .25)) * (gy1 - gy0) / ny_
        if not pip((cx, cy), GS_SALA):
            continue
        gc.prism(blob(cx, cy, rg.uniform(2.3, 3.9), rg.uniform(1.3, 2.3), rg.uniform(0, math.pi)),
                 ZC_GS - rg.uniform(.9, 1.5), .14, PANEL_GS[rg.randrange(len(PANEL_GS))])
x = gx0 + 1.5
while x < gx1 - 1:                                       # focos puntuales entre los paneles
    y = gy0 + 2.0
    while y < gy1 - 1:
        if pip((x, y), GS_SALA):
            gc.raw(*CYL8, FOCO_GS, (x, y, ZC_GS - .22), (.18, .18, .2))
        y += 4.2
    x += 3.6
# Ingresos del auditorio (2a foto del recorrido 360): puertas dobles en la pared del lobby, cabina con ventanal encima,
# puertas laterales cerca del fondo y rejillas de aire en los muros largos.
lb = G[('gs', 'Lobby_Gran_Salon')]
_sx0, _sy0, _sx1, _sy1 = bbox(GS_SALA); _ex0, _ey0, _ex1, _ey1 = bbox(GS_ED)
VID_GS = mat('vidrio_gs_esmerilado', (.42, .66, .68), .25, alpha=.6)
lb.box(((_sx0 + _sx1) / 2, _sy0 - .6, Z_GS), (_sx1 - _sx0, .08, 3.3), VID_GS)              # frente de vidrio esmerilado
_xm = _sx0
while _xm <= _sx1 + .01:
    lb.box((_xm, _sy0 - .6, Z_GS), (.12, .16, 3.3), M['acero']); _xm += (_sx1 - _sx0) / 12
lb.box(((_sx0 + _sx1) / 2, _sy0 - .6, Z_GS + 3.3), (_sx1 - _sx0 + .4, .5, .35), M['blanco'])
lb.box((_sx0 - 5.0, _sy0 - .35, Z_GS + 2.5), (7.0, .12, 1.0), mat('aviso_gs_verde', (.42, .72, .08), .5))
wall_text('GRAN SALÓN', (_sx0 - 5.0, _sy0 - .45, Z_GS + 3.0), .6, M['blanco'], 'gs', 0.0)
for _c in ((vx0, vy0), (vx1, vy0), (vx0, vy1), (vx1, vy1), ((vx0 + vx1) / 2, vy0), ((vx0 + vx1) / 2, vy1), (_ex0 + 6, 176), (_ex1 - 8, 176)):
    lb.raw(*CYL12, M['concreto'], (_c[0], _c[1], Z_GS), (.45, .45, 4.1))                      # pilares redondos de concreto
PUERTA_BLACK = mat('puerta_black', (.17, .10, .05), .5)
for _yd in (174.5, 179.5, 184.5, 189.5, 194.5):                                              # salas de convenciones: Zona Black
    lb.box((_ex1 - .45, _yd, Z_GS), (.14, 2.6, 2.7), PUERTA_BLACK)
    lb.box((_ex1 - .52, _yd, Z_GS + .1), (.06, .06, 2.5), M['acero'])
aviso(lb, 'SALA DE NEGOCIOS  ·  PRENSA  ·  SALA VIP', (_ex1 - .6, 184.5), 18, Z_GS + 2.85, -math.pi / 2, .9, .5, 'gs')
BX0, BX1, BY0, BY1 = _sx1 + 1.7, _ex1 - .4, _sy0 + 1.0, 262.0
BCX = (BX0 + BX1) / 2; YA_B = 244.0
MUR_B = mat('muro_comisiones', (.86, .85, .80), .8); ALF_B = mat('alfombra_black', (.20, .21, .24), .9)
lb.prism(rect(BX0, BY0, BX1, BY1), Z_GS + .01, .06, ALF_B)
for a_, b_ in (((BX0, BY0), (BX0, BY1)), ((BX1, BY0), (BX1, BY1)), ((BX0, BY1), (BX1, BY1)),
               ((BX0, BY0), (BCX - 1.6, BY0)), ((BCX + 1.6, BY0), (BX1, BY0)),
               ((BCX - 1.6, BY0), (BCX - 1.6, YA_B)), ((BCX + 1.6, BY0), (BCX + 1.6, YA_B)),
               ((BX0, YA_B), (BCX - 1.6, YA_B)), ((BCX + 1.6, YA_B), (BX1, YA_B))):
    lb.seg(a_, b_, .2, Z_GS, 3.0, MUR_B)
_yb = BY0 + 5.0
while _yb < YA_B - 2:                                     # salas a lado y lado del pasillo, con puertas de madera abiertas
    for _sg in (-1, 1):
        lb.box((BCX + _sg * 1.05, _yb, Z_GS), (1.0, .07, 2.3), PUERTA_BLACK, _sg * 1.1)
        lb.box((BCX + _sg * 1.6, _yb + .9, Z_GS + 2.35), (.24, .5, .5), mat('aviso_gs_verde', (.42, .72, .08), .5))
    lb.seg((BX0, _yb + 4.2), (BCX - 1.6, _yb + 4.2), .15, Z_GS, 3.0, MUR_B)
    lb.seg((BCX + 1.6, _yb + 4.2), (BX1, _yb + 4.2), .15, Z_GS, 3.0, MUR_B)
    _yb += 8.4
for _sg in (-1, 1):                                       # puertas dobles del auditorio Black (Comisiones 5+6)
    lb.box((BCX + _sg * 1.1, YA_B - .5, Z_GS), (.07, 1.0, 2.3), PUERTA_BLACK)
lb.box((BCX, BY1 - 2.6, Z_GS), (8.0, 3.0, .5), M['negro'])                                   # tarima
pantalla(lb, (BCX - 3.0, BY1 - 1.2), (BCX + 3.0, BY1 - 1.2), .9, 2.6, LED_MAIN, .1) if 'LED_MAIN' in globals() else None
for _r in range(6):
    for _sg in (-1, 1):
        lb.box((BCX + _sg * 2.6, YA_B + 2.5 + _r * 1.7, Z_GS), (4.0, .5, .5), M['silla'])
aviso(lb, 'ZONA BLACK  ·  SALAS DE COMISIONES', (BCX, BY0 - .15), BX1 - BX0, Z_GS + 3.0, 0, .9, .5, 'gs')
for _xs in (BX0 + 1.6, BX0 + 4.6, BX1 - 1.6):                                                 # lounge de sofas negros en el acceso
    lb.box((_xs, BY0 - 3.4, Z_GS), (2.2, .9, .75), M['negro'])
_yp = 175.0
while _yp < PY1 - 1:                                                                        # pasillo lateral occidental: pilares
    lb.raw(*CYL12, M['concreto'], (fxw(_yp) - .25, _yp, Z_GS), (.42, .42, 8.5)); _yp += 7.5
lb.seg((fxw(186.0), 186.0), (fxw(PY1 - 1), PY1 - 1), .1, Z_GS + .1, 3.6, M['vidrio'])   # vidriera hacia el jardin
for _yd in (_sy0 + 7.0, _sy0 + 15.0, _sy0 + 30.0):                                           # ingresos laterales de vidrio esmerilado
    lb.box((_sx0 - .35, _yd, Z_GS), (.1, 4.6, 3.0), VID_GS)
    for _s in (-2.3, 0, 2.3):
        lb.box((_sx0 - .35, _yd + _s, Z_GS), (.14, .12, 3.0), M['acero'])
for _ym in range(187, 270, 4):                           # montantes de la vidriera entre pasillo interior y exterior
    lb.box((fxw(_ym), _ym, Z_GS), (.12, .12, 3.7), M['acero'])
zona_vip('Gran_Salon_1', -15.6, 209.8, -8.2, 230.3, Z_GS, 'gs', cortes=(230.3,))
zve = G[('gs', 'Zona_VIP_Gran_Salon_exterior')]
_e = [(fxw(232.0) - 4.4, 232.0), (fxw(232.0) - .9, 232.0), (fxw(266.0) - .9, 266.0), (fxw(266.0) - 4.4, 266.0)]
zve.prism(_e, Z_GS + .03, .05, M['vip'])
for k in range(4):
    a, b = _e[k], _e[(k + 1) % 4]; n = max(1, int(math.dist(a, b) / 1.6))
    for i in range(n + 1):
        if k == 0 and 0 < i < n:                             # acceso por el extremo sur
            continue
        zve.raw(*CYL6, DORADO_VIP, (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, Z_GS), (.05, .05, .95))
    if k != 0:
        zve.seg(a, b, .05, Z_GS + .85, .07, mat('cordon_vip', (.45, .04, .08), .6))
for _ym in range(235, 265, 4):                             # mesas con sillas de la zona VIP exterior
    _xm = fxw(_ym) - 2.9
    zve.box((_xm, _ym, Z_GS), (.9, 1.6, .75), M['negro'])
    for _d in (-.75, .75):
        zve.box((_xm + _d, _ym - .4, Z_GS), (.42, .42, .45), M['negro']); zve.box((_xm + _d, _ym + .4, Z_GS), (.42, .42, .45), M['negro'])
flat_text('ZONA VIP EXTERIOR', (fxw(250.0) - 1.6, 250.0, Z_GS + .12), .7, M['blanco'], 'gs')
lb.box((-13.4, 223.5, Z_GS), (1.9, 3.9, 1.1), M['negro'], top=M['blanco'])                    # barra 4x2 de la zona VIP
MESA_AZ = mat('mesa_networking', (.10, .22, .62), .5)
for _ym in [187.5 + 2.3 * k for k in range(9)]:          # mesas altas de networking junto a la vidriera
    lb.raw(*CYL8, M['acero'], (fxw(_ym) + 1.1, _ym, Z_GS), (.06, .06, 1.05)); lb.raw(*CYL8, MESA_AZ, (fxw(_ym) + 1.1, _ym, Z_GS + 1.05), (.38, .38, .05))
for _c in ((-15.4, 192.0), (-15.4, 194.6), (-13.6, 200.6), (-13.6, 203.0), (-15.8, 200.6), (-15.8, 203.0)):
    lb.raw(*CYL8, M['acero'], (_c[0], _c[1], Z_GS), (.06, .06, 1.05)); lb.raw(*CYL8, MESA_AZ, (_c[0], _c[1], Z_GS + 1.05), (.38, .38, .05))
lb.box((-17.2, 197.3, Z_GS + .9), (.14, 4.2, 2.3), M['negro'])                                # pantalla de la zona de networking
lb.box((-17.1, 197.3, Z_GS + 1.0), (.06, 3.9, 2.1), mat('pantalla_networking', (.05, .08, .14), .3, 0, (.30, .55, 1.0), 1.6))
for _r in range(3):
    for _k in range(10):
        lb.box((-15.9 + _r * .75, 195.3 + _k * .45, Z_GS), (.4, .4, .45), MESA_AZ)
flat_text('NETWORKING', (-13.0, 197.3, Z_GS + .1), .7, M['negro'], 'gs')
flat_text('ZONA DE PRENSA', (-16.5, 167.2, Z_GS + .1), .7, M['negro'], 'gs')
flat_text('PASILLO EXTERIOR', (fxw(205.0) - 3.4, 205.0, Z_GS + .1), .7, M['negro'], 'gs')
tal = G[('terreno', 'Talud_pasillo_exterior')]
tal.seg((-41.5, PY1), (fxw(PY1) - 4.8, PY1), .3, Z_GS, Z_MULTI - Z_GS, M['arenisca'])   # relleno verde a nivel
fac = G[('losa', 'Fachada_pasillo_exterior')]
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .5, Z_GS + 3.7, .4, M['concreto'])
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .3, Z_GS + 4.1, 3.0, PERS)
for _k in range(0, 96, 7):
    fac.seg((fxw(174.0 + _k) - .2, 174.0 + _k), (fxw(177.5 + _k) - .2, 177.5 + _k), .1, Z_GS + 5.0 + (_k % 3) * .7, .35, M['negro'])
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .5, -1.9, .4, M['concreto'])
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .4, -1.5, 2.4, M['arenisca'])
tp = G[('terreno', 'Taludes_plaza_alta')]                 # taludes de cesped y gradas que suben a la plaza de la Caja (coordenadas reales)
_zh = DZ_CONV + .1
RX_A, RX_B = PX1 + .5, PX1 + 8.0
ZR = 3.0
rampa(tp, RX_A, 160.0, RX_B, 220.0, 'S', ZR, M['pav_plaza'])                      # rampa peatonal (recuadro negro)
tp.prism(rect(PX1, 220.0, RX_B, 264.0), 0, ZR, M['arenisca'], top=M['pav_plaza'])   # llegada a nivel de la plaza
for _xr in (RX_A + .1, RX_B - .1):
    beam(tp, (_xr, 160.0, 1.0), (_xr, 220.0, ZR + 1.0), .06, M['acero'])
    for k in range(27):
        tp.box((_xr, 160.0 + 2.3 * k, ZR * k / 26), (.06, .06, 1.0), M['acero'])
MAD_GR = [mat('madera_gradas_a', (.16, .10, .06), .7), mat('madera_gradas_b', (.21, .13, .08), .7)]
for i in range(10):                                        # gradas anchas de madera oscura
    tp.prism(rect(PX1 - 11.0 + i * 1.1, 222.0, PX1 - 11.0 + (i + 1) * 1.1 + .02, 262.0), ZR - .4, _zh - (_zh - ZR) * (i + 1) / 11 - ZR + .4, MAD_GR[i % 2])
beam(tp, (RX_B - .1, 220.0, ZR + 1.0), (RX_B - .1, 264.0, ZR + 1.0), .06, M['acero'])                           # gradas (lineas moradas)
for _yb in (222.0, 262.0):
    beam(tp, (PX1 - 11.0, _yb, _zh + .9), (PX1, _yb, ZR + .9), .05, M['acero'])
for _yb in range(172, 221, 3):                                                      # balcon de la plaza sobre la rampa (linea naranja)
    tp.box((PX1 + .1, _yb, _zh), (.06, .06, 1.0), M['acero'])
beam(tp, (PX1 + .1, 172.0, _zh + 1.0), (PX1 + .1, 220.0, _zh + 1.0), .06, M['acero'])
tp.seg((PX1 + .25, 172.0), (PX1 + .25, 220.0), .5, 0, _zh, M['arenisca'])
rampa(tp, RX_B, 172.0, RX_B + 9.0, 264.0, 'E', 2.4, M['cesped'])                    # talud verde al costado de la rampa
rampa(tp, RX_A, 264.0, RX_B + 2.0, PY1 + .6, 'E', _zh, M['cesped'])
for _xa, _xb in ((-13.2, 6.0), (18.0, PX1 + .6)):
    _n = [(_xa, PY1 + .6, _zh), (_xb, PY1 + .6, _zh), (_xb, PY1 + 13.6, .05), (_xa, PY1 + 13.6, .05)]
    _n += [(x, y, 0) for x, y, z in _n]
    tp.raw(_n, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['cesped'])
gradas(tp, 6.0, PY1 + .6, 18.0, PY1 + 13.6, 'N', _zh, 28)
for _x in (6.0, 12.0, 18.0):
    beam(tp, (_x, PY1 + .6, _zh + .9), (_x, PY1 + 13.6, .9), .05, M['acero'])     # fachada del piso 2 sobre la vidriera
fac.seg((fxw(172.0), 172.0), (fxw(186.0), 186.0), .12, Z_GS + .1, 3.6, M['vidrio'])
_sin_remate_sur = None          # remates sur y norte del pasillo
fac.seg((fxw(PY1) - 5.0, PY1), (fxw(PY1), PY1), .4, Z_GS, -Z_GS - .5, M['arenisca'])
_t = [(-41.5, 172.0, Z_MULTI + .1), (-41.5, PY1, Z_MULTI + .1), (fxw(PY1) - 4.8, PY1, Z_GS + .5), (fxw(172.0) - 4.8, 172.0, Z_GS + .5)]   # manga suave desde la calle            # talud verde hacia la Carrera 57
_t += [(x, y, Z_GS) for x, y, z in _t]
tal.raw(_t, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['cesped'])
tal.seg((fxw(172.0) - 4.8, 172.0), (fxw(PY1) - 4.8, PY1), .3, Z_GS, .5, M['arenisca'])                               # bordillo del pasillo
tal.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .25, -.6, .7, M['concreto'])                                    # borde de la plaza
for _yb in range(174, int(PY1), 3):
    tal.box((fxw(_yb), _yb, .1), (.06, .06, 1.0), M['acero'])
beam(tal, (fxw(172.0), 172.0, 1.1), (fxw(PY1), PY1, 1.1), .06, M['acero'])
_sin_baranda = None
mur = G[('multi', 'Lobby_murales')]
MURAL = [mat('mural_gs_%d' % i, c, .6) for i, c in enumerate(((.35, .55, .25), (.70, .20, .18), (.20, .40, .65), (.80, .62, .20), (.25, .50, .45)))]
for _ya, _sg in ((vy0, 1), (vy1, -1)):                                                       # antepecho de concreto con murales fotograficos
    mur.box(((vx0 + vx1) / 2, _ya, Z_MULTI - 1.3), (vx1 - vx0, .25, 1.3), M['concreto'])
    for _i in range(5):
        mur.box((vx0 + (vx1 - vx0) * (_i + .5) / 5, _ya + _sg * .14, Z_MULTI - 1.15), (3.6, .05, 1.0), MURAL[_i])
for _xa, _sg in ((vx0, 1), (vx1, -1)):
    mur.box((_xa, (vy0 + vy1) / 2, Z_MULTI - 1.3), (.25, vy1 - vy0, 1.3), M['concreto'])
    mur.box((_xa + _sg * .14, (vy0 + vy1) / 2, Z_MULTI - 1.15), (.05, 5.0, 1.0), MURAL[(2 + _sg) % 5])
gd = G[('gs', 'Gran_Salon_puertas')]
PUERTA_GS = mat('puerta_gs', (.86, .84, .78), .5); MARCO_GS = mat('marco_gs', (.30, .20, .10), .6)
SALIDA_GS = mat('salida_gs', (.1, .5, .2), .4, emit=(.2, 1.0, .4), strength=3.0)
CABINA_GS = mat('cabina_gs', (.10, .07, .04), .15, emit=(1.0, .62, .25), strength=1.6)
gxm = (gx0 + gx1) / 2
for dx in (-9.6, -3.2, 3.2, 9.6):                         # 4 puertas dobles hacia el lobby
    gd.box((gxm + dx, gy0 + .26, Z_GS), (2.5, .12, 2.6), MARCO_GS)
    for s_ in (-.58, .58):
        gd.box((gxm + dx + s_, gy0 + .33, Z_GS + .05), (1.06, .08, 2.4), PUERTA_GS)
    gd.box((gxm + dx, gy0 + .30, Z_GS + 2.7), (.9, .08, .28), SALIDA_GS)
gd.box((gxm, gy0 + .28, Z_GS + 3.25), (12.5, .14, 1.15), MARCO_GS)       # cabina de control: marco y ventanal iluminado
for dx in (-4.1, 0, 4.1):
    gd.box((gxm + dx, gy0 + .36, Z_GS + 3.35), (3.8, .06, .95), CABINA_GS)
for xw, sg in ((gx0 + .26, 1), (gx1 - .26, -1)):          # puertas laterales (dos por costado, hacia el fondo de la sala)
    for yd in (gy0 + 7.0, gy0 + 15.0):
        gd.box((xw, yd, Z_GS), (.12, 2.5, 2.6), MARCO_GS)
        for s_ in (-.58, .58):
            gd.box((xw + sg * .07, yd + s_, Z_GS + .05), (.08, 1.06, 2.4), PUERTA_GS)
        gd.box((xw + sg * .04, yd, Z_GS + 2.7), (.08, .9, .28), SALIDA_GS)
    for yr in (gy0 + 14.0, gy0 + 34.0, gy0 + 52.0):       # rejillas de aire en lo alto del muro
        gc.box((xw, yr, Z_GS + 5.4), (.1, 5.0, .8), M['acero'])
        gc.box((xw + sg * .04, yr, Z_GS + 5.5), (.06, 4.6, .6), mat('rejilla_gs', (.12, .12, .13), .7))

# ================================================================ STANDS, SALAS ABIERTAS, SILLAS, TARIMAS, MESAS
CONT = [('Amarillo', E['Amarillo_A']), ('Amarillo', E['Amarillo_B']), ('Blanco', E['Blanco']), ('Verde', VERDE), ('Verde', ANEXO),
        ('Verde', VIPV), ('Hall', E['Hall']), ('Azul', AZUL)]


def stand_key(c, reg):
    k = {'rojo': 'Rojo', 'gran_salon': 'GS', 'caja': 'Caja', 'comunidades': 'Com', 'multi': 'Multi'}.get(reg)
    if k:
        return k
    for k, p in CONT:
        if pip(c, p):
            return k
    return 'Plaza'


obst = []
for s in D['stands']:
    p = [tuple(q) for q in s['poly']]; c = centroid(p); reg = s['region']
    k = stand_key(c, reg); z = z_of(c, reg); g = group_of(c, reg)
    x0, y0, x1, y1 = bbox(p)
    e1 = math.dist(p[0], p[1]); e2 = math.dist(p[1], p[2])
    franja = not s['codigo'] and max(e1, e2) > 7 * max(min(e1, e2), .1)
    if s['codigo'] == 'HV3':                              # Auditorio Lucid Bot (Zona IA): abierto, sin muros; se amuebla mas abajo
        G[(g, 'Salas_abiertas')].prism(p, z + .02, .1, MATS['stand_' + k])
        AUD_IA = (x0, y0, x1, y1, z, g)
        continue
    if s.get('sala') or 'caten' in s['texto'].lower() or len(p) > 5 or franja or s['codigo'] in ('PL17', 'PL18'):   # sala abierta / marcacion a piso: tapete
        if reg == 'gran_salon':
            p = [(a, max(b, 170.6)) for a, b in p]
        G[(g, 'Salas_abiertas')].prism(p, z + .02, .1, MATS['stand_' + k])
        if s['codigo']:
            flat_text(s['codigo'], (c[0], c[1], z + .14), .9, M['negro'], g)
        continue
    obst.append((x0, y0, x1, y1))
    h = 2.6 if max(x1 - x0, y1 - y0) < 9 else 3.2
    G[(g, 'Stands')].prism(p, z + .05, h, M['carpa'] if k == 'Plaza' else M['stand_lado'],
                           top=M['carpa_roja'] if k == 'Plaza' else MATS['stand_' + k])
    if s['codigo']:
        flat_text(s['codigo'], (c[0], c[1], z + h + .07), max(.45, min(1.3, min(x1 - x0, y1 - y0) * .32)), M['negro'], g)


def free(x, y, m=.6):
    return not any(a - m < x < c + m and b - m < y < d + m for a, b, c, d in obst)


# Auditorio UGC: tarima Livesound 12.2 x 3.7 al costado OCCIDENTAL, bajo la carpa, con la pantalla a lo largo
# del lado largo de atras: la pantalla le da la espalda al Ingreso con escarapela occidente (pin 21) y mira a las
# sillas. El centro de la carpa se fija con todas las sillas del plano; las que quedan bajo la tarima o a menos
# de 1.5 m de ella se quitan (quedan ~600 px, el aforo del auditorio).
_ug = [s for s in D['sillas'] if s[3] == 'main' and -25 < s[0] < 20 and 120 < s[1] < 152]
UGC_C = (sum(s[0] for s in _ug) / len(_ug), sum(s[1] for s in _ug) / len(_ug))
UGC_W, UGC_L = 25.0, 18.0                                           # carpa: lado largo oriente-occidente, corto norte-sur
UGC_TX0 = UGC_C[0] - UGC_W / 2 + .5                                 # borde occidental de la carpa + 50 cm
UGC_TX1 = UGC_TX0 + 3.7
D['sillas'] = [s for s in D['sillas'] if not (s in _ug and s[0] < UGC_TX1 + 1.5)]
for x, y, a, reg in D['sillas']:
    if reg == 'comunidades' and not pip((x, y), COM):
        continue
    G[(group_of((x, y), reg), 'Sillas')].box((x, y, z_of((x, y), reg) + .12), (.5, .5, .5), M['silla'], a)
chairs_xy = [(s[0], s[1]) for s in D['sillas']]
LED_MAIN = led_mat('led_main', 'led_main'); LED_WIDE = led_mat('led_wide', 'led_wide'); LED_LAT = led_mat('led_lateral', 'led_lateral')


def pantalla(mb, a, b, z0, h, m, grosor=.35):
    # Pantalla LED vertical de a a b (planta): bastidor negro y cara emisiva hacia el lado izquierdo de a->b
    L = math.dist(a, b); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    mb.box((c[0], c[1], z0), (L + .1, grosor, h + .1), M['negro'], ang)
    co, si = math.cos(ang), math.sin(ang); hx = L / 2; d = grosor / 2 + .02
    P = [(c[0] + x * co - y * si, c[1] + x * si + y * co) for x, y in ((-hx, d), (hx, d))]
    v0 = len(mb.v)
    mb.v += [(P[0][0], P[0][1], z0), (P[1][0], P[1][1], z0), (P[1][0], P[1][1], z0 + h), (P[0][0], P[0][1], z0 + h)]
    mb.f.append((v0 + 1, v0, v0 + 3, v0 + 2)); mb.m.append(mb.mi(m)); mb.sm.append(False)
    if not hasattr(mb, 'uvs'):
        mb.uvs = {}
    mb.uvs[len(mb.f) - 1] = [(1, 0), (0, 0), (0, 1), (1, 1)]


def torre_luces(mb, x, y, z0, h=6.0, n=4):
    truss(mb, (x, y, z0), (x, y, z0 + h), .35)
    for k in range(n):
        mb.box((x, y, z0 + 1.2 + k * (h - 1.6) / max(n - 1, 1)), (.45, .45, .5), M['luz_movil'])


TARIMAS = []
for t in D['tarimas']:
    c0 = centroid([tuple(q) for q in t['poly']])
    if t['region'] == 'main' and -18 < c0[0] < -12 and 130 < c0[1] < 144:        # UGC: ficha Livesound 12.2 x 3.7 (frente al oriente)
        ugy = UGC_C[1]                                                              # costado occidental de la carpa, centrada N-S
        TARIMAS.append({'region': 'main', 'texto': 'Tarima UGC 12.2 (Livesound)', 'poly': [[UGC_TX0, ugy - 6.1], [UGC_TX1, ugy - 6.1], [UGC_TX1, ugy + 6.1], [UGC_TX0, ugy + 6.1]],
                        'publico': UGC_C})                                         # el publico es la carpa, no las sillas de toda la plazoleta
    else:
        TARIMAS.append(t)
for t in TARIMAS:
    p = [tuple(q) for q in t['poly']]; c = centroid(p); reg = t['region']; z = z_of(c, reg); g = group_of(c, reg)
    e1 = math.dist(p[0], p[1]); e2 = math.dist(p[1], p[2]); big = max(e1, e2) > 4.5
    hh = .6 if max(e1, e2) > 12 else (1.0 if big else .6)          # fichas: principal 60 cm; secundarias 90-100 cm
    G[(g, 'Tarimas')].prism(p, z, hh, M['tarima'], side=M['faldon'])
    near = [(q[0], q[1]) for q in D['sillas'] if q[3] == reg and math.dist((q[0], q[1]), c) < (70 if big else 25)]   # solo sillas del mismo nivel
    if (big or reg in ('multi', 'comunidades')) and near:
        pc = t.get('publico') or centroid(near)
        largo = lambda i: math.dist(p[i], p[(i + 1) % len(p)])
        cand = range(len(p))
        if t.get('publico'):                                           # tarima angosta: la pantalla va a lo largo, nunca en la punta
            cand = [i for i in cand if largo(i) >= .9 * max(largo(j) for j in range(len(p)))]
        i = max(cand, key=lambda i: math.dist(((p[i][0] + p[(i + 1) % len(p)][0]) / 2, (p[i][1] + p[(i + 1) % len(p)][1]) / 2), pc))
        a_, b_ = p[i], p[(i + 1) % len(p)]; L = math.dist(a_, b_)
        W_, H_ = (15.0, 4.0) if L >= 18 else ((10.0, 3.0) if L >= 11 else (6.0, 2.5))   # pantalla central (fichas)
        W_ = min(W_, L - 1.0)
        ux, uy = (b_[0] - a_[0]) / L, (b_[1] - a_[1]) / L
        mid = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)
        nx, ny = -uy, ux                                               # lado izquierdo de a->b
        pa = (mid[0] - ux * W_ / 2, mid[1] - uy * W_ / 2); pb = (mid[0] + ux * W_ / 2, mid[1] + uy * W_ / 2)
        if (pc[0] - mid[0]) * nx + (pc[1] - mid[1]) * ny < 0:          # la cara emisiva mira al publico
            pa, pb = pb, pa; nx, ny = -nx, -ny
        pantalla(G[(g, 'Tarimas')], pa, pb, z + hh + .2, H_, LED_MAIN if W_ >= 12 else LED_WIDE)
        if big:
            for q in (a_, b_):                                         # torres de luces en las esquinas del fondo
                torre_luces(G[(g, 'Tarimas')], q[0] + (mid[0] - q[0]) * .06, q[1] + (mid[1] - q[1]) * .06, z + hh, 6.0 if L >= 18 else 4.4)
            if L >= 18:                                                # pantallas laterales 16:9 a media sala (Verde, Gran Salon)
                dist_pub = math.hypot(pc[0] - mid[0], pc[1] - mid[1])
                for s_ in (-1, 1):
                    cxl = mid[0] + nx * dist_pub * .45 + ux * s_ * .42 * L; cyl = mid[1] + ny * dist_pub * .45 + uy * s_ * .42 * L
                    la = (cxl - ux * 3.0, cyl - uy * 3.0); lb = (cxl + ux * 3.0, cyl + uy * 3.0)
                    if (pa[0] - pb[0]) * (la[0] - lb[0]) + (pa[1] - pb[1]) * (la[1] - lb[1]) < 0:
                        la, lb = lb, la
                    pantalla(G[(g, 'Tarimas')], la, lb, z + 4.0, 3.4, LED_LAT, .25)
# Auditorio Lucid Bot (HV3, Zona IA): tarima al norte con pantalla hacia el publico y sillas en dos bloques con pasillo central
_x0, _y0, _x1, _y1, _z, _g = AUD_IA
_cx = (_x0 + _x1) / 2
G[(_g, 'Tarimas')].box((_cx, _y1 - 1.3, _z), (6.0, 2.0, .6), M['tarima'], 0, None, M['faldon'])
pantalla(G[(_g, 'Tarimas')], (_cx + 3.0, _y1 - .2), (_cx - 3.0, _y1 - .2), _z + .8, 2.5, LED_WIDE)
for _sx in (-1, 1):
    torre_luces(G[(_g, 'Tarimas')], _cx + _sx * 3.6, _y1 - .5, _z, 4.4)
for _r in range(6):
    for _c in range(6):
        for _sx in (-1, 1):
            G[(_g, 'Sillas')].box((_cx + _sx * (.7 + _c * .6), _y0 + 1.1 + _r * .9, _z + .12), (.5, .5, .5), M['silla'])
obst.append((_cx - 3.0, _y1 - 2.3, _cx + 3.0, _y1 - .3))
for x, y, horiz, reg in D['mesas']:
    g = group_of((x, y), reg); z = z_of((x, y), reg); ang = math.pi / 2 if horiz else 0.0
    mb = G[(g, 'Mesas')]
    mb.box((x, y, z + .72), (.8, 1.4, .06), M['mesa'], ang); mb.raw(*CYL6, M['concreto_osc'], (x, y, z), (.08, .08, .72))
    for dx in (-.75, .75):
        for dy in (-.38, .38):
            mb.box((x + dx * math.cos(ang) - dy * math.sin(ang), y + dx * math.sin(ang) + dy * math.cos(ang), z), (.42, .42, .45), M['silla'], ang)
G[('multi', 'Tarimas')].seg((-6.9, 169.7), (-6.9, 174.7), .25, Z_MULTI + .6, 2.8, M['pantalla'])     # pantalla 4x2.5 (PDF)

# ================================================================ SALON MULTIPROPOSITO (piso 2, mas pequeno)
mx0, my0, mx1, my1 = bbox(E['Multi_bloque']); mx1 = min(mx1, PX1 - .6); my0 = max(my0, 168.4)   # no sobresale de la fachada hacia las gradas
wx0, wy0, wx1, wy1 = bbox(E['Multi_vacio'])
mu = G[('multi', 'Multiproposito_placa')]
for rc in (rect(mx0, my0, mx1, wy0), rect(mx0, wy1, mx1, my1), rect(mx0, wy0, wx0, wy1), rect(wx1, wy0, mx1, wy1)):
    mu.prism(rc, Z_MULTI - .5, .5, MATS['piso_Multi'])
OFI = [(max(x, -18.6), max(y, 170.5)) for x, y in E['Multi_oficina']]   # sin sobresalir al pasillo exterior
mu.prism(OFI, Z_MULTI - .5, .5, MATS['piso_Multi'])
mu.walls(rect(wx0, wy0, wx1, wy1), Z_MULTI, 1.1, .1, M['vidrio'])                    # baranda del vacio
mu.walls(rect(mx0, my0, mx1, my1), Z_MULTI, 1.3, .3, MATS['muro_Multi'], skip=(3,))
mu.walls(ccw(OFI), Z_MULTI, 2.6, .2, M['stand_lado'], skip=(1,))     # oficina Grupo Effi (paneleria)
for k in range(5):                                                                   # puestos de trabajo
    mu.box((-16.2, 172 + k * 5.5, Z_MULTI), (3.2, 1.4, .75), M['mesa'])
mu.box((33.5, 196.0, Z_MULTI), (3.5, 6.0, 1.1), M['mesa'], top=M['blanco'])        # cafeteria
ESC2 = E['Escalera_L2_L1']; ESC3 = E['Escalera_L3_L2']
escalera_electrica(mu, bbox(ESC2)[2], bbox(ESC2)[0], bbox(ESC2)[1], bbox(ESC2)[3], Z_MULTI, Z_GS)

# ================================================================ CAJA DE MADERA piso 3: portico, registro y taquillas (adentro)
cj = G[('caja', 'Caja_piso3_registro')]
for rc in (rect(cx0, cy0, cx1, vy0), rect(cx0, vy1, cx1, cy1), rect(cx0, vy0, vx0, vy1), rect(vx1, vy0, cx1, vy1)):
    cj.prism(rc, -.5, .52, MATS['piso_Caja'])
cj.walls(rect(vx0, vy0, vx1, vy1), .02, 1.1, .1, M['vidrio'])
escalera_electrica(cj, bbox(ESC3)[2], bbox(ESC3)[0], bbox(ESC3)[1], bbox(ESC3)[3], 0.0, Z_MULTI)
PORTICO = None
for it in D['caja_items']:
    p = [tuple(q) for q in it['poly']]; x0, y0, x1, y1 = bbox(p); t = it['tipo']
    if t == 'backing':                                   # backing de registro (muro de fondo de los counters)
        cj.prism(p, .02, 3.6, M['efx_n'], top=M['efx_r'])
        wall_text('REGISTRO · FERIA EFFIX 2026', (x1 + .06, (y0 + y1) / 2, 2.6), .9, M['blanco'], 'caja', math.pi / 2)
    elif t == 'counter':
        cj.prism(p, .02, 1.1, M['efx_n'], top=M['blanco'])
        cj.box((x1 + .9, (y0 + y1) / 2, .02), (.45, .45, .5), M['silla'])
    elif t == 'bodega':
        cj.prism(p, .02, 2.4, M['stand_lado'])
    elif t == 'control':                                 # punto de control: arco detector + torniquete
        c = centroid(p); horiz = (x1 - x0) > (y1 - y0)
        for d in (-1.1, 1.1):
            cj.box((c[0] + (d if horiz else 0), c[1] + (0 if horiz else d), .02), (.25, .25, 2.2), M['poste'])
        cj.box((c[0], c[1], 2.2), ((2.5, .3, .25) if horiz else (.3, 2.5, .25)), M['efx_r'])
    elif t == 'taquilla':                                # taquilla general / VIP - Black: modulo con ventanillas y marquesina
        cj.prism(rect(x1, y0, x1 + 2.2, y1), .02, 2.8, M['efx_n'])
        n = max(3, int((y1 - y0) / 2.0))
        for i in range(n):
            yv = y0 + (y1 - y0) * (i + .5) / n
            cj.box((x1 - .02, yv, 1.0), (.06, (y1 - y0) / n * .7, 1.2), M['vidrio_brt'])
            cj.box((x1 - .35, yv, 1.0), (.6, (y1 - y0) / n * .8, .08), M['concreto'])
        cj.prism(rect(x1 - 1.6, y0 - .4, x1 + 2.3, y1 + .4), 2.8, .3, M['efx_r'])
        wall_text('TAQUILLA GENERAL · VIP · BLACK', (x1 - 1.62, (y0 + y1) / 2, 3.45), .55, M['blanco'], 'caja', -math.pi / 2)
        cj.prism(rect(x1 - 1.7, y0 - .4, x1 - 1.55, y1 + .4), 3.1, .75, M['efx_n'])
    elif t == 'vip_black':                               # sala VIP / Black
        cj.walls(rect(20.9, 191.5, 25.9, 201.7), .02, 2.8, .2, M['negro'], top=mat('dorado_vip', (.80, .62, .28), .35, .6))
        cj.prism(rect(21.0, 191.6, 25.8, 201.6), .02, .1, M['vip'])
    elif t == 'portico':
        PORTICO = (x0, y0, x1, y1)
for a, b in D['caja_filas']:                             # filas con catenarias (lineas punteadas del PDF)
    L = math.dist(a, b); n = max(1, int(L / 1.6))
    for i in range(n + 1):
        cj.raw(*CYL6, M['concreto_osc'], (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, .02), (.05, .05, .95))
    cj.seg(a, b, .04, .88, .08, M['efx_r'])
if PORTICO:                                              # portico de ingreso LED (ficha Livesound: 10.2 x 5.1 m, vano 6 m, patas 1.5 x 2.1)
    x0, y0, x1, y1 = PORTICO
    cxp, yf = (x0 + x1) / 2, y1 + .4                    # frente hacia el norte (plaza / letrero Yo Medellin)
    cj.prism(rect(cxp - 6, cy1, cxp + 6, y1 + 3), -.5, .64, MATS['piso_Caja'])
    LED_U = led_mat('led_portal', 'led_wide'); LED_PATA = led_mat('led_pata', 'led_portal_pata', 2.0)
    for sg in (-1, 1):
        px_ = cxp + sg * 3.75                            # centro de cada pata
        cj.box((px_, yf - 1.05, 0), (1.5, 2.1, 3.0), M['negro'])
        for dx in (-.65, .65):
            for dy in (-.95, .95):
                truss(cj, (px_ + dx, yf - 1.05 + dy, 0), (px_ + dx, yf - 1.05 + dy, 5.1), .3, m=M['efx_n'])
        pantalla(cj, (px_ - .75, yf), (px_ + .75, yf), .05, 2.9, LED_PATA, .1)                     # LED frontal de la pata (mira al norte)
        if sg > 0:
            pantalla(cj, (px_ + .75, yf), (px_ + .75, yf - 2.1), .05, 2.9, LED_PATA, .1)             # LED lateral exterior (mira al este)
        else:
            pantalla(cj, (px_ - .75, yf - 2.1), (px_ - .75, yf), .05, 2.9, LED_PATA, .1)             # LED lateral exterior (mira al oeste)
    truss(cj, (cxp - 5.1, yf - 1.05, 5.1), (cxp + 5.1, yf - 1.05, 5.1), .4, m=M['efx_n'])       # dintel superior
    cj.box((cxp, yf - 1.05, 3.0), (10.2, 2.1, 2.1), M['negro'])                                   # caja superior
    pantalla(cj, (cxp - 5.0, yf), (cxp + 5.0, yf), 3.05, 2.0, LED_U, .1)                           # banda LED 10 x 2 (mira al norte)
    pantalla(cj, (cxp - 5.0, yf - 2.1), (cxp + 5.0, yf - 2.1), 3.05, 2.0, LED_U, .1)               # cara interior (hacia el registro)
for k in range(4):                                       # huella de la celosia (liston bajo) para leer la Caja abierta
    a_, b_ = rect(cx0, cy0, cx1, cy1)[k], rect(cx0, cy0, cx1, cy1)[(k + 1) % 4]; n_ = int(math.dist(a_, b_) / .9)
    for i in range(n_ + 1):
        if k == 2 and PORTICO and PORTICO[0] - 1 < a_[0] + (b_[0] - a_[0]) * i / n_ < PORTICO[2] + 1:
            continue
        G[('huella', 'Huella_celosia')].box((a_[0] + (b_[0] - a_[0]) * i / n_, a_[1] + (b_[1] - a_[1]) * i / n_, .02), (.28, .55, 1.3), MATS['muro_Caja'],
               math.atan2(b_[1] - a_[1], b_[0] - a_[0]))
for txt, xy, sz in (('REGISTRO · COUNTERS', (-1.6, 204), .8), ('UGC · PRENSA', (4.8, 198.2), .6), ('EXPOSITORES', (4.8, 206.3), .6),
                    ('ACREDITACIÓN VIP', (12.2, 194.6), .55), ('ACREDITACIÓN BLACK', (12.2, 201.2), .55), ('COMPRA GENERAL', (14.9, 210.0), .6),
                    ('COMPRA VIP / BLACK', (16.2, 215.2), .5), ('TAQUILLA', (24.6, 211), .8), ('SALA VIP / BLACK', (19.9, 196.6), .6),
                    ('ESCALERAS ELÉCTRICAS', (26.8, 183.3), .6), ('PÓRTICO DE INGRESO 10×6', (4.6, 222.2), .6), ('TARIMA 3×3', (11.0, 198.5), .45)):
    flat_text(txt, (xy[0], xy[1], .08), sz, M['negro'], 'caja')
# caparazon: base acristalada con columnas en V, losa, celosia de madera y cubierta (fotos de referencia)
sh = G[('shell', 'Caja_Madera_caparazon')]
madera_t = [MATS['madera_caja']]
BOX0, BOX1, R_IN = 7.2, 24.0, 0.9
outer = rect(cx0, cy0, cx1, cy1); inner = rect(cx0 + R_IN, cy0 + R_IN, cx1 - R_IN, cy1 - R_IN)
sh.walls(inner, .02, 6.4, .12, M['vidrio'], skip=(2,))
for k in range(4):
    a, b = inner[k], inner[(k + 1) % 4]; ao, bo = outer[k], outer[(k + 1) % 4]; L = math.dist(a, b)
    n = int(L / 3.0)
    for i in range(n + 1):
        if k == 2 and PORTICO and PORTICO[0] - 1 < a[0] + (b[0] - a[0]) * i / n < PORTICO[2] + 1:
            continue
        sh.box((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, .02), (.18, .18, 6.4), M['concreto_osc'])
    n = max(2, int(L / 7.5)); dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    for i in range(1, n):
        t = i / n; base = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0)
        top = (ao[0] + (bo[0] - ao[0]) * t, ao[1] + (bo[1] - ao[1]) * t)
        for sgn in (-1, 1):
            beam(sh, (top[0], top[1], 0), (top[0] + sgn * 2.2 * dx, top[1] + sgn * 2.2 * dy, BOX0), .32, M['acero'])   # columnas en V por fuera del vidrio
if PORTICO:                                               # vidrio del frente norte, con vano en el portico
    sh.seg(inner[3], (PORTICO[0] - 1, inner[3][1]), .12, .02, 6.4, M['vidrio']); sh.seg((PORTICO[2] + 1, inner[2][1]), inner[2], .12, .02, 6.4, M['vidrio'])
sh.walls(inner, 6.4, BOX0 - 6.4, .5, M['concreto'])
sh.prism(outer, BOX0 - .05, .6, M['concreto'])
sh.prism(rect(cx0 + .7, cy0 + .7, cx1 - .7, cy1 - .7), BOX0 + .5, BOX1 - BOX0 - .5, mat('caja_fondo', (.07, .05, .04), .8))
for k in range(4):
    a, b = outer[k], outer[(k + 1) % 4]; L = math.dist(a, b); n = int(L / .42); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for i in range(n + 1):
        sh.box((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, BOX0 + .55), (.13, .55, BOX1 - BOX0 - .55 + random.uniform(-.15, .15)),
               random.choice(madera_t), ang)
cub = mat('cubierta_caja', (.22, .22, .23), .6)
sh.prism(rect(cx0 + .3, cy0 + .3, cx1 - .3, cy1 - .3), BOX1 - .3, .35, cub)
sh.walls(rect(cx0 + .3, cy0 + .3, cx1 - .3, cy1 - .3), BOX1, .6, .3, cub)
ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
for ux, uy, w, d in ((-8, 6, 6, 4), (7, -5, 5, 5), (0, 10, 10, 2.5)):
    sh.box((ccx + ux, ccy + uy, BOX1 + .05), (w, d, 1.4), M['concreto_osc'])

# ================================================================ PLAZA NORTE (frente de la Caja): letrero Yo Medellin, banderas
ls = G[('losa', 'Frente_Caja_banderas')]
for i, y in enumerate(range(224, 268, 6)):
    ls.raw(*CYL6, M['poste'], (fxw(y) + 1.6, y, 0), (.07, .07, 9.0))
    ls.box((fxw(y) + 1.6, y + .8, 6.0), (.06, 1.4, 2.9), M['efx_r'] if i % 2 == 0 else M['efx_n'])
yo = empty('Letrero_YoMedellin', (26, 244, 0), 'losa'); yo.rotation_euler = (0, 0, math.pi)       # mira al norte (foto)
for body, dz in (('Yo', 3.0), ('Medellín', 0.0)):
    cu = bpy.data.curves.new('yo', 'FONT'); cu.body = body; cu.size = 4.0; cu.extrude = .5; cu.font = FONT; cu.align_x = 'LEFT'
    ob = bpy.data.objects.new('Letras_' + body, cu); ob.data.materials.append(M['blanco'])
    COLL['losa'].objects.link(ob); ob.parent = yo; ob.rotation_euler = (math.pi / 2, 0, 0); ob.location = (-8.5, 0, dz)
hz = MB()
for dx, dz, col in ((0, 0, (.35, .70, .25)), (1.15, .25, (.10, .40, .85)), (.35, -.85, (.90, .25, .20)), (1.35, -.75, (.98, .62, .12))):
    hz.raw(*ICO1, mat('corazon_%d' % int(dx * 10 + dz * 10 + 30), col, .4), (-2.6 + dx, -.3, 4.7 + dz), (.95, .4, .95))
ho = hz.build('Corazon', 'losa'); ho.parent = yo

# ================================================================ PLAZOLETA: estructuras flotantes, jardineras, carpa UGC, truss
def smooth(pts, k=6):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
        for j in range(k):
            t = j / k; t2 = t * t; t3 = t2 * t
            out.append(tuple(.5 * (2 * p1[d] + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2
                                   + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3) for d in (0, 1)))
    out.append(pts[-1])
    return out


def offset_line(pts, d):
    res = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1
        res.append((p[0] - ty / L * d, p[1] + tx / L * d))
    return res


# trazado digitalizado del plano tecnico (px del recorte -> pagina -> mundo); las dos bandas nacen en el ingreso
# occidental, una se abre hacia el sur y la otra hacia el norte, y vuelven a juntarse en el ingreso oriental
def _w(px, py):
    return ((771.6 + py * 1.314 - 1150) / 9.76, (2098.6 + px * 1.314 - 1300) / 9.25)


TRKS = [smooth([_w(*q) for q in ((315, 40), (250, 180), (190, 320), (150, 470), (140, 600), (165, 730), (205, 830), (245, 910))]),
        smooth([_w(*q) for q in ((315, 40), (335, 200), (348, 380), (340, 540), (315, 680), (285, 790), (250, 880), (245, 910))])]
mb = G[('mob', 'Estructuras_flotantes_plazoleta')]     # bandas curvas verde palido sobre postes blancos inclinados (fotos)
for ti, trk in enumerate(TRKS):
    G[('terreno', 'Franja_pavimento_plazoleta')].prism(offset_line(trk, -3.2) + list(reversed(offset_line(trk, 3.2))), .0, .05 + .005 * ti, M['pav_osc'])
    for d0 in (-1.6, 1.6):
        for off, hzt in ((-.55, 6.6 + .5 * ti), (.55, 7.3 + .5 * ti)):      # la segunda banda pasa un poco mas alta donde se cruzan
            line = offset_line(trk, d0 + off)
            for i in range(len(line) - 1):
                mb.seg(line[i], line[i + 1], 1.1, hzt, .32, M['arco'])
        mid = offset_line(trk, d0); acc = 0.0
        for i in range(len(mid) - 1):
            a, b = mid[i], mid[i + 1]; acc += math.dist(a, b)
            if acc >= 9.0:
                acc = 0.0
                tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1; nx, ny = -ty / L, tx / L; sg = 1 if d0 > 0 else -1
                base = (b[0] + nx * .9 * sg, b[1] + ny * .9 * sg, 0)
                beam(mb, base, (b[0] - nx * .55, b[1] - ny * .55, 6.6 + .5 * ti), .32, M['poste']); beam(mb, base, (b[0] + nx * .55, b[1] + ny * .55, 7.3 + .5 * ti), .32, M['poste'])
trk = TRKS[0]
PLANTERS = [(-23, 119), (-9.7, 118.4), (.2, 123.5), (8.1, 126.1), (32.7, 129.6), (43.1, 130.1), (63.1, 132.2), (71.3, 132.2), (79.4, 133.1)]
mb = G[('mob', 'Jardineras_y_truss')]
for x, y in PLANTERS:
    mb.raw(*CYL12, M['arenisca'], (x, y, 0), (2.2, 2.2, .55)); mb.raw(*CYL12, M['cesped'], (x, y, .55), (1.9, 1.9, .02))
    mb.raw(*ICO1, M['copa2'], (x, y, .75), (1.75, 1.75, .55), smooth=True)                       # arbustos
for x in range(70, 96, 5):
    mb.box((x, 107, 0), (1.4, 1.4, .6), M['arenisca'])
TRUSS_ING = ((-30, 125), (84, 120))                     # ingresos con escarapela: techo truss 8x4 sobre el cerramiento (PDF)
for x, y in TRUSS_ING:
    for dy in (-4, 4):
        truss(mb, (x, y + dy, 0), (x, y + dy, 5), .4, m=M['efx_n'])
    truss(mb, (x, y - 4, 5), (x, y + 4, 5), .4, m=M['efx_n'])
    mb.box((x, y, 5.2), (4.0, 8.8, .15), M['efx_n']); mb.box((x, y, 5.35), (4.1, 8.9, .6), M['efx_r'])          # techo 8x4 y banda roja
    for dy in (-2.6, 0, 2.6):                                                                                   # 3 carriles de control
        mb.box((x, y + dy, 0), (.25, .7, 2.2), M['poste'])
    wall_text('INGRESO CON ESCARAPELA', (x + (2.1 if x > 0 else -2.1), y, 4.6), .55, M['blanco'], 'mob', math.pi / 2 if x > 0 else -math.pi / 2)
# Pabellon Auditorio UGC: trimalla (cubierta plana en malla espacial) 25 x 18 m, 6 patas con ecopesos, con el lado largo
# oriente-occidente (tarima al occidente); piso en cesped sintetico (tapete 17)
# (UGC_C se fija antes de dibujar las sillas, con todas las del plano)
UW, UL, EAVE, RIDGE = UGC_W, UGC_L, 6.5, 8.0                        # girada 90°: lado largo oriente-occidente
ux0, ux1, uy0, uy1 = UGC_C[0] - UW / 2, UGC_C[0] + UW / 2, UGC_C[1] - UL / 2, UGC_C[1] + UL / 2
cg = G[('mob', 'Carpa_UGC_estructura')]
for x, y in ((ux0, uy0), (UGC_C[0], uy0), (ux1, uy0), (ux0, uy1), (UGC_C[0], uy1), (ux1, uy1)):          # 6 patas: las del medio en los lados largos
    truss(cg, (x, y, 0), (x, y, EAVE), .5)
    cg.box((x, y, 0), (1.2, 1.2, .5), M['concreto_osc'])                                                   # ecopeso
MOD = 2.0
nx, ny = int(UW / MOD), int(UL / MOD)
for i in range(nx + 1):                                                                                   # cordones inferiores
    beam(cg, (ux0 + i * MOD, uy0, EAVE), (ux0 + i * MOD, uy1, EAVE), .07, M['alu'])
    beam(cg, (ux0 + i * MOD, uy0, EAVE + 1.4), (ux0 + i * MOD, uy1, EAVE + 1.4), .07, M['alu'])
for j in range(ny + 1):
    beam(cg, (ux0, uy0 + j * MOD, EAVE), (ux1, uy0 + j * MOD, EAVE), .07, M['alu'])
    beam(cg, (ux0, uy0 + j * MOD, EAVE + 1.4), (ux1, uy0 + j * MOD, EAVE + 1.4), .07, M['alu'])
for i in range(nx):                                                                                       # diagonales de la malla espacial
    for j in range(ny):
        cx_, cy_ = ux0 + (i + .5) * MOD, uy0 + (j + .5) * MOD
        for dx, dy in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
            beam(cg, (cx_ + dx * MOD, cy_ + dy * MOD, EAVE), (cx_, cy_, EAVE + 1.4), .05, M['alu'])
lo = G[('mob', 'Carpa_UGC_lona')]
lo.prism(rect(ux0 - .4, uy0 - .4, ux1 + .4, uy1 + .4), EAVE + 1.45, .12, M['lona'])                       # lona superior
for a_, b_ in (((ux0 - .4, uy0 - .4), (ux1 + .4, uy0 - .4)), ((ux1 + .4, uy0 - .4), (ux1 + .4, uy1 + .4)),
               ((ux1 + .4, uy1 + .4), (ux0 - .4, uy1 + .4)), ((ux0 - .4, uy1 + .4), (ux0 - .4, uy0 - .4))):
    lo.seg(a_, b_, .06, EAVE + .9, .6, M['lona'])                                                         # faldon
# torres de luces (3), punto de encuentro, mesas de coctel (25) y cerramiento en malla brandeada de 2 m
mb = G[('mob', 'Plazoleta_montaje')]
for x, y in ((ux0 - 3, uy0 - 3), (ux1 + 3, uy0 - 3), (ux1 + 3, uy1 + 3)):
    truss(mb, (x, y, 0), (x, y, 7.5), .4); mb.box((x, y, 7.5), (1.2, .6, .5), M['negro'])
mb.raw(*CYL8, M['efx_n'], (-6, 108, 0), (.45, .45, 3.2)); mb.box((-6, 108, 3.2), (1.4, .3, .9), M['efx_r'])   # totem punto de encuentro
random.seed(7)
for _ in range(25):
    x = random.uniform(-26, -12); y = random.uniform(104, 128)
    if free(x, y, 1):
        mb.raw(*CYL8, M['blanco'], (x, y, 0), (.06, .06, 1.1)); mb.raw(*CYL12, M['blanco'], (x, y, 1.1), (.4, .4, .05))
# perimetro de la plazoleta: se detiene en las graderias (X -29.6..35.9, Y 153.6) y deja los dos vanos de 8 m de los ingresos
CERR = [((-30, 97), (97, 97)), ((97, 97), (97, 112)), ((97, 112), (84, 112)), ((84, 112), (84, 116)), ((84, 124), (84, 148)),
        ((84, 148), (36, 150)), ((-30, 150), (-30, 129)), ((-30, 121), (-30, 97))]
malla = mat('malla_brandeada', (.10, .10, .11), .8, alpha=.75)
for a_, b_ in CERR:
    mb.seg(a_, b_, .05, .2, 1.8, malla)
    n_ = int(math.dist(a_, b_) / 2.5)
    for k in range(n_ + 1):
        tt = k / max(n_, 1); mb.raw(*CYL6, M['poste'], (a_[0] + (b_[0] - a_[0]) * tt, a_[1] + (b_[1] - a_[1]) * tt, 0), (.05, .05, 2.0))
# tapetes de la feria (archivo 'Tapete Feria EFFIX a cotizar') con su color real
TAP = json.loads((R / 'tapetes_effix.json').read_text(encoding='utf8'))
def tap_m(x, y):
    if 2819 <= x <= 3817 and 864 <= y <= 1521:                                                            # recuadro del Gran Salon
        return (-29.303 + (y - 864) / 8.985, 164.216 + (x - 2819) / 8.57, 'gs')
    return ((y - 1150) / 9.76, (x - 1300) / 9.25, None)
for tp in TAP:
    if 'Académico' in tp['espacio']:
        continue                                                                                           # quedan dentro de los stands
    pts = [tap_m(x, y) for x, y in tp['poly']]; reg = pts[0][2]; p = [(a, b) for a, b, _ in pts]
    c = centroid(p); g = reg or group_of(c, 'main'); z = Z_GS if reg == 'gs' else z_of(c, 'main')
    h6 = tp['hex'].lstrip('#'); col = tuple(int(h6[i:i + 2], 16) / 255 for i in (0, 2, 4))
    G[(g, 'Tapetes')].prism(p, z + .12, .05, mat('tapete_' + tp['color'], tuple(v ** 2.2 for v in col), .9))

# ================================================================ VEGETACION
tr, cp = G[('veg', 'Troncos')], G[('veg', 'Copas')]


def blocked(x, y):
    return (PX0 - 3 < x < PX1 + 3 and sy0 - 2 < y < PY1 + 3) or not free(x, y, 2.5) or \
        (ux0 - 3 < x < ux1 + 3 and uy0 - 3 < y < uy1 + 3)


def tree(x, y, s=1.0, palm=False, force=False):
    if not force and blocked(x, y):
        return
    if palm:                                              # palma: tronco alto y hojas en estrella
        h = 8.5 * s
        tr.raw(*CONE6, M['tronco'], (x, y, 0), (.22 * s, .22 * s, h), smooth=True)
        a0 = random.uniform(0, 1)
        for k in range(9):
            a = a0 + k * 2 * math.pi / 9; L = 2.6 * s
            mid = (x + math.cos(a) * L * .55, y + math.sin(a) * L * .55, h + .5 * s); end = (x + math.cos(a) * L, y + math.sin(a) * L, h - .7 * s)
            beam(cp, (x, y, h), mid, .28 * s, M['palma']); beam(cp, mid, end, .2 * s, M['palma'])
        return
    h = random.uniform(3.6, 5.2) * s
    tr.raw(*CONE6, M['tronco'], (x, y, 0), (.3 * s, .3 * s, h + .8), smooth=True)
    m = random.choice((M['copa1'], M['copa2'], M['copa3'])); r = random.uniform(2.3, 3.0) * s
    cp.raw(*ICO2, m, (x, y, h + r * .6), (r, r, r * .82), smooth=True)
    for k in range(3):                                    # copa irregular: lobulos alrededor
        a = random.uniform(0, 2 * math.pi); rr = r * random.uniform(.5, .68); d = r * .62
        cp.raw(*ICO1, m, (x + math.cos(a) * d, y + math.sin(a) * d, h + r * random.uniform(.3, .8)), (rr, rr, rr * .85), smooth=True)


def tree_line(a, b, step, jitter=.6, s=(.85, 1.25), palm=False):
    n = max(1, int(math.dist(a, b) / step))
    for i in range(n + 1):
        t = i / n
        tree(a[0] + (b[0] - a[0]) * t + random.uniform(-jitter, jitter), a[1] + (b[1] - a[1]) * t + random.uniform(-jitter, jitter),
             random.uniform(*s), palm)


for x in (100, 114.8, 126.8, 142):
    tree_line((x, YS), (x, YN), 9 if x in (100, 142) else 11)
for off in (37, 58, 79, -37, -76):
    tree_line((river_x(-240) + off, -240), (river_x(255) + off, 255), 10)
tree_line((-112, -30), (-112, 160), 9); tree_line((-80, -125), (90, -125), 10)
for x, y in PLANTERS:
    tree(x, y, 1.15, force=True)
tree_line((-60, 296), (94, 296), 9); tree_line((-62, 168), (-62, 292), 8)
tree_line((93, -128), (93, 160), 7); tree_line((46, 110), (95, 110), 7)
tree_line((-86, -128), (-112, -45), 8); tree_line((-118, 0), (-118, 165), 7); tree_line((-100, 100), (-100, 160), 8, palm=True)
for _ in range(46):                                        # jardin de bambu: masa densa y alta
    tree(random.uniform(49, 91), random.uniform(171, 210), random.uniform(.75, 1.1), force=True)
for _ in range(10):
    tree(random.uniform(49, 91), random.uniform(171, 210), random.uniform(.6, .8), palm=True, force=True)
for _ in range(90):
    x = random.uniform(-180, -110); y = random.uniform(-200, 230)
    if regional_edge(y) + 6 < x < -112 and not (-170 < x < -78 and 138 < y < 218):
        tree(x, y, random.uniform(.9, 1.4))
for _ in range(30):
    x = random.uniform(-2, 45); y = random.uniform(-120, -30)
    if all(math.dist((x, y), (m[0], m[1])) > 4 for m in D['mesas']):
        tree(x, y, random.uniform(.8, 1.1))

# ================================================================ ENTORNO
mb = G[('entorno', 'Entorno_hitos')]
mb.prism(rect(-165, 142, -82, 214), 0, .2, M['pav'])                                 # Teatro Metropolitano
pr = G[('entorno', 'Parques_del_Rio')]
PRY0, PRY1 = 150, 388
TUNEL = mat('tunel_parques', (.02, .02, .025), .9)
for _o0, _o1 in ((34, 86), (-86, -34)):                    # losa del parque sobre las calzadas, a ambos lados del rio
    oblique(pr, _o0, _o1, 'concreto', 1.6, 1.6, PRY0 + .6, PRY1)
    oblique(pr, _o0 + 1.5, _o1 - 1.5, 'pav', 1.72, .12, PRY0 + 1.5, PRY1)
    oblique(pr, _o0 + 5 if _o0 > 0 else _o0 + 20, _o1 - 20 if _o0 > 0 else _o1 - 5, 'cesped', 1.86, .14, PRY0 + 8, PRY1 - 6)
    for _a, _b in ((_o0 + 9, _o0 + 22), (_o0 + 27, _o0 + 40)) if _o0 > 0 else ((_o1 - 40, _o1 - 27), (_o1 - 22, _o1 - 9)):
        pr.box((river_x(PRY0) + (_a + _b) / 2, PRY0 - .2, .05), (_b - _a, .8, 1.45), TUNEL, math.radians(15.5))   # bocas del tunel
pr.prism([(river_x(205) - 36, 205), (river_x(205) + 36, 205), (river_x(213) + 36, 213), (river_x(213) - 36, 213)], 1.5, .5, M['concreto'],
         top=M['cesped'])                                  # puente peatonal sobre el rio
ENREJADO = mat('enrejado_parques', (.03, .03, .035), .5)
for _yp, _of in ((232, 52), (247, 58), (262, 50)):          # pabellones negros con cubierta en celosia
    _xp = river_x(_yp) + _of
    pr.box((_xp, _yp, 1.86), (9, 7, 3.4), ENREJADO, math.radians(20))
    pr.box((_xp, _yp, 5.6), (13, 11, .25), ENREJADO, math.radians(35))
    for _dx, _dy in ((-5, -4), (5, -4), (5, 4), (-5, 4)):
        beam(pr, (_xp + _dx, _yp + _dy, 1.86), (_xp + _dx * 1.1, _yp + _dy * 1.1, 5.6), .12, ENREJADO)
for _yt in range(170, 380, 11):
    for _of in (40, 62, 78, -44, -60, -78):
        if not (228 < _yt < 268 and 44 < _of < 66):
            tree(river_x(_yt) + _of + random.uniform(-3, 3), _yt + random.uniform(-3, 3), random.uniform(.7, 1.1), force=True)
mb.prism(rect(-158, 150, -92, 205), 0, 14, M['ladrillo']); mb.prism(rect(-148, 158, -102, 198), 14, 9, M['ladrillo'], top=M['techo_gris'])
mb.prism(rect(-140, 162, -110, 194), 23, 2, M['techo_gris']); mb.prism(rect(-92, 160, -84, 195), 0, 8, M['ladrillo'])
mb.prism(rect(119.2, 140, 122.3, 200), 0, 1.0, M['concreto']); mb.prism(rect(118.6, 140, 122.9, 200), 4.2, .3, M['vidrio_brt'])   # Metroplus
for y in range(142, 200, 8):
    mb.raw(*CYL8, M['poste'], (120.75, y, 1), (.18, .18, 3.2))
mb.walls(rect(119.2, 140, 122.3, 200), 1.0, 2.4, .08, M['vidrio_brt'])
mb.box((121, 146, 6.5), (52, 3.6, .5), M['concreto'])                                # puente peatonal Av. Ferrocarril
mb.walls(rect(95, 144.2, 147, 147.8), 7.0, 1.1, .08, M['vidrio_brt'], skip=(1, 3))
for x in (98, 110, 121, 132, 144):
    mb.raw(*CYL8, M['concreto'], (x, 146, 0), (.4, .4, 6.5))
for i in range(13):
    mb.box((92 - i * .3 - 1, 146, 0), (.6, 3.6, 6.5 * (13 - i) / 13), M['concreto'])
mb.seg((river_x(55) + 86, 55), (river_x(20) - 82, 20), 3.5, 5.5, .5, M['concreto'])  # puente peatonal del rio
# edificio de servicios de Plaza Mayor (piedra, cubierta con paneles solares) entre la plaza de la Caja y la Av. Ferrocarril
mb.prism(rect(80, 216, 95, 300), 0, 11, M['arenisca'], top=MATS['solar'])
mb.prism(rect(79.6, 216, 80, 300), 3.2, 3.0, M['vidrio'])
mb = G[('entorno', 'Ciudad')]
cmats = [M['ciudad1'], M['ciudad2'], M['ciudad3'], M['ciudad4']]


def blocks(x0, x1, y0, y1, bw=34, bh=30, street=11, hmin=6, hmax=30):
    x = x0
    while x + bw <= x1:
        y = y0
        while y + bh <= y1:
            for sx in range(2):
                for sy in range(2):
                    if random.random() < .85:
                        w, d = (bw - 2) / 2 - 1, (bh - 2) / 2 - 1
                        h = random.choice((hmin, hmin * 1.5, hmin * 2, random.uniform(hmin, hmax)))
                        mb.box((x + 1 + sx * (bw / 2) + w / 2, y + 1 + sy * (bh / 2) + d / 2, 0), (w, d, h), random.choice(cmats), top=M['azotea'])
            y += bh + street
        x += bw + street


blocks(150, 300, -240, 390); blocks(-60, 146, 305, 390, hmin=5, hmax=12); blocks(-60, 95, -240, -160, hmin=6, hmax=22)
blocks(-340, river_x(390) - 82, -240, 390, hmin=8, hmax=28)
mb.box((215, 360, 0), (34, 30, 70), M['ciudad4'], top=M['concreto']); mb.box((215, 360, 70), (26, 22, 12), M['ciudad1'], top=M['concreto'])

# ================================================================ VEHICULOS
veh = G[('veh', 'Vehiculos')]
CARC = [mat('auto_%d' % i, c, .35, .3) for i, c in enumerate([(.85, .85, .86), (.12, .12, .14), (.70, .08, .07), (.15, .30, .60), (.55, .56, .58), (.95, .80, .10)])]


def wheels(c, ang, xs, half_w, r=.34):
    for wx in xs:
        for sy in (-1, 1):
            p = rot_pts([(wx, sy * half_w, 0)], c, ang)[0]
            veh.raw(*CYL8, M['rueda'], (p[0], p[1], r), (r, r, .01))                      # disco (tapa)
            veh.box((p[0], p[1], 0), (2 * r, .24, 2 * r), M['rueda'], ang)


def car(x, y, ang, m=None):
    m = m or random.choice(CARC); c = (x, y, 0)
    low = [(-2.15, -.9, .28), (2.15, -.9, .28), (2.15, .9, .28), (-2.15, .9, .28), (-2.15, -.9, .82), (2.05, -.9, .74), (2.05, .9, .74), (-2.15, .9, .82)]
    cab = [(-1.55, -.84, .82), (.75, -.84, .80), (.75, .84, .80), (-1.55, .84, .82), (-1.15, -.72, 1.38), (.25, -.72, 1.38), (.25, .72, 1.38), (-1.15, .72, 1.38)]
    veh.raw(rot_pts(low, c, ang), BOXF, m); veh.raw(rot_pts(cab, c, ang), BOXF, M['ventana'])
    veh.raw(rot_pts([(-1.12, -.70, 1.38), (.22, -.70, 1.38), (.22, .70, 1.38), (-1.12, .70, 1.38),
                     (-1.12, -.70, 1.42), (.22, -.70, 1.42), (.22, .70, 1.42), (-1.12, .70, 1.42)], c, ang), BOXF, m)
    wheels(c, ang, (-1.35, 1.35), .82)


BUSM = mat('bus_metroplus', (.94, .94, .92), .4); BUSV = mat('bus_franja_verde', (.20, .55, .30), .5)


def bus(x, y, ang):
    veh.box((x, y, .45), (18, 2.55, 2.75), BUSM, ang, top=M['concreto'])
    veh.box((x, y, 1.55), (18.05, 2.6, 1.0), M['ventana'], ang)
    veh.box((x, y, .75), (18.06, 2.61, .35), BUSV, ang)
    wheels((x, y, 0), ang, (-6.5, -1.0, 6.5), 1.2, .5)


for x, d in ((105.5, 1), (109, 1), (112.5, 1), (129.5, -1), (133, -1), (136.5, -1)):
    for y in range(YS, YN):
        if random.random() < .045:
            car(x, y, math.pi / 2 * d)
for y in (-150, -40, 60, 170, 300):
    bus(117.2, y + random.uniform(-10, 10), math.pi / 2); bus(124.3, y + 40 + random.uniform(-10, 10), -math.pi / 2)
for off in (45.5, 49, 52.5, 63.5, 67, 70.5, -46, -50, -54, -58, -62, -66):
    for y in range(-240, 255):
        if random.random() < .04:
            car(river_x(y) + off, y, math.radians(90 + 15.5) if 0 < off < 57 or off < -55 else math.radians(-90 + 15.5))
for x in range(-150, -30):
    if random.random() < .05:
        car(x, 127.5 if random.random() < .5 else 133.5, 0)
LUX = [mat('lujo_%d' % i, c, .2, .85) for i, c in enumerate([(.80, .02, .04), (.04, .04, .05), (.92, .92, .90), (.55, .57, .60), (.05, .12, .35), (.90, .60, .05), (.35, .36, .38)])]
CROMO = mat('cromo', (.85, .86, .88), .15, 1.0)


def sports_car(x, y, ang, m):
    # deportivo de lujo: carroceria baja, capo largo, cabina atras, rines cromados
    c = (x, y, 0)
    body = [(-2.3, -.98, .30), (2.3, -.98, .30), (2.3, .98, .30), (-2.3, .98, .30), (-2.3, -.98, .80), (2.25, -.98, .68), (2.25, .98, .68), (-2.3, .98, .80)]
    hood = [(.3, -.92, .80), (2.2, -.92, .68), (2.2, .92, .68), (.3, .92, .80), (.3, -.92, .92), (2.0, -.92, .74), (2.0, .92, .74), (.3, .92, .92)]
    cab = [(-1.7, -.86, .80), (.6, -.86, .88), (.6, .86, .88), (-1.7, .86, .80), (-1.35, -.70, 1.30), (-.15, -.70, 1.30), (-.15, .70, 1.30), (-1.35, .70, 1.30)]
    roof = [(-1.3, -.66, 1.30), (-.2, -.66, 1.30), (-.2, .66, 1.30), (-1.3, .66, 1.30), (-1.3, -.66, 1.34), (-.2, -.66, 1.34), (-.2, .66, 1.34), (-1.3, .66, 1.34)]
    veh.raw(rot_pts(body, c, ang), BOXF, m); veh.raw(rot_pts(hood, c, ang), BOXF, m)
    veh.raw(rot_pts(cab, c, ang), BOXF, M['ventana']); veh.raw(rot_pts(roof, c, ang), BOXF, m)
    veh.raw(rot_pts([(-2.35, -.6, .55), (-2.3, -.6, .55), (-2.3, .6, .55), (-2.35, .6, .55), (-2.35, -.6, .9), (-2.3, -.6, .9), (-2.3, .6, .9), (-2.35, .6, .9)], c, ang), BOXF, M['negro'])
    for wx in (-1.45, 1.5):
        for sy in (-1, 1):
            p_ = rot_pts([(wx, sy * .92, 0)], c, ang)[0]
            veh.box((p_[0], p_[1], 0), (.72, .28, .72), M['rueda'], ang)
            veh.raw(*CYL12, CROMO, (p_[0] + math.sin(ang) * sy * .02, p_[1] - math.cos(ang) * sy * .02, .36), (.23, .23, .01))


def moto(x, y, ang, m):
    c = (x, y, 0)
    for wx in (-.72, .72):
        p_ = rot_pts([(wx, 0, 0)], c, ang)[0]
        veh.box((p_[0], p_[1], 0), (.64, .14, .64), M['rueda'], ang)
    veh.raw(rot_pts([(-.55, -.2, .45), (.6, -.2, .45), (.6, .2, .45), (-.55, .2, .45), (-.55, -.2, .85), (.6, -.2, .72), (.6, .2, .72), (-.55, .2, .85)], c, ang), BOXF, m)   # tanque y asiento
    veh.raw(rot_pts([(-.2, -.1, .3), (.45, -.1, .3), (.45, .1, .3), (-.2, .1, .3), (-.2, -.1, .5), (.45, -.1, .5), (.45, .1, .5), (-.2, .1, .5)], c, ang), BOXF, CROMO)   # motor
    beam(veh, rot_pts([(.55, -.38, 1.05)], c, ang)[0], rot_pts([(.55, .38, 1.05)], c, ang)[0], .04, CROMO)                                                      # manubrio
    beam(veh, rot_pts([(.5, 0, .72)], c, ang)[0], rot_pts([(.75, 0, .2)], c, ang)[0], .05, CROMO)                                                              # horquilla


# carros: iconos rojos del PDF (posicion y angulo del eje largo, en el mundo)
CARROS_LUJO = [(55.0, 142.2, -63), (54.9, 135.0, -63), (57.1, 136.7, -63), (59.1, 139.9, -63), (51.9, 141.5, -63), (47.7, 142.8, -63),
               (51.1, 136.3, -63), (47.7, 137.6, -63), (46.3, 127.3, -40), (42.9, 126.3, -40), (39.3, 125.7, -40)]
for i, (x, y, a) in enumerate(CARROS_LUJO):
    sports_car(x, y, math.radians(a), LUX[i % len(LUX)])
for i, (x, y) in enumerate(D['carros']):                                                  # motos: iconos 28x14 del PDF, en linea diagonal
    moto(x, y, math.radians(72), LUX[(i + 2) % len(LUX)])
# el tapete/catenarias VIP 10x5 queda al norte de las motos (PDF)
for i in range(16):
    for xx in (49, 67.5, 79, 91.5):
        if random.random() < .7:
            car(xx, 22.6 + i * 5.2, 0)

# ================================================================ PERSONAS (escala)
PC = [mat('persona_%d' % i, c, .7) for i, c in enumerate([(.10, .20, .45), (.80, .12, .12), (.12, .12, .12), (.90, .90, .88), (.20, .45, .25), (.95, .65, .15)])]
SKIN = mat('piel', (.55, .38, .26), .7)
PANT = [mat('pantalon_%d' % i, c, .8) for i, c in enumerate([(.10, .11, .16), (.16, .18, .26), (.22, .20, .18)])]


def person(g, x, y, z):
    mb = G[(g, 'Personas')]
    mb.raw(*CYL6, random.choice(PANT), (x, y, z), (.17, .17, .85), smooth=True)                 # piernas
    mb.raw(*TORSO, random.choice(PC), (x, y, z + .85), (.17, .15, .62), smooth=True)           # torso
    mb.raw(*ICO1, SKIN, (x, y, z + 1.62), (.115, .115, .135), smooth=True)                       # cabeza


def crowd(g, box, n, z, ok=lambda x, y: True):
    k = tries = 0
    while k < n and tries < n * 30:
        tries += 1
        x = random.uniform(box[0], box[2]); y = random.uniform(box[1], box[3])
        if free(x, y) and ok(x, y):
            person(g, x, y, z if not callable(z) else z(x, y)); k += 1


crowd('base', (-5, 98, 95, 151), 330, 0, lambda x, y: not (ux0 < x < ux1 and uy0 < y < uy1))
crowd('base', (0, -118, 46, -24), 160, lambda x, y: ZH_HALL if y > -34.4 else (0 if y < -39.8 else ZH_HALL * (y + 39.8) / 5.4)); crowd('base', (48, -102, 87, 12), 140, 0); crowd('base', (7, 3, 37, 96), 130, lambda x, y: z_blanco(y))
crowd('base', (-29, 170, -21, 290), 0, 0); crowd('base', (46, 216, 76, 290), 50, 0)
crowd('base', (sx0 + 1, sy0, sx1 - 1, sy1), 45, lambda x, y: (Z_GS - Z_MULTI) * min(1, max(0, (y - (sy0 + 6.1)) / (sy1 - (sy0 + 6.1)))))
crowd('sup', (-60, -21, -3, 18), 110, Z_UP); crowd('sup', (-98, 21, 0, 95), 150, Z_UP, lambda x, y: pip((x, y), VERDE) or pip((x, y), VIPV))
crowd('inf', (-60, -21, -10, 18), 60, 0); crowd('inf', (-54, 62, -26, 89), 14, .15, lambda x, y: pip((x, y), COM))
crowd('gs', (PX0 + 1, PY0 + .5, PX1 - 1, 200), 110, Z_GS)
crowd('multi', (mx0 + 1, my0 + 1, mx1 - 1, wy0 - 1), 22, Z_MULTI)
crowd('caja', (cx0 + 1, vy1 + 1, cx1 - 1, cy1 - 1), 55, .02)
if PORTICO:
    crowd('caja', (PORTICO[0] - 3, cy1, PORTICO[2] + 3, PORTICO[3] + 2.5), 14, .02)
crowd('losa', (PX0 + 2, cy1 + 9, PX1 - 2, PY1 - 2), 90, .12, lambda x, y: x > fxw(y) + 1 and not (x > PX1 - 12 and 220 < y < 264) and not (12 < x < 40 and 236 < y < 256))

# construir todas las mallas acumuladas
for (c, name), mbx in list(G.items()):
    mbx.build(name, c)

# ================================================================ PINES NUMERADOS + LEYENDA
PIN_R = 5.4


def pin_outline(Rr, h, n=40):
    beta = math.acos(Rr / h); a0 = -math.pi / 2 + beta; a1 = 1.5 * math.pi - beta
    return [(0, 0)] + [(Rr * math.cos(a0 + (a1 - a0) * i / n), h + Rr * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


LEYENDA = []


def pin(n, nombre, detalle, col, xy, z, grp='base', nivel='Nivel principal', Rr=PIN_R):
    c = 'pins_' + grp
    root = bpy.data.objects.new('Pin_%02d' % n, None); root.location = (xy[0], xy[1], z); COLL[c].objects.link(root)
    if c in PARENT:
        root.parent = ROOT[PARENT[c]]
    root.constraints.new('COPY_ROTATION').target = orient
    h = Rr * 1.85
    body = MB()
    body.prism(pin_outline(Rr + .45, h + .35), -.35, .3, M['blanco'])
    body.prism(pin_outline(Rr, h), -.1, .5, mat('pin_%02d' % n, col, .45))
    body.prism([(Rr * .66 * math.cos(2 * math.pi * i / 32), h + Rr * .66 * math.sin(2 * math.pi * i / 32)) for i in range(32)], .4, .12, M['blanco'])
    ob = body.build('Pin_%02d_cuerpo' % n, c); ob.parent = root; ob.visible_shadow = False
    cu = bpy.data.curves.new('num', 'FONT'); cu.body = str(n); cu.size = Rr * (.95 if n < 10 else .8); cu.font = FONT
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = .04
    t = bpy.data.objects.new('Pin_%02d_num' % n, cu); t.data.materials.append(mat('pin_txt_%02d' % n, tuple(v * .55 for v in col), .5))
    COLL[c].objects.link(t); t.parent = root; t.location = (0, h, .6); t.visible_shadow = False
    LEYENDA.append({'n': n, 'nombre': nombre, 'detalle': detalle, 'color': [round(v, 3) for v in col], 'nivel': nivel,
                    'pos': [round(xy[0], 2), round(xy[1], 2), round(z + (DZ_CONV if grp in ('gs', 'multi', 'caja') else 0), 2)], 'grupo': grp})


CAF, DOR, GRIS = (.42, .25, .12), (.75, .56, .16), (.40, .42, .45)
pc = ((PORTICO[0] + PORTICO[2]) / 2, (PORTICO[1] + PORTICO[3]) / 2) if PORTICO else (ccx, cy1 + 4)
pin(1, 'Ingreso principal · Caja de Madera', 'Pórtico de ingreso 10×6, frente al letrero Yo ♥ Medellín', CAF, pc, 7.5, 'caja', 'Caja · piso 3')
pin(2, 'Registro y taquillas', 'Dentro de la Caja: taquilla General/VIP/Black, counters de registro, acreditación', CAF, (14, 204), 4.5, 'caja', 'Caja · piso 3')
pin(3, 'Salón Multipropósito', 'Zona VIP · 400 px · oficina Grupo Effi', DOR, (30, 167), Z_MULTI + 3.0, 'multi', 'Convenciones · piso 2')
pin(4, 'Gran Salón · Auditorio E-commerce', 'Zona académica · 2.900 px · tarima 20×6', (.58, .46, .34), centroid(GS_SALA), Z_GS + 6, 'gs', 'Convenciones · piso 1')
pin(5, 'Lobby Gran Salón', 'Sala Abierta Convertmate, Zona Black, stands GL', (.20, .20, .22), (12, 174), Z_GS + 5, 'gs', 'Convenciones · piso 1')
pin(6, 'Gradas Plazoleta ↔ Gran Salón', 'Bajan de la Plazoleta Interamericana al piso 1', GRIS, (20, 158.5), 1.0)
pin(7, 'Auditorio UGC', 'Carpa 20×25 · creadores de contenido · 600 px', (.45, .30, .62), UGC_C, RIDGE + 1.5)
pin(8, 'Plazoleta Interamericana', 'Activaciones, exhibición de carros, stands PL', (.62, .42, .68), (52, 121), 9.0)
pin(9, 'Auditorio Comunidades', 'Debajo del Pabellón Verde', (.18, .42, .12), centroid(COM), 4.0, 'inf', 'Nivel inferior')
pin(10, 'Pabellón Verde · Auditorio Effix', 'Zona académica · 2.800 px · tarima 20×8', (.33, .62, .12), (-66, 47), Z_UP + 16.5, 'sup', 'Nivel superior')
pin(11, 'Zona IA', 'Pabellón Verde', (.20, .55, .30), (-13, 84), Z_UP + 16.5, 'sup', 'Nivel superior')
pin(12, 'Zona VIP', 'Entre Azul y Verde · acceso VIP', DOR, (-31, 44), Z_UP + 16.5, 'sup', 'Nivel superior')
pin(13, 'Pabellón Azul', 'Encima del Rojo · Auditorio Prendas Control', (.08, .38, .82), (-32, -1), Z_UP + 13, 'sup', 'Nivel superior')
pin(14, 'Pabellón Rojo · Rematex', 'Debajo del Azul', (.78, .10, .08), (-20, -1), 4.0, 'inf', 'Nivel inferior')
pin(15, 'Hall principal', 'Conecta Blanco, Amarillo, Azul, Rojo y Zona de Comidas · Auditorio Unmerco', (.70, .25, .55), (30, -6), 21.5)
pin(16, 'Pabellón Blanco', 'Stands B · Sala abierta 22×6', (.50, .52, .55), (22, 52), 21.5)
pin(17, 'Pabellón Amarillo', 'Stands AM', (.88, .64, .02), (68, -18), 22.5)
pin(18, 'Auditorio Marketing', 'Pabellón Amarillo · 2.500 px · tarima 20×6', (.80, .55, .02), (68, -80), 22.5)
pin(19, 'Zona de Comidas', 'Stands T · mesas', (.93, .48, .10), (18, -72), 6)
pin(20, 'Ingreso con escarapela · oriente', 'Acceso a la Plazoleta por el cerramiento, techo truss 8×4 (PDF)', (.10, .10, .12), TRUSS_ING[1], 7.0)
pin(21, 'Ingreso con escarapela · occidente', 'Acceso a la Plazoleta por el cerramiento, techo truss 8×4 (PDF)', (.10, .10, .12), TRUSS_ING[0], 7.0)
pin(23, 'Grupo Effi · piso 2 del Hall', 'Mezanine del Hall principal: todas las marcas de Grupo Effi', (.05, .30, .68), (20, -17.5), Z_MEZ + 13.5, 'sup', 'Nivel superior')
pin(22, 'Zona Black · uso exclusivo', 'Comisiones, Sala de Negocios, Sala de Prensa y Sala VIP (edificio de Convenciones)', (.08, .08, .09), (36.4, 226.0), Z_GS + 5, 'gs', 'Convenciones · piso 1')
(R / 'leyenda_v04.json').write_text(json.dumps(LEYENDA, ensure_ascii=False, indent=1), encoding='utf8')

# ---------------------------------------------------------------- rotulos de contexto (vias, rio, hitos)


def rounded_rect(w, h, r, seg=6):
    r = min(r, h / 2, w / 2); pts = []
    for qx, qy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg); pts.append((qx + r * math.cos(a), qy + r * math.sin(a)))
    return pts


def label(text, pos, z, col, size=3.0):
    root = empty('Rotulo_' + text, (pos[0], pos[1], z), 'ctx')
    root.constraints.new('COPY_ROTATION').target = orient
    cu = bpy.data.curves.new('lbl', 'FONT'); cu.body = text; cu.size = size; cu.font = FONT
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = .05
    t = bpy.data.objects.new('Rotulo_txt_' + text, cu); t.data.materials.append(M['blanco'])
    COLL['ctx'].objects.link(t); t.parent = root; t.location = (0, 0, .25); t.visible_shadow = False
    bpy.context.view_layer.update()
    w = t.dimensions.x + size * 1.3; h = size * 1.55
    pb = MB(); pb.prism(rounded_rect(w, h, h / 2), -.15, .35, mat('rotulo_' + text, col, .5))
    pb.prism(rounded_rect(w + size * .25, h + size * .25, h / 2 + size * .12), -.3, .14, M['blanco'])
    o = pb.build('Rotulo_placa_' + text, 'ctx'); o.parent = root; o.visible_shadow = False


label('METROPLÚS · ESTACIÓN PLAZA MAYOR', (121, 170), 12, (.15, .45, .25))
label('AV. DEL FERROCARRIL', (121, -70), 9, (.25, .25, .28))
label('RÍO MEDELLÍN', (river_x(40), 40), 6, (.12, .40, .50), 3.2)
label('AV. REGIONAL', (river_x(-90) + 58, -90), 6, (.25, .25, .28))
label('TEATRO METROPOLITANO', (-124, 178), 30, (.55, .25, .15), 3.2)
label('PARQUES DEL RÍO', (river_x(290) + 60, 290), 22, (.20, .50, .25), 3.0)
flat_text('CARRERA 57', (-60, 235, .2), 2.2, M['blanco'], 'vias')
flat_text('CARRERA 57', (-46, 235, .2), 2.2, M['blanco'], 'vias')
for _yt in range(176, 296, 13):
    tree(-36 + random.uniform(-2, 2), _yt, random.uniform(.8, 1.15), force=True); tree(-53, _yt + 5, random.uniform(.6, .9), force=True)
    tree(-72 + random.uniform(-3, 3), _yt + 3, random.uniform(.8, 1.1), force=True)
for _i, (_xc, _yc, _an) in enumerate(((-58, 190, math.pi / 2), (-62, 248, math.pi / 2), (-44, 215, -math.pi / 2), (-48, 270, -math.pi / 2))):
    car(_xc, _yc, _an)
label('CALLE 41', (-95, 130.5), 5, (.25, .25, .28), 2.6)

# ---------------------------------------------------------------- guias punteadas de los niveles flotantes
gd = MB()


def vguide(x, y, z0, z1):
    z = z0
    while z < z1:
        gd.raw(*CYL6, M['guia'], (x, y, z), (.12, .12, min(1.0, z1 - z))); z += 2.0


for x, y in rect(ax0, ay0, ax1, ay1):
    vguide(x, y, H_LOW, Z_UP + LIFT['sup'])
for x, y in (VERDE[0], VERDE[15], VERDE[16]):
    vguide(x, y, 0, Z_UP + LIFT['sup'])
for x, y in rect(cx0, cy0, cx1, cy1):
    vguide(x, y, Z_GS if PX0 < x < PX1 and y > PY0 else 0, LIFT['shell'] + BOX0)
for x, y in rect(mx0, my0, mx1, my1):
    vguide(x, y, Z_GS, Z_MULTI + LIFT['multi'])
gd.build('Guias_niveles', 'guias')

# ================================================================ REFERENCIA (calco del PDF, oculto en render)
for name in ('plano_tecnico_metrico', 'gran_salon_metrico'):
    bb = REF[name]
    img = bpy.data.images.load(str(R / 'referencias' / (name + '.png')))
    m = bpy.data.materials.new('ref_' + name); m.use_nodes = True
    tx = m.node_tree.nodes.new('ShaderNodeTexImage'); tx.image = img
    m.node_tree.links.new(tx.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    (x0, x1), (y0, y1) = bb['X'], bb['Y']
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, q in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = q
    me.materials.append(m)
    ob = bpy.data.objects.new('Calco_' + name, me); ob.location.z = .35 if name.startswith('plano') else Z_GS + .2
    COLL['ref'].objects.link(ob); ob.hide_render = True

# ================================================================ LUZ, MUNDO, CAMARAS
world = bpy.data.worlds.new('Cielo'); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn['Background']; bg.inputs[1].default_value = 1.0
tcw = wn.new('ShaderNodeTexCoord'); sep = wn.new('ShaderNodeSeparateXYZ'); ramp = wn.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .0; ramp.color_ramp.elements[0].color = (.80, .86, .92, 1)      # horizonte
ramp.color_ramp.elements[1].position = .55; ramp.color_ramp.elements[1].color = (.22, .45, .85, 1)     # cenit
e = ramp.color_ramp.elements.new(.12); e.color = (.55, .72, .93, 1)
wl.new(tcw.outputs['Generated'], sep.inputs[0]); wl.new(sep.outputs['Z'], ramp.inputs['Fac']); wl.new(ramp.outputs['Color'], bg.inputs[0])
sun = bpy.data.objects.new('Sol', bpy.data.lights.new('Sol', 'SUN'))
sun.data.energy = 3.6; sun.data.angle = math.radians(1.5); sun.data.color = (1, .95, .87)
sun.rotation_euler = (math.radians(48), math.radians(-8), math.radians(-55)); scene.collection.objects.link(sun)


def cam_ortho(name, target, az, el, scale, dist=1200):
    c = bpy.data.cameras.new(name); c.type = 'ORTHO'; c.ortho_scale = scale; c.clip_end = 6000
    o = bpy.data.objects.new(name, c); scene.collection.objects.link(o)
    a, e = math.radians(az), math.radians(el); T = Vector(target)
    o.location = T + dist * Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    o.rotation_euler = (T - o.location).to_track_quat('-Z', 'Y').to_euler()
    return o


def cam_persp(name, loc, target, lens):
    c = bpy.data.cameras.new(name); c.lens = lens; c.clip_end = 4000
    o = bpy.data.objects.new(name, c); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
    return o


# Vista principal desde el oriente (lado Metroplus): norte a la derecha como en el PDF; asi los niveles
# flotantes solo tapan lo que queda al occidente (zonas sin recintos).
cam_ortho('Cam_Iso', (-14, 72, 24), 72, 36, 400)
cam_ortho('Cam_Niveles_Caja', (6, 200, 26), 72, 30, 190)
cam_ortho('Cam_Niveles_Azul_Verde', (-45, 35, 22), 72, 34, 230)
cp_ = cam_ortho('Cam_Planta', (-12, 78, 0), 0, 90, 440); cp_.rotation_euler = (0, 0, math.radians(90))
cr = cam_ortho('Cam_Planta_Caja', (ccx + 4, ccy + 2, 0), 0, 90, 66); cr.rotation_euler = (0, 0, math.radians(90))
cg_ = cam_ortho('Cam_Planta_GS', (3, 188, 0), 0, 90, 100); cg_.rotation_euler = (0, 0, math.radians(90))   # lobby del Gran Salon + gradas, norte a la derecha
cam_persp('Cam_Ingreso_Caja', (44, 282, 7.5), (8, 212, 10.5), 22)       # desde el norte: letrero al frente, Teatro a la derecha
cam_persp('Cam_UGC', (UGC_C[0] + 34, UGC_C[1] + 17, 7.5), (UGC_C[0] - 2, UGC_C[1], 5.5), 20)
cam_persp('Cam_Gradas', (70, 150, 16), (0, 176, -2), 24)
cam_persp('Cam_Fachada_GS', (-10, 157.5, -2.5), (4, 172, -3), 18)
cam_persp('Cam_Carros', (74, 118, 6), (49, 134, .8), 26)
cam_persp('Cam_Portico', (11, 236, 2.0), (11, 222, 3.0), 28)      # frente al portico LED del ingreso
cam_persp('Cam_Verde_Tarima', (-40, 80, 7.5), (-84, 46, 7.0), 24)   # Auditorio Effix (Verde) hacia la tarima   # desde la plazoleta hacia las graderias y la fachada del Gran Salon                 # gradas de la plazoleta hacia el Gran Salon / Caja
scene.camera = bpy.data.objects['Cam_Iso']; orient.rotation_euler = scene.camera.rotation_euler

scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 2400; scene.render.resolution_y = 1680
scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = -0.2
for k, v in LIFT.items():
    scene['LIFT_' + k] = v
for k, c in COLL.items():            # grupo de cada objeto (lo usa el mapa web para prender/apagar niveles)
    for ob in c.objects:
        ob['grupo'] = k
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print('triangulos:', tris)
_raices = set(ROOT.values())
for _c in ('gs', 'multi', 'caja', 'shell', 'losa', 'huella', 'pins_gs', 'pins_multi', 'pins_caja'):
    for _o in COLL[_c].objects:
        if _o not in _raices and (_o.parent is None or _o.parent in _raices):
            _o.location.z += DZ_CONV
for _n in ('Foso_Gran_Salon_y_gradas', 'Talud_pasillo_exterior'):
    bpy.data.objects[_n].location.z += DZ_CONV
bpy.ops.wm.save_as_mainfile(filepath=str(R / 'Plaza_Mayor_mapa_v04.blend'))
print('OK guardado', len(bpy.data.objects), 'objetos;', len(LEYENDA), 'pines')
