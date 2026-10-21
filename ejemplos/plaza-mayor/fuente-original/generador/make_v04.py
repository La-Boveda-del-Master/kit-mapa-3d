"""Genera construir_mapa_v04.py a partir de v03: UVs + texturas, vegetacion, vehiculos, personas, cielo, datos para web."""
import pathlib, re
R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
s = (R / 'construir_mapa_v03.py').read_text(encoding='utf8')


def rep(a, b, count=1):
    global s
    assert a in s, 'NO ENCONTRADO: ' + a[:80]
    s = s.replace(a, b) if count == 0 else s.replace(a, b, count)


def block(start, end, new):
    """Reemplaza desde el marcador start (incluido) hasta end (excluido)."""
    global s
    i0 = s.index(start); i1 = s.index(end, i0)
    s = s[:i0] + new + s[i1:]


rep('"""Mapa 3D de Feria Effix 2026 en Plaza Mayor (v03)', '"""Mapa 3D de Feria Effix 2026 en Plaza Mayor (v04: acabados con texturas, base del mapa web y del video)')
rep("Uso: blender -b --factory-startup --python construir_mapa_v03.py", "Uso: python generar_texturas.py ; blender -b --factory-startup --python construir_mapa_v04.py")
rep("import bpy, bmesh, json, math, random, pathlib", "import bpy, bmesh, json, math, random, pathlib\nimport numpy as np")

# ---------------------------------------------------------------- materiales con textura
rep("def noise_mat(name, c1, c2, scale=40., rough=.8):", '''TEX = R / 'texturas'
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


def noise_mat(name, c1, c2, scale=40., rough=.8):''')

block("M = {\n    'suelo'", "    'stand_lado'", '''M = {
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
''')
rep("    'ciudad1': mat('edif_ciudad_1', (.86, .84, .80), .8), 'ciudad2': mat('edif_ciudad_2', (.76, .72, .66), .8),\n    'ciudad3': mat('edif_ciudad_3', (.70, .45, .32), .8), 'ciudad4': mat('edif_ciudad_4', (.90, .90, .88), .8),",
    "    'ciudad1': tex_mat('edif_ciudad_1', 'fachada_1', 9, .8, avg=(.80, .78, .74)), 'ciudad2': tex_mat('edif_ciudad_2', 'fachada_2', 9, .8, avg=(.70, .67, .62)),\n"
    "    'ciudad3': tex_mat('edif_ciudad_3', 'fachada_3', 9, .8, avg=(.64, .44, .34)), 'ciudad4': tex_mat('edif_ciudad_4', 'fachada_4', 9, .8, avg=(.84, .84, .82)),\n"
    "    'azotea': mat('azotea', (.62, .61, .58), .9), 'rueda': mat('rueda', (.05, .05, .06), .8),")
rep("for k, (c, f, s) in PAV.items():\n    mat('muro_' + k, c, .6); mat('piso_' + k, f, .7); mat('stand_' + k, s, .55)",
    '''TINTE = {'Amarillo': 'amarillo', 'Blanco': 'blanco', 'Azul': 'azul', 'Verde': 'verde', 'Rojo': 'rojo', 'Hall': 'hall', 'GS': 'gs', 'Multi': 'multi'}
for k, (c, f, s) in PAV.items():
    if k in TINTE:      # fachada de panel metalico nervado y cubierta de junta alzada, en el color del pabellon
        tex_mat('muro_' + k, 'panel_' + TINTE[k], 4.8, .55, .25, normal='panel_n', nstr=.5, avg=c)
        tex_mat('techo_' + k, 'techo_' + TINTE[k], 3.6, .4, .45, normal='techo_n', avg=c)
    else:
        mat('muro_' + k, c, .6)
    mat('piso_' + k, f, .7); mat('stand_' + k, s, .55)
tex_mat('muro_Verde_bajo', 'panel_verde_osc', 4.8, .6, .2, normal='panel_n', nstr=.5, avg=(.30, .52, .12))
tex_mat('madera_caja', 'madera', 2.0, .7, avg=(.30, .15, .07))''')
rep("mat('muro_Verde_bajo', (.30, .52, .12), .6)", "MATS['muro_Verde_bajo']")
rep("madera_t = [mat('madera_caja_%d' % i, c, .75) for i, c in enumerate([(.30, .15, .07), (.26, .13, .06), (.34, .18, .09)])]",
    "madera_t = [MATS['madera_caja']]")
rep("            G[(ext, 'Cubiertas')].prism(poly, z0 + h_total, .6, MATS['muro_' + key])",
    "            G[(ext, 'Cubiertas')].prism(poly, z0 + h_total, .6, MATS.get('techo_' + key, MATS['muro_' + key]), side=MATS['muro_' + key])")

# ---------------------------------------------------------------- MB: caras suaves y UVs en metros
rep("    def __init__(s):\n        s.v, s.f, s.m, s.mats = [], [], [], []", "    def __init__(s):\n        s.v, s.f, s.m, s.mats, s.sm = [], [], [], [], []")
rep("        s.f.append(tuple(b + i for i in reversed(range(n)))); s.m.append(s.mi(m))\n        s.f.append(tuple(b + n + i for i in range(n))); s.m.append(s.mi(top or m))\n        for i in range(n):\n            j = (i + 1) % n\n            s.f.append((b + i, b + j, b + n + j, b + n + i)); s.m.append(s.mi(side or m))",
    "        s.f.append(tuple(b + i for i in reversed(range(n)))); s.m.append(s.mi(m))\n        s.f.append(tuple(b + n + i for i in range(n))); s.m.append(s.mi(top or m))\n        for i in range(n):\n            j = (i + 1) % n\n            s.f.append((b + i, b + j, b + n + j, b + n + i)); s.m.append(s.mi(side or m))\n        s.sm += [False] * (n + 2)")
rep("    def raw(s, verts, faces, m, off=(0, 0, 0), sc=(1, 1, 1)):\n        b = len(s.v)\n        s.v += [(off[0] + x * sc[0], off[1] + y * sc[1], off[2] + z * sc[2]) for x, y, z in verts]\n        for f in faces:\n            s.f.append(tuple(b + i for i in f)); s.m.append(s.mi(m))",
    "    def raw(s, verts, faces, m, off=(0, 0, 0), sc=(1, 1, 1), smooth=False):\n        b = len(s.v)\n        s.v += [(off[0] + x * sc[0], off[1] + y * sc[1], off[2] + z * sc[2]) for x, y, z in verts]\n        for f in faces:\n            s.f.append(tuple(b + i for i in f)); s.m.append(s.mi(m)); s.sm.append(smooth)")
rep("        me.polygons.foreach_set('material_index', s.m)\n        for m in s.mats:\n            me.materials.append(m)\n        me.update()",
    '''        me.polygons.foreach_set('material_index', s.m)
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
        uvl.data.foreach_set('uv', np.column_stack((u / pt, v / pt)).astype(np.float32).ravel())''')
rep("ICO1, ICO2, CYL6, CYL8, CYL12 = ico(1), ico(2), cyl(6), cyl(8), cyl(12)", '''ICO1, ICO2, ICO3, CYL6, CYL8, CYL12 = ico(1), ico(2), ico(3), cyl(6), cyl(8), cyl(12)


def cone(n, r_top):
    """Tronco de cono (radio 1 abajo, r_top arriba, alto 1)."""
    v = [(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z) for z, r in ((0, 1), (1, r_top)) for i in range(n)]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return v, f


CONE6, TORSO = cone(6, .55), cone(6, 1.25)


def rot_pts(pts, c, ang):
    co, si = math.cos(ang), math.sin(ang)
    return [(c[0] + x * co - y * si, c[1] + x * si + y * co, c[2] + z) for x, y, z in pts]


BOXF = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]''')

# ---------------------------------------------------------------- vegetacion mas natural
block("def tree(x, y, s=1.0, palm=False, force=False):", "def tree_line(", '''def tree(x, y, s=1.0, palm=False, force=False):
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


''')

# ---------------------------------------------------------------- vehiculos con forma (cabina, ruedas)
block("def car(x, y, ang, m=None):", "for x, d in ((105.5, 1), (109, 1)", '''def wheels(c, ang, xs, half_w, r=.34):
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


''')

# ---------------------------------------------------------------- personas con forma
rep("    mb.raw(*CYL6, random.choice(PC), (x, y, z), (.24, .24, 1.35)); mb.raw(*ICO1, SKIN, (x, y, z + 1.55), (.17, .17, .2))",
    "    mb.raw(*CYL6, random.choice(PANT), (x, y, z), (.17, .17, .85), smooth=True)                 # piernas\n"
    "    mb.raw(*TORSO, random.choice(PC), (x, y, z + .85), (.17, .15, .62), smooth=True)           # torso\n"
    "    mb.raw(*ICO1, SKIN, (x, y, z + 1.62), (.115, .115, .135), smooth=True)                       # cabeza")
rep("SKIN = mat('piel', (.55, .38, .26), .7)", "SKIN = mat('piel', (.55, .38, .26), .7)\nPANT = [mat('pantalon_%d' % i, c, .8) for i, c in enumerate([(.10, .11, .16), (.16, .18, .26), (.22, .20, .18)])]")

# azoteas de la ciudad
rep("mb.box((x + 1 + sx * (bw / 2) + w / 2, y + 1 + sy * (bh / 2) + d / 2, 0), (w, d, h), random.choice(cmats), top=M['concreto'])",
    "mb.box((x + 1 + sx * (bw / 2) + w / 2, y + 1 + sy * (bh / 2) + d / 2, 0), (w, d, h), random.choice(cmats), top=M['azotea'])")

# ---------------------------------------------------------------- pines con posicion (para el mapa web)
rep("    LEYENDA.append({'n': n, 'nombre': nombre, 'detalle': detalle, 'color': [round(v, 3) for v in col], 'nivel': nivel})",
    "    LEYENDA.append({'n': n, 'nombre': nombre, 'detalle': detalle, 'color': [round(v, 3) for v in col], 'nivel': nivel,\n"
    "                    'pos': [round(xy[0], 2), round(xy[1], 2), round(z, 2)], 'grupo': grp})")
rep("(R / 'leyenda_v03.json')", "(R / 'leyenda_v04.json')")

# ---------------------------------------------------------------- cielo con degradado y luz mas natural
block("world = bpy.data.worlds.new('Cielo')", "sun = bpy.data.objects.new('Sol'", '''world = bpy.data.worlds.new('Cielo'); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn['Background']; bg.inputs[1].default_value = 1.0
tcw = wn.new('ShaderNodeTexCoord'); sep = wn.new('ShaderNodeSeparateXYZ'); ramp = wn.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .0; ramp.color_ramp.elements[0].color = (.80, .86, .92, 1)      # horizonte
ramp.color_ramp.elements[1].position = .55; ramp.color_ramp.elements[1].color = (.22, .45, .85, 1)     # cenit
e = ramp.color_ramp.elements.new(.12); e.color = (.55, .72, .93, 1)
wl.new(tcw.outputs['Generated'], sep.inputs[0]); wl.new(sep.outputs['Z'], ramp.inputs['Fac']); wl.new(ramp.outputs['Color'], bg.inputs[0])
''')
rep("sun.data.energy = 3.4; sun.data.angle = math.radians(3); sun.data.color = (1, .96, .9)",
    "sun.data.energy = 3.6; sun.data.angle = math.radians(1.5); sun.data.color = (1, .95, .87)")
rep("sun.rotation_euler = (math.radians(38), math.radians(-22), math.radians(-40))", "sun.rotation_euler = (math.radians(48), math.radians(-8), math.radians(-55))")
rep("scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = -0.1",
    "scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = -0.2")
rep("bpy.ops.wm.save_as_mainfile(filepath=str(R / 'Plaza_Mayor_mapa_v03.blend'))",
    "for k, c in COLL.items():            # grupo de cada objeto (lo usa el mapa web para prender/apagar niveles)\n    for ob in c.objects:\n        ob['grupo'] = k\n"
    "tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')\nprint('triangulos:', tris)\n"
    "bpy.ops.wm.save_as_mainfile(filepath=str(R / 'Plaza_Mayor_mapa_v04.blend'))")

# ================= ajustes segun el recorrido 360 real (materiales y entorno)
rep("tex_mat('madera_caja', 'madera', 2.0, .7, avg=(.30, .15, .07))",
    "tex_mat('madera_caja', 'madera', 2.0, .5, .35, avg=(.17, .12, .09))\ntex_mat('fachada_pab', 'fachada_pab', 12, .45, .1, avg=(.62, .64, .66))\ntex_mat('solar', 'solar', 8, .25, .5, avg=(.10, .14, .26))")
rep("        G[(ext, 'Muros_altos')].walls(poly, z0 + low_h, h_total - low_h, t, MATS['muro_' + key])",
    "        G[(ext, 'Muros_altos')].walls(poly, z0 + low_h, h_total - low_h, t, MATS['fachada_pab'] if key in ('Amarillo', 'Blanco', 'Azul', 'Verde', 'Hall') else MATS['muro_' + key])")
rep("G[(ext, 'Cubiertas')].prism(poly, z0 + h_total, .6, MATS.get('techo_' + key, MATS['muro_' + key]), side=MATS['muro_' + key])",
    "G[(ext, 'Cubiertas')].prism(poly, z0 + h_total, 1.5, MATS.get('techo_' + key, MATS['muro_' + key]), side=MATS['muro_' + key])   # cornisa del color del pabellon")
rep("mb.prism(rect(62, 262, 94, 292), .02, .5, M['cesped'])", "mb.prism(rect(47, 169, 93, 212), .02, .5, M['cesped'])                       # jardin de bambu al oriente de la Caja (recorrido 360)")
rep("for _ in range(18):\n    tree(random.uniform(64, 92), random.uniform(264, 290), random.uniform(.5, .7), palm=True)",
    "for _ in range(46):                                        # jardin de bambu: masa densa y alta\n    tree(random.uniform(49, 91), random.uniform(171, 210), random.uniform(.75, 1.1), force=True)\nfor _ in range(10):\n    tree(random.uniform(49, 91), random.uniform(171, 210), random.uniform(.6, .8), palm=True, force=True)")
rep("tree_line((-62, 168), (-62, 292), 8); tree_line((95.5, 170), (95.5, 292), 8)", "tree_line((-62, 168), (-62, 292), 8)")
rep("crowd('base', (-55, 170, -33, 290), 40, 0); crowd('base', (46, 170, 94, 258), 60, 0)", "crowd('base', (-55, 170, -33, 290), 40, 0); crowd('base', (46, 216, 76, 290), 50, 0)")
rep("for x, y in PLANTERS:\n    mb.raw(*CYL12, M['arenisca'], (x, y, 0), (2.2, 2.2, .55)); mb.raw(*CYL12, M['cesped'], (x, y, .55), (1.9, 1.9, .02))",
    "for x, y in PLANTERS:\n    mb.raw(*CYL12, M['arenisca'], (x, y, 0), (2.2, 2.2, .55)); mb.raw(*CYL12, M['cesped'], (x, y, .55), (1.9, 1.9, .02))\n    mb.raw(*ICO1, M['copa2'], (x, y, .75), (1.75, 1.75, .55), smooth=True)                       # arbustos")
rep("mb = G[('entorno', 'Ciudad')]", """# edificio de servicios de Plaza Mayor (piedra, cubierta con paneles solares) entre la plaza de la Caja y la Av. Ferrocarril
mb.prism(rect(80, 216, 95, 300), 0, 11, M['arenisca'], top=MATS['solar'])
mb.prism(rect(79.6, 216, 80, 300), 3.2, 3.0, M['vidrio'])
mb = G[('entorno', 'Ciudad')]""")

# ================= la vidriera de la Caja va en el perimetro (plano de Registro): taquilla y registro quedan ADENTRO
rep("BOX0, BOX1, R_IN = 7.2, 24.0, 3.2", "BOX0, BOX1, R_IN = 7.2, 24.0, 0.9")
rep("        cj.prism(rect(x1, y0, x1 + 3.2, y1), .02, 2.8, M['efx_n'])", "        cj.prism(rect(x1, y0, x1 + 2.2, y1), .02, 2.8, M['efx_n'])")
rep("        cj.prism(rect(x1 - 1.6, y0 - .4, x1 + 3.4, y1 + .4), 2.8, .3, M['efx_r'])", "        cj.prism(rect(x1 - 1.6, y0 - .4, x1 + 2.3, y1 + .4), 2.8, .3, M['efx_r'])")
rep("            beam(sh, base, (top[0] + sgn * 2.2 * dx, top[1] + sgn * 2.2 * dy, BOX0), .32, M['acero'])",
    "            beam(sh, (top[0], top[1], 0), (top[0] + sgn * 2.2 * dx, top[1] + sgn * 2.2 * dy, BOX0), .32, M['acero'])   # columnas en V por fuera del vidrio")

# ================= alturas del plano oficial de Plaza Mayor y materiales interiores del recorrido 360
rep("Z_UP, H_LOW = 7.5, 7.0            # piso del nivel superior / altura libre del nivel inferior",
    "Z_UP, H_LOW = 5.6, 5.2            # Rojo h libre 4.5 m (plano oficial) + entrepiso; el Azul (h 4.7) va encima")
rep("pavilion(E['Amarillo_A'], 0, 13, 'Amarillo', 'base', 'ext_base')\npavilion(E['Amarillo_B'], 0, 13, 'Amarillo', 'base', 'ext_base')",
    "pavilion(E['Amarillo_A'], 0, 11.5, 'Amarillo', 'base', 'ext_base')     # h 10.7 m (plano oficial) + cubierta\npavilion(E['Amarillo_B'], 0, 11.5, 'Amarillo', 'base', 'ext_base')")
rep("pavilion(E['Blanco'], 0, 12, 'Blanco', 'base', 'ext_base')", "pavilion(E['Blanco'], 0, 10.8, 'Blanco', 'base', 'ext_base')         # h 10.05 m")
rep("pavilion(AZUL, Z_UP, 8, 'Azul', 'sup', 'ext_sup')\npavilion(VERDE, Z_UP, 8, 'Verde', 'sup', 'ext_sup')",
    "pavilion(AZUL, Z_UP, 5.4, 'Azul', 'sup', 'ext_sup')                   # h 4.7 m\npavilion(VERDE, Z_UP, 13.3 - Z_UP + .6, 'Verde', 'sup', 'ext_sup')   # h total 13.3 m desde el suelo")
rep("    G[(grp, 'Pisos')].prism(poly, z0 - .45 if z0 > .1 else z0 - .25, .5 if z0 > .1 else .3, MATS['piso_' + key])",
    "    G[(grp, 'Pisos')].prism(poly, z0 - .45 if z0 > .1 else z0 - .25, .5 if z0 > .1 else .3, MATS.get('int_' + key, MATS['piso_' + key]))")
rep("tex_mat('madera_caja', 'madera', 2.0, .5, .35, avg=(.17, .12, .09))",
    "tex_mat('madera_caja', 'madera', 2.0, .5, .35, avg=(.17, .12, .09))\n"
    "# pisos interiores reales (recorrido 360): concreto pulido en pabellones, piedra pulida en lobbies, alfombra en Gran Salon y comisiones\n"
    "for _k in ('Amarillo', 'Blanco', 'Azul', 'Rojo', 'Verde'):\n"
    "    tex_mat('int_' + _k, 'concreto_pulido', 6, .35, .05, avg=(.60, .60, .60))\n"
    "tex_mat('int_Hall', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50)); tex_mat('int_Caja', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50))\n"
    "tex_mat('int_Multi', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50)); tex_mat('int_GS', 'piedra_pulida', 4, .25, .05, avg=(.55, .56, .50))\n"
    "tex_mat('alfombra_gs', 'alfombra', 3, .95, avg=(.42, .46, .52)); tex_mat('madera_clara', 'madera_clara', 3, .6, avg=(.70, .55, .35))")
rep("gsm.walls(ccw(GS_SALA), Z_GS, 4.5, .4, MATS['muro_Caja'])",
    "gsm.walls(ccw(GS_SALA), Z_GS, 4.5, .4, MATS['madera_clara'])                     # muros de madera clara del auditorio\n"
    "G[('gs', 'Pisos')].prism(ccw(GS_SALA), Z_GS + .01, .08, MATS['alfombra_gs'])         # alfombra gris azulada")
rep("pin(21, 'Ingreso / salida Plazoleta', 'Techo truss 8×4 (costado Verde)', (.10, .10, .12), TRUSS_ING[0], 6.5)",
    "pin(21, 'Ingreso / salida Plazoleta', 'Techo truss 8×4 (costado Verde)', (.10, .10, .12), TRUSS_ING[0], 6.5)\n"
    "pin(22, 'Zona Black · uso exclusivo', 'Comisiones, Sala de Negocios, Sala de Prensa y Sala VIP (edificio de Convenciones)', (.08, .08, .09), (33.0, 178.4), Z_GS + 5, 'gs', 'Convenciones · piso 1')")

rep("(.20, .20, .22), (37, 181), Z_GS + 5, 'gs', 'Convenciones · piso 1')", "(.20, .20, .22), (12, 174), Z_GS + 5, 'gs', 'Convenciones · piso 1')")

# ================= Plazoleta segun el fotomontaje oficial de Effix: pabellon UGC en trimalla 18x25 (lado largo N-S), tapetes, cerramiento, torres, mesas
block("# carpa del Auditorio UGC (carpa pabellon 20x25, aforo 600): truss + lona a dos aguas, centrada en las sillas del plano",
      "# ================================================================ VEGETACION", """# Pabellon Auditorio UGC: trimalla (cubierta plana en malla espacial) 18 x 25 m, 6 patas con ecopesos, girada con el lado largo
# norte-sur como en el fotomontaje de Effix; piso en cesped sintetico (tapete 17)
ug = [s for s in D['sillas'] if s[3] == 'main' and -25 < s[0] < 20 and 120 < s[1] < 152]
UGC_C = (sum(s[0] for s in ug) / len(ug), sum(s[1] for s in ug) / len(ug))
UW, UL, EAVE, RIDGE = 18.0, 25.0, 6.5, 8.0
ux0, ux1, uy0, uy1 = UGC_C[0] - UW / 2, UGC_C[0] + UW / 2, UGC_C[1] - UL / 2, UGC_C[1] + UL / 2
cg = G[('mob', 'Carpa_UGC_estructura')]
for x, y in ((ux0, uy0), (ux0, UGC_C[1]), (ux0, uy1), (ux1, uy0), (ux1, UGC_C[1]), (ux1, uy1)):          # 6 patas en trimalla
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
CERR = [(-30, 97), (97, 97), (97, 112), (84, 112), (84, 148), (-5, 160), (-30, 160)]                       # perimetro de la plazoleta (aprox.)
malla = mat('malla_brandeada', (.10, .10, .11), .8, alpha=.75)
for i in range(len(CERR)):
    a_, b_ = CERR[i], CERR[(i + 1) % len(CERR)]
    if a_[1] == 97 and b_[1] == 97:                                                                        # el frente sur tiene los dos ingresos
        for seg_ in (((-30, 97), (-19, 97)), ((-9, 97), (73, 97)), ((83, 97), (97, 97))):
            mb.seg(*seg_, .05, .2, 1.8, malla)
        continue
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

""")

# ================= cerramiento sin pasar por las graderias + 2 ingresos con escarapela (truss 8x4 del PDF: occidente y oriente)
rep("TRUSS_ING = ((-14, 101), (78, 101))\nfor x, y in TRUSS_ING:                                   # ingresos techo truss 8x4 (PDF)\n    for dx in (-4, 4):\n        truss(mb, (x + dx, y, 0), (x + dx, y, 5), .4, m=M['efx_n'])\n    truss(mb, (x - 4, y, 5), (x + 4, y, 5), .4, m=M['efx_n'])",
    "TRUSS_ING = ((-30, 125), (84, 120))                     # ingresos con escarapela: techo truss 8x4 sobre el cerramiento (PDF)\n"
    "for x, y in TRUSS_ING:\n"
    "    for dy in (-4, 4):\n"
    "        truss(mb, (x, y + dy, 0), (x, y + dy, 5), .4, m=M['efx_n'])\n"
    "    truss(mb, (x, y - 4, 5), (x, y + 4, 5), .4, m=M['efx_n'])\n"
    "    mb.box((x, y, 5.2), (4.0, 8.8, .15), M['efx_n']); mb.box((x, y, 5.35), (4.1, 8.9, .6), M['efx_r'])          # techo 8x4 y banda roja\n"
    "    for dy in (-2.6, 0, 2.6):                                                                                   # 3 carriles de control\n"
    "        mb.box((x, y + dy, 0), (.25, .7, 2.2), M['poste'])\n"
    "    wall_text('INGRESO CON ESCARAPELA', (x + (2.1 if x > 0 else -2.1), y, 4.6), .55, M['blanco'], 'mob', math.pi / 2 if x > 0 else -math.pi / 2)")
rep("CERR = [(-30, 97), (97, 97), (97, 112), (84, 112), (84, 148), (-5, 160), (-30, 160)]                       # perimetro de la plazoleta (aprox.)",
    "# perimetro de la plazoleta: se detiene en las graderias (X -29.6..35.9, Y 153.6) y deja los dos vanos de 8 m de los ingresos\n"
    "CERR = [((-30, 97), (97, 97)), ((97, 97), (97, 112)), ((97, 112), (84, 112)), ((84, 112), (84, 116)), ((84, 124), (84, 148)),\n"
    "        ((84, 148), (36, 150)), ((-30, 150), (-30, 129)), ((-30, 121), (-30, 97))]")
rep("for i in range(len(CERR)):\n    a_, b_ = CERR[i], CERR[(i + 1) % len(CERR)]\n    if a_[1] == 97 and b_[1] == 97:                                                                        # el frente sur tiene los dos ingresos\n        for seg_ in (((-30, 97), (-19, 97)), ((-9, 97), (73, 97)), ((83, 97), (97, 97))):\n            mb.seg(*seg_, .05, .2, 1.8, malla)\n        continue\n    mb.seg(a_, b_, .05, .2, 1.8, malla)",
    "for a_, b_ in CERR:\n    mb.seg(a_, b_, .05, .2, 1.8, malla)")
rep("pin(20, 'Ingreso / salida Plazoleta', 'Techo truss 8×4', (.10, .10, .12), TRUSS_ING[1], 6.5)",
    "pin(20, 'Ingreso con escarapela · oriente', 'Acceso a la Plazoleta por el cerramiento, techo truss 8×4 (PDF)', (.10, .10, .12), TRUSS_ING[1], 7.0)")
rep("pin(21, 'Ingreso / salida Plazoleta', 'Techo truss 8×4 (costado Verde)', (.10, .10, .12), TRUSS_ING[0], 6.5)",
    "pin(21, 'Ingreso con escarapela · occidente', 'Acceso a la Plazoleta por el cerramiento, techo truss 8×4 (PDF)', (.10, .10, .12), TRUSS_ING[0], 7.0)")

# ================= fachada del Gran Salon hacia las graderias (fotos 360): zocalo de piedra, puertas al lobby, franja de vidrio
rep("mb.prism(rect(PX0, 167.8, PX1, 168.2), Z_GS, -Z_GS - .4, M['arenisca'])            # fachada del Gran Salon hacia las gradas\nmb.prism(rect(-8, 167.6, 30, 167.9), Z_GS, 4.0, M['vidrio'])\nmb.prism(rect(-8, 166.0, 30, 168.0), Z_GS + 4.0, .3, M['concreto'])",
"""FY = 167.8                                                                           # linea de fachada hacia las gradas
mb.prism(rect(PX0, FY, PX1, FY + 1.0), Z_GS + 4.5, .7, M['concreto'])                 # losa del piso 2 (Multiproposito)
mb.prism(rect(PX0, FY, PX1, FY + .6), Z_MULTI + .7, -Z_MULTI - 1.1 - .7 + .3, M['arenisca'])   # zocalo de piedra del piso 2
mb.prism(rect(PX0, FY - .05, PX1, FY + .1), Z_MULTI + 1.9, 1.3, M['vidrio'])          # franja acristalada horizontal
mb.prism(rect(PX0, FY, PX1, FY + .6), Z_MULTI + 1.9, 1.3, M['arenisca'])              # (fondo detras del vidrio)
mb.prism(rect(PX0, FY - .4, PX1, FY + .6), -.4, .55, M['concreto'])                   # borde de la plaza
xp = PX0 + 1.0
while xp < PX1:                                                                        # pilares de piedra cada 7.2 m
    mb.box((xp, FY + .3, Z_GS), (1.2, .7, 4.5), M['arenisca'])
    xp += 7.2
mb.prism(rect(PX0, FY + .15, PX1, FY + .25), Z_GS, 4.5, M['vidrio'])                  # vidriera del lobby (piso 1)
for xd in (PX0 + 1.0 + 7.2 * 2 + 3.6, PX0 + 1.0 + 7.2 * 4 + 3.6, PX0 + 1.0 + 7.2 * 6 + 3.6):   # puertas de acceso al lobby
    mb.box((xd, FY + .1, Z_GS), (3.6, .25, 3.0), M['negro']); mb.box((xd, FY + .05, Z_GS + .1), (3.3, .1, 2.8), M['vidrio_brt'])
    mb.box((xd, FY + .12, Z_GS + 3.0), (4.0, .3, .25), M['efx_r'])
wall_text('PLAZA MAYOR  ·  CONVENCIONES Y EXPOSICIONES', (PX0 + 24, FY - .02, Z_MULTI + 3.9), .6, M['blanco'], 'losa', 0.0)
wall_text('GRAN SALÓN  ·  REGISTRO Y SALAS', (PX0 + 24, FY + .08, Z_GS + 3.9), .5, M['blanco'], 'losa', 0.0)""")

rep("cam_persp('Cam_Gradas', (70, 150, 16), (0, 176, -2), 24)", "cam_persp('Cam_Gradas', (70, 150, 16), (0, 176, -2), 24)\ncam_persp('Cam_Fachada_GS', (4, 112, 9), (3, 168, -3), 24)   # desde la plazoleta hacia las graderias y la fachada del Gran Salon")

# ================= exhibicion de carros y motos de lujo (iconos del PDF: 11 carros rojos vectoriales, 10 motos como imagenes)
rep("for x, y in D['carros']:\n    car(x, y, math.radians(-20), CARC[2])", """LUX = [mat('lujo_%d' % i, c, .2, .85) for i, c in enumerate([(.80, .02, .04), (.04, .04, .05), (.92, .92, .90), (.55, .57, .60), (.05, .12, .35), (.90, .60, .05), (.35, .36, .38)])]
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
# el tapete/catenarias VIP 10x5 queda al norte de las motos (PDF)""")
rep("cam_persp('Cam_Fachada_GS', (4, 112, 9), (3, 168, -3), 24)", "cam_persp('Cam_Fachada_GS', (-10, 157.5, -2.5), (4, 172, -3), 18)\ncam_persp('Cam_Carros', (74, 118, 6), (49, 134, .8), 26)")

rep("mx0, my0, mx1, my1 = bbox(E['Multi_bloque']); mx1 = min(mx1, PX1 - .6)", "mx0, my0, mx1, my1 = bbox(E['Multi_bloque']); mx1 = min(mx1, PX1 - .6); my0 = max(my0, 168.4)   # no sobresale de la fachada hacia las gradas")

# ================= fachada Gran Salon / Multiproposito hacia las graderias, segun foto del usuario
block("FY = 167.8                                                                           # linea de fachada hacia las gradas",
      "# ================================================================ VIAS Y RIO", """FY = 167.8                                   # linea de fachada hacia las gradas (voladizo); el vidrio del piso 1 va retranqueado
RET = 3.2                                    # retranqueo de la vidriera del Gran Salon bajo el voladizo
Z1T = Z_GS + 4.6                             # cara superior de la losa del piso 2 (balcon)
Z2T = -0.6                                   # losa superior (plaza)
# piso 1: pilares de concreto en el borde del voladizo + vidriera retranqueada con puertas
xp = PX0 + 2.0
while xp < PX1 - 1:
    mb.box((xp, FY + .45, Z_GS), (.8, .8, Z1T - Z_GS), M['concreto']); xp += 8.4
mb.prism(rect(PX0, FY + RET, PX1, FY + RET + .1), Z_GS, Z1T - .7 - Z_GS, M['vidrio'])
for xm in range(int(PX0) + 3, int(PX1), 3):
    mb.box((xm, FY + RET + .05, Z_GS), (.12, .2, Z1T - .7 - Z_GS), M['concreto_osc'])
mb.prism(rect(PX0, FY + RET - .1, PX1, FY + RET + .3), Z1T - .7, .7, M['concreto'])        # dintel
mb.prism(rect(PX0, FY, PX1, FY + RET + .3), Z1T - .7, .7, M['concreto'])                   # losa del voladizo
for xd in (PX0 + 10, PX0 + 24, PX0 + 38):                                                   # puertas de vidrio al lobby
    mb.box((xd, FY + RET + .02, Z_GS), (3.6, .3, 2.9), M['negro']); mb.box((xd, FY + RET - .05, Z_GS + .1), (3.3, .1, 2.7), M['vidrio_brt'])
mb.prism(rect(PX0, FY, PX1, FY + RET), Z_GS - .3, .32, M['pav_plaza'])                        # piso del porche
# piso 2: balcon corrido con baranda de vidrio, ventanales altos y volumen de persianas de madera
mb.prism(rect(PX0, FY, PX1, FY + 1.6), Z1T, .25, M['concreto'])                             # piso del balcon
mb.prism(rect(PX0, FY + .05, PX1, FY + .1), Z1T + .25, 1.1, M['vidrio'])                    # baranda
for xm in range(int(PX0) + 1, int(PX1), 2):
    mb.box((xm, FY + .07, Z1T + .25), (.05, .05, 1.1), M['acero'])
mb.prism(rect(PX0, FY + 1.6, PX1, FY + 1.7), Z1T, Z2T - .9 - Z1T, M['vidrio'])             # ventanales altos
for xm in range(int(PX0) + 2, int(PX1), 4):
    mb.box((xm, FY + 1.65, Z1T), (.15, .25, Z2T - .9 - Z1T), M['concreto_osc'])
mb.prism(rect(PX0, FY + 1.6, PX1, FY + 1.7), Z2T - .9, .3, M['concreto'])
mb.prism(rect(PX0, FY, PX1, FY + 1.7), Z2T - .6, .6, M['negro'])                            # franja negra del letrero
mb.prism(rect(PX0, FY, PX0 + 16, FY + 1.7), Z1T + .25, Z2T - .6 - Z1T - .25, mat('persiana_madera', (.22, .13, .08), .7))   # volumen de persianas (occidente)
for zz in [Z1T + .5 + k * .35 for k in range(int((Z2T - .6 - Z1T - .5) / .35))]:
    mb.box((PX0 + 8, FY - .02, zz), (16, .06, .12), M['negro'])
mb.prism(rect(PX0, FY, PX1, FY + 1.7), Z2T, .6, M['arenisca'])                              # remate de piedra bajo la plaza
mb.prism(rect(PX0, FY - .4, PX1, FY + .6), -.4, .42, M['concreto'])                         # borde de la plaza
wall_text('PLAZA MAYOR  ·  CONVENCIONES Y EXPOSICIONES', (PX0 + 30, FY - .03, Z2T - .3), .45, M['blanco'], 'losa', 0.0)
# muros laterales de piedra de las gradas (jardineras) con pasamanos
for a_, b_ in (((sx0 - .4, sy0), (sx0 - .4, FY)), ((sx1 + .4, sy0), (sx1 + .4, FY))):
    mb.seg(a_, b_, .8, Z_GS, -Z_GS + .9, M['arenisca'])

""")

# ================= fachada de Convenciones segun fotos 360 (Plazoleta Interamericana / Acceso Convenciones)
block("FY = 167.8                                   # linea de fachada hacia las gradas (voladizo); el vidrio del piso 1 va retranqueado",
      "# ================================================================ VIAS Y RIO", """FY = 167.8                                   # linea de fachada (borde del voladizo del piso 2)
RET = 2.6                                    # retranqueo de la vidriera del Gran Salon
Z1T = Z_GS + 4.6                             # cara superior de la losa del balcon (piso 2)
Z2T = -0.6                                   # losa de la plaza (piso 3)
PERS = mat('persiana_madera', (.20, .12, .07), .7)
LED = mat('pantalla_fachada', (.05, .08, .14), .3, 0, (.30, .55, 1.0), 1.6)
# --- piso 1: porche con pilares redondos, vidriera retranqueada con puertas, piso de piedra
xp = PX0 + 3.0
while xp < PX1 - 1:
    mb.raw(*CYL12, M['concreto'], (xp, FY + .6, Z_GS), (.45, .45, Z1T - .7 - Z_GS)); xp += 7.2
mb.prism(rect(PX0, FY + RET, PX1, FY + RET + .1), Z_GS, Z1T - .7 - Z_GS, M['vidrio'])
for xm in range(int(PX0) + 2, int(PX1), 2):
    mb.box((xm, FY + RET + .05, Z_GS), (.1, .18, Z1T - .7 - Z_GS), M['concreto_osc'])
for xd in (PX0 + 12, PX0 + 24, PX0 + 36):
    mb.box((xd, FY + RET + .02, Z_GS), (4.2, .3, 3.0), M['negro']); mb.box((xd, FY + RET - .05, Z_GS + .1), (3.9, .1, 2.8), M['vidrio_brt'])
mb.prism(rect(PX0, FY - .4, PX1, FY + RET), Z_GS - .3, .32, M['pav_plaza'])                # piso del porche
mb.prism(rect(PX0, FY, PX1, FY + RET + .3), Z1T - .7, .7, M['concreto'])                   # losa del voladizo
# --- piso 2: balcon corrido con baranda de acero, antepecho de concreto, ventanales, pantalla LED, persianas de madera al occidente
mb.prism(rect(PX0, FY - .3, PX1, FY + .1), Z1T, .9, M['concreto'])                         # antepecho
for xm in range(int(PX0) + 1, int(PX1), 2):
    mb.box((xm, FY - .1, Z1T + .9), (.05, .05, .5), M['acero'])
mb.box(((PX0 + PX1) / 2, FY - .1, Z1T + 1.35), (PX1 - PX0, .06, .06), M['acero'])
mb.prism(rect(PX0, FY + 1.8, PX1, FY + 1.9), Z1T, Z2T - 1.2 - Z1T, M['vidrio'])            # ventanales
for xm in range(int(PX0) + 2, int(PX1), 3):
    mb.box((xm, FY + 1.85, Z1T), (.14, .25, Z2T - 1.2 - Z1T), M['concreto_osc'])
mb.prism(rect(PX0, FY - .3, PX1, FY + 1.9), Z2T - 1.2, 1.2, M['concreto'])                 # viga/losa superior en voladizo
mb.prism(rect(PX0 + 2, FY - .2, PX0 + 22, FY + 1.9), Z1T + .9, Z2T - 1.2 - Z1T - .9, PERS)  # volumen de persianas (occidente)
for zz in [Z1T + 1.1 + k * .32 for k in range(int((Z2T - 1.2 - Z1T - 1.1) / .32))]:
    mb.box((PX0 + 12, FY - .22, zz), (20, .05, .1), M['negro'])
mb.box((PX0 + 34, FY - .25, Z1T + 1.6), (10, .12, 4.2), LED)                               # pantalla LED
mb.box((PX0 + 34, FY - .2, Z1T + 1.6), (10.3, .08, 4.5), M['negro'])
wall_text('PLAZA MAYOR  ·  CONVENCIONES Y EXPOSICIONES', (PX0 + 48, FY - .33, Z2T - .6), .45, M['blanco'], 'losa', 0.0)
# --- muros laterales de piedra (contencion de la plaza alta) y pasamanos de la escalinata
for a_, b_ in (((sx0 - .4, sy0), (sx0 - .4, FY)), ((sx1 + .4, sy0), (sx1 + .4, FY))):
    mb.seg(a_, b_, 1.0, Z_GS, -Z_GS - .05, M['arenisca'])
for x in [sx0 + 8 * k for k in range(1, 8)]:
    beam(mb, (x, sy0, 1.0), (x, sy1, Z_GS + 1.0), .06, M['acero'])
# --- totem negro de senalizacion frente al acceso
mb.box((sx0 + 20, sy0 - 2.5, 0), (.7, 1.2, 6.0), M['negro']); mb.box((sx0 + 20, sy0 - 3.12, 2.0), (.5, .02, 3.5), mat('totem_rojo', (.75, .05, .08), .4))

""")

rep("cr = cam_ortho('Cam_Planta_Caja', (ccx + 4, ccy + 2, 0), 0, 90, 66); cr.rotation_euler = (0, 0, math.radians(90))",
    "cr = cam_ortho('Cam_Planta_Caja', (ccx + 4, ccy + 2, 0), 0, 90, 66); cr.rotation_euler = (0, 0, math.radians(90))\n"
    "cg_ = cam_ortho('Cam_Planta_GS', (3, 188, 0), 0, 90, 100); cg_.rotation_euler = (0, 0, math.radians(90))   # lobby del Gran Salon + gradas, norte a la derecha")

# ================= proporciones del lobby (plano): las gradas terminan en Y 162.8; de ahi a la vidriera (167.8 + 2.6) va la explanada con los PL17-24
rep("PX0, PY0, PX1, PY1 = -30.1, 164.3, gx1 + 1.0, gy1 + 1.0", "PX0, PY0, PX1, PY1 = -30.1, 162.8, gx1 + 1.0, gy1 + 1.0")
rep("sx0, sy0, sx1, sy1 = bbox(GRADAS)", "sx0, sy0, sx1, sy1 = bbox(GRADAS); sy1 = 162.8")

# el muro bajo del Gran Salon no se dibuja en el frente de las gradas (ahi va la vidriera retranqueada)
rep("gsm.walls(ccw(GS_ED), Z_GS, 4.0, .5, MATS['muro_GS'], skip=(0,))",
    "_gp = ccw(GS_ED)\ngsm.walls(_gp, Z_GS, 4.0, .5, MATS['muro_GS'], skip=tuple(i for i in range(len(_gp)) if max(_gp[i][1], _gp[(i + 1) % len(_gp)][1]) < 169))")

# PL17 y PL18 estan al pie de las gradas, frente al acceso del Gran Salon: como volumen tapan la fachada; van como marcacion a piso
rep("    if s.get('sala') or 'caten' in s['texto'].lower() or len(p) > 5 or franja:   # sala abierta / marcacion a piso: tapete",
    "    if s.get('sala') or 'caten' in s['texto'].lower() or len(p) > 5 or franja or s['codigo'] in ('PL17', 'PL18'):   # sala abierta / marcacion a piso: tapete")
rep("        G[(g, 'Salas_abiertas')].prism(p, z + .02, .1, MATS['stand_' + k])\n        continue",
    "        G[(g, 'Salas_abiertas')].prism(p, z + .02, .1, MATS['stand_' + k])\n        if s['codigo']:\n            flat_text(s['codigo'], (c[0], c[1], z + .14), .9, M['negro'], g)\n        continue")

# la oficina del Multiproposito (paneleria blanca, piso 2) no puede salir mas alla de la fachada: se recorta a Y >= 170.5
rep("mu.prism(E['Multi_oficina'], Z_MULTI - .5, .5, MATS['piso_Multi'])",
    "OFI = [(x, max(y, 170.5)) for x, y in E['Multi_oficina']]\nmu.prism(OFI, Z_MULTI - .5, .5, MATS['piso_Multi'])")
rep("mu.walls(ccw(E['Multi_oficina']), Z_MULTI, 2.6, .2, M['stand_lado'], skip=(1,))", "mu.walls(ccw(OFI), Z_MULTI, 2.6, .2, M['stand_lado'], skip=(1,))")

# en el lobby del Gran Salon nada queda por fuera de la vidriera (Y >= 170.6): la Sala Abierta Convermate se recorta al interior
rep("        G[(g, 'Salas_abiertas')].prism(p, z + .02, .1, MATS['stand_' + k])",
    "        if reg == 'gran_salon':\n            p = [(a, max(b, 170.6)) for a, b in p]\n        G[(g, 'Salas_abiertas')].prism(p, z + .02, .1, MATS['stand_' + k])")

# ================= estructuras flotantes: dos bandas curvas que se cruzan (plano tecnico), no una sola
block("trk = smooth([(-28, 127), (-14, 120.5), (0, 116.5), (14, 116.5), (28, 120.5), (46, 126.5), (66, 130.5), (82, 132), (97, 132.5)])",
      "PLANTERS = [", """# trazado digitalizado del plano tecnico (px del recorte -> pagina -> mundo); las dos bandas nacen en el ingreso
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
""")

# ================= Fichas tecnicas Livesound (Render aprobado, 13/04/2026): tarimas, pantallas LED, torres y portico de ingreso
rep("    'tarima': mat('tarima', (.08, .08, .09), .5), 'pantalla': mat('pantalla_led', (.05, .08, .12), .2, 0, (.35, .65, 1.0), 2.0),",
    "    'tarima': mat('tarima', (.08, .08, .09), .5), 'pantalla': mat('pantalla_led', (.05, .08, .12), .2, 0, (.35, .65, 1.0), 2.0),\n"
    "    'faldon': mat('faldon_tarima', (.04, .04, .05), .9), 'luz_movil': mat('cabeza_movil', (.30, .18, .55), .35, .6),")
rep("def noise_mat(name, c1, c2, scale=40., rough=.8):", """def led_mat(name, file, strength=2.2):
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


def noise_mat(name, c1, c2, scale=40., rough=.8):""")
block("for t in D['tarimas']:\n    p = [tuple(q) for q in t['poly']]; c = centroid(p); reg = t['region']; z = z_of(c, reg); g = group_of(c, reg)",
      "for x, y, horiz, reg in D['mesas']:", """LED_MAIN = led_mat('led_main', 'led_main'); LED_WIDE = led_mat('led_wide', 'led_wide'); LED_LAT = led_mat('led_lateral', 'led_lateral')


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
        ugx, ugy1 = -1.7, 149.6                                                     # bajo la carpa (18 x 25, centro -1.7/137.3), extremo norte
        TARIMAS.append({'region': 'main', 'texto': 'Tarima UGC 12.2 (Livesound)', 'poly': [[ugx - 6.1, ugy1 - 3.7], [ugx + 6.1, ugy1 - 3.7], [ugx + 6.1, ugy1], [ugx - 6.1, ugy1]]})
    else:
        TARIMAS.append(t)
for t in TARIMAS:
    p = [tuple(q) for q in t['poly']]; c = centroid(p); reg = t['region']; z = z_of(c, reg); g = group_of(c, reg)
    e1 = math.dist(p[0], p[1]); e2 = math.dist(p[1], p[2]); big = max(e1, e2) > 4.5
    hh = .6 if max(e1, e2) > 12 else (1.0 if big else .6)          # fichas: principal 60 cm; secundarias 90-100 cm
    G[(g, 'Tarimas')].prism(p, z, hh, M['tarima'], side=M['faldon'])
    near = [(q[0], q[1]) for q in D['sillas'] if q[3] == reg and math.dist((q[0], q[1]), c) < (70 if big else 25)]   # solo sillas del mismo nivel
    if (big or reg in ('multi', 'comunidades')) and near:
        pc = centroid(near)
        i = max(range(len(p)), key=lambda i: math.dist(((p[i][0] + p[(i + 1) % len(p)][0]) / 2, (p[i][1] + p[(i + 1) % len(p)][1]) / 2), pc))
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
""")
rep("        uvl = me.uv_layers.new(name='UVMap')\n        uvl.data.foreach_set('uv', np.column_stack((u / pt, v / pt)).astype(np.float32).ravel())",
    "        uvl = me.uv_layers.new(name='UVMap')\n        uvarr = np.column_stack((u / pt, v / pt)).astype(np.float32)\n"
    "        for fi, quad in getattr(s, 'uvs', {}).items():            # caras con UV explicito (pantallas LED)\n"
    "            ls = me.polygons[fi].loop_start\n"
    "            for k, (uu, vv) in enumerate(quad):\n                uvarr[ls + k] = (uu, vv)\n"
    "        uvl.data.foreach_set('uv', uvarr.ravel())")
block("if PORTICO:                                              # portico de ingreso 10x6 (norte de la Caja)",
      "for k in range(4):                                       # huella de la celosia (liston bajo) para leer la Caja abierta", """if PORTICO:                                              # portico de ingreso LED (ficha Livesound: 10.2 x 5.1 m, vano 6 m, patas 1.5 x 2.1)
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
""")

rep("cam_persp('Cam_Carros', (74, 118, 6), (49, 134, .8), 26)", "cam_persp('Cam_Carros', (74, 118, 6), (49, 134, .8), 26)\n"
    "cam_persp('Cam_Portico', (11, 236, 2.0), (11, 222, 3.0), 28)      # frente al portico LED del ingreso\n"
    "cam_persp('Cam_Verde_Tarima', (-40, 80, 7.5), (-84, 46, 7.0), 24)   # Auditorio Effix (Verde) hacia la tarima")

# el fondo de la sala del Gran Salon se extiende hasta detras de la tarima (Y 269.5): el muro ya no corta la tarima
rep("gsm.walls(ccw(GS_SALA), Z_GS, 4.5, .4, MATS['madera_clara'])                     # muros de madera clara del auditorio",
    "GS_SALA = [(x, (269.5 if y > 250 else y)) for x, y in GS_SALA]                    # fondo detras de la tarima (PDF: tarima en Y 261-268.5)\n"
    "gsm.walls(ccw(GS_SALA), Z_GS, 4.5, .4, MATS['madera_clara'])                     # muros de madera clara del auditorio")

# ================= Pabellones mas altos (pedido de Alexander, 3 oct 2026): +2 a 3 m en cada volumen, con sus pines encima
rep("pavilion(E['Amarillo_A'], 0, 11.5, 'Amarillo', 'base', 'ext_base')", "pavilion(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'base', 'ext_base')")
rep("pavilion(E['Amarillo_B'], 0, 11.5, 'Amarillo', 'base', 'ext_base')", "pavilion(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'base', 'ext_base')")
rep("pavilion(E['Blanco'], 0, 10.8, 'Blanco', 'base', 'ext_base')", "pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', 'ext_base')")
rep("pavilion(E['Hall'], 0, 9, 'Hall', 'base', 'ext_base')", "pavilion(E['Hall'], 0, 11.5, 'Hall', 'base', 'ext_base')")
rep("pavilion(AZUL, Z_UP, 5.4, 'Azul', 'sup', 'ext_sup')", "pavilion(AZUL, Z_UP, 7.5, 'Azul', 'sup', 'ext_sup')")
rep("pavilion(VERDE, Z_UP, 13.3 - Z_UP + .6, 'Verde', 'sup', 'ext_sup')", "pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup')")
rep("G[('ext_sup', 'Cubiertas')].prism(VIPV, Z_UP + 6, .5, M['vip'])", "G[('ext_sup', 'Cubiertas')].prism(VIPV, Z_UP + 8, .5, M['vip'])")
rep("(-66, 47), Z_UP + 10, 'sup', 'Nivel superior')", "(-66, 47), Z_UP + 14.5, 'sup', 'Nivel superior')")
rep("(-13, 84), Z_UP + 9.5, 'sup', 'Nivel superior')", "(-13, 84), Z_UP + 14.5, 'sup', 'Nivel superior')")
rep("(-31, 44), Z_UP + 9.5, 'sup', 'Nivel superior')", "(-31, 44), Z_UP + 14.5, 'sup', 'Nivel superior')")
rep("(-32, -1), Z_UP + 10, 'sup', 'Nivel superior')", "(-32, -1), Z_UP + 11, 'sup', 'Nivel superior')")
rep("(.70, .25, .55), (30, -10), 10.5)", "(.70, .25, .55), (30, -10), 14.5)")
rep("(.50, .52, .55), (22, 52), 14)", "(.50, .52, .55), (22, 52), 16.5)")
rep("(.88, .64, .02), (68, -18), 15)", "(.88, .64, .02), (68, -18), 17.5)")
rep("(.80, .55, .02), (68, -80), 15)", "(.80, .55, .02), (68, -80), 17.5)")

# ================= Gran Salon: auditorio a toda altura con cielo negro, paneles acusticos organicos y focos (foto del recorrido 360)
# Va en el grupo 'losa': se ve desde adentro (video, renders) y se quita en el modo por niveles para no tapar el auditorio.
rep("G[('gs', 'Pisos')].prism(ccw(GS_SALA), Z_GS + .01, .08, MATS['alfombra_gs'])         # alfombra gris azulada",
    """G[('gs', 'Pisos')].prism(ccw(GS_SALA), Z_GS + .01, .08, MATS['alfombra_gs'])         # alfombra gris azulada
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
        gc.box((xw + sg * .04, yr, Z_GS + 5.5), (.06, 4.6, .6), mat('rejilla_gs', (.12, .12, .13), .7))""")

# ================= Pabellon Blanco como en la foto del recorrido 360: nave abierta con columnas redondas de concreto,
# cerchas metalicas bajo la cubierta blanca, cerramiento alto de vidrio con montantes, ventiladores y el extremo norte
# (hacia la Plazoleta Interamericana) abierto. Todo en 'ext_base': se quita en el modo por niveles.
rep("pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', 'ext_base')         # h 10.05 m",
    """pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', None)               # muros bajos y piso; lo alto va aparte
HB = 13.5
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
        bl.box((xf, yf, ZT - 1.7), (6.4, .32, .05), M['blanco'], a_ * math.pi / 3)""")

# ================= Hall principal y Pabellon Azul segun las fotos del recorrido 360 (3 oct 2026)
# Hall: conecta Blanco (norte), Amarillo (oriente), Azul/Rojo (occidente) y Zona de Comidas (sur). Cubierta alta con
# cerchas, cerramiento de vidrio, mezanine en el costado sur (2o piso = Grupo Effi), avisos negros con el nombre de
# cada pabellon, bloque azul del ascensor y gradas anchas que suben al Azul.
rep("pavilion(E['Hall'], 0, 11.5, 'Hall', 'base', 'ext_base')\nfor k in ('Sala_Grupo_Effi', 'Sala_Unmerco'):",
    """pavilion(E['Hall'], 0, 11.5, 'Hall', 'base', None)
HH = 11.5
_hp = ccw(E['Hall']); hx0, hy0, hx1, hy1 = bbox(E['Hall'])
G[('ext_base', 'Muros_altos')].walls(_hp, WALL_LOW, HH - WALL_LOW, .12, M['vidrio'])
G[('ext_base', 'Cubiertas')].prism(_hp, HH, 1.5, MATS.get('techo_Hall', MATS['muro_Hall']), side=MATS['muro_Hall'])
hl = G[('ext_base', 'Hall_estructura')]
xh = hx0 + 3.0
while xh < hx1 - 1:                                      # cerchas de la cubierta del Hall
    truss(hl, (xh, hy0 + .6, HH - 1.0), (xh, hy1 - .6, HH - 1.0), 1.1, 2.4, m=M['acero']); xh += 6.9
for yh in (hy0 + 1.2, (hy0 + hy1) / 2, hy1 - 1.2):
    truss(hl, (hx0 + 1, yh, HH - 1.0), (hx1 - 1, yh, HH - 1.0), .7, 3.2, m=M['acero'])
AVISO = mat('aviso_negro', (.03, .03, .04), .5)


def aviso(mb, texto, c, largo, z, rz, alto=1.1, size=.62, grp='ext_base'):
    # banda negra colgada con el nombre en blanco; rz = hacia donde mira (0 = sur, pi = norte, pi/2 = oriente, -pi/2 = occidente)
    mb.box((c[0], c[1], z), (largo if abs(math.sin(rz)) < .5 else .16, .16 if abs(math.sin(rz)) < .5 else largo, alto), AVISO)
    dx, dy = math.sin(rz) * .1, -math.cos(rz) * .1
    wall_text(texto, (c[0] + dx, c[1] + dy, z + alto / 2), size, M['blanco'], grp, rz)


aviso(hl, 'PABELLÓN BLANCO', (22.5, hy1 - .5), 26, 6.2, 0)                       # pared norte: acceso al Blanco
aviso(hl, 'SALIDA · EXIT', (3.0, hy1 - .5), 7.5, 6.2, 0, size=.5)
aviso(hl, 'PABELLÓN AMARILLO', (hx1 - .5, -10), 20, 5.2, -math.pi / 2)           # pared oriente: acceso al Amarillo
aviso(hl, 'PABELLÓN AZUL', (hx0 + 6.5, -4.5), 9, 7.4, math.pi / 2)               # sobre las gradas que suben al Azul
aviso(hl, 'PABELLÓN ROJO', (hx0 + .6, -17.5), 7, 3.4, math.pi / 2, .8, .42)      # acceso bajo al Rojo
hl.box((hx0 + .5, -17.5, 0), (.4, 8.0, 1.2), MATS['muro_Rojo'])                  # antepecho rojo del acceso al Rojo
hl.box((hx0 + 2.6, -11.0, 0), (4.6, 4.8, HH - 1.6), MATS['muro_Azul'])           # bloque azul del ascensor
hl.box((hx0 + 5.0, -11.0, 0), (.2, 2.2, 2.4), M['acero'])                        # puerta del ascensor
n_g = 28                                                 # gradas anchas Hall -> Pabellon Azul (suben hacia el occidente)
for i in range(n_g):
    xa = hx0 + 10.0 - (i + 1) * (10.0 / n_g)
    hl.prism(rect(xa, -8.2, xa + 10.0 / n_g + .02, hy1 - .8), 0, (i + 1) * Z_UP / n_g, M['concreto'])
for yb in (-8.2, -3.4, hy1 - .8):                        # barandas de las gradas
    beam(hl, (hx0 + 10.0, yb, 1.0), (hx0, yb, Z_UP + 1.0), .05, M['acero'])
# mezanine (2o piso) del costado sur: Grupo Effi. Va en el nivel superior ('sup'): en el modo por niveles sube con el Azul.
mz = G[('sup', 'Hall_mezanine_Grupo_Effi')]
MX0, MX1, MY0, MY1 = hx0 + 6.0, hx1 - .6, hy0 + .5, hy0 + 9.6
mz.prism(rect(MX0, MY0, MX1, MY1), Z_UP - .5, .5, M['concreto'], top=mat('piso_grupo_effi', (.10, .12, .16), .55))
mz.box(((MX0 + MX1) / 2, MY1, Z_UP - .5), (MX1 - MX0, .22, 1.7), M['blanco'])                 # antepecho blanco del mezanine
aviso(mz, 'HALL PRINCIPAL  ·  EXHIBITION CENTER MAIN HALL', ((MX0 + MX1) / 2, MY1 + .05), MX1 - MX0, Z_UP - 1.5, math.pi, 1.0, .5, 'sup')
flat_text('GRUPO EFFI', ((MX0 + MX1) / 2, (MY0 + MY1) / 2, Z_UP + .03), 2.2, M['blanco'], 'sup', 0.0)
for xm in (MX0 + 4, (MX0 + MX1) / 2 - 6, (MX0 + MX1) / 2 + 6, MX1 - 4):                        # salas y lounges de Grupo Effi
    mz.box((xm, MY0 + 2.2, Z_UP), (5.0, 3.0, 2.6), M['stand_lado'])
    mz.box((xm, MY0 + 3.75, Z_UP + 1.9), (5.0, .12, .7), mat('grupo_effi_marca', (.05, .35, .75), .5))
xc_ = MX0 + 3.0
while xc_ < MX1:                                         # columnas del mezanine (se quitan con las cubiertas)
    hl.box((xc_, MY1 - .5, 0), (.7, .9, Z_UP - .5), M['concreto']); xc_ += 9.0
n_e = 24                                                 # escalera al mezanine (extremo occidental, sube hacia el oriente)
for i in range(n_e):
    xe = hx0 + .6 + i * (MX0 + 1.0 - hx0 - .6) / n_e
    hl.prism(rect(xe, MY0 + 4.6, xe + (MX0 + 1.0 - hx0 - .6) / n_e + .02, MY0 + 7.0), 0, (i + 1) * (Z_UP - .5) / n_e, M['concreto'])
for k in ('Sala_Unmerco',):""")
rep("pin(15, 'Hall', 'Auditorios Grupo Effi y Unmerco', (.70, .25, .55), (30, -10), 14.5)",
    "pin(15, 'Hall principal', 'Conecta Blanco, Amarillo, Azul, Rojo y Zona de Comidas · Auditorio Unmerco', (.70, .25, .55), (30, -6), 14.5)")
rep("pin(22, 'Zona Black · uso exclusivo',",
    "pin(23, 'Grupo Effi · piso 2 del Hall', 'Mezanine del Hall principal: todas las marcas de Grupo Effi', (.05, .30, .68), (20, -17.5), Z_UP + 9.5, 'sup', 'Nivel superior')\n"
    "pin(22, 'Zona Black · uso exclusivo',")

# Pabellon Azul: nave real (columnas, cerchas, vidrio con montantes, ventiladores), abierta hacia el Hall (oriente)
rep("pavilion(AZUL, Z_UP, 7.5, 'Azul', 'sup', 'ext_sup')                   # h 4.7 m",
    """pavilion(AZUL, Z_UP, 7.5, 'Azul', 'sup', None)
HA = 7.5
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
        az.box((xf, yf, ZA - 1.5), (5.6, .3, .05), M['blanco'], a_ * math.pi / 3)""")

# ================= Puertas reales: los muros bajos de cada pabellon se abren donde hay acceso (antes eran corridos)
rep("def pavilion(poly, z0, h_total, key, grp, ext, roofed=True, low_h=WALL_LOW, t=.5):",
    """def walls_gaps(mb, poly, z0, h, t, m, gaps=(), skip=()):
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
PUERTAS_HALL = [(22.5, 1.8, 14.0), (46.3, -10.0, 12.0), (-1.2, -3.6, 9.6), (-1.2, -17.5, 7.0), (20.0, -22.2, 12.0)]
PUERTAS_BLANCO = [(22.5, 1.8, 14.0), (22.5, 98.0, 18.0)]
PUERTAS_AMARILLO = [(46.9, -10.0, 12.0)]
PUERTAS_AZUL_VERDE = [(-55.5, 19.7, 6.0), (-22.0, 19.7, 6.0)]
PUERTAS_ROJO = [(-9.2, -17.5, 6.0), (-15.0, -22.2, 5.0)]


def pavilion(poly, z0, h_total, key, grp, ext, roofed=True, low_h=WALL_LOW, t=.5, gaps=()):""")
rep("    G[(grp, 'Muros_bajos')].walls(poly, z0, low_h, t, MATS['muro_' + key])",
    "    walls_gaps(G[(grp, 'Muros_bajos')], poly, z0, low_h, t, MATS['muro_' + key], gaps)")
rep("pavilion(E['Hall'], 0, 11.5, 'Hall', 'base', None)", "pavilion(E['Hall'], 0, 11.5, 'Hall', 'base', None, gaps=PUERTAS_HALL)")
rep("pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', None)               # muros bajos y piso; lo alto va aparte",
    "pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', None, gaps=PUERTAS_BLANCO)   # muros bajos y piso; lo alto va aparte")
rep("pavilion(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'base', 'ext_base')", "pavilion(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'base', 'ext_base', gaps=PUERTAS_AMARILLO)")
rep("pavilion(AZUL, Z_UP, 7.5, 'Azul', 'sup', None)", "pavilion(AZUL, Z_UP, 7.5, 'Azul', 'sup', None, gaps=PUERTAS_AZUL_VERDE)")
rep("pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup')", "pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup', gaps=PUERTAS_AZUL_VERDE)")
rep("        az.box((xf, yf, ZA - 1.5), (5.6, .3, .05), M['blanco'], a_ * math.pi / 3)",
    """        az.box((xf, yf, ZA - 1.5), (5.6, .3, .05), M['blanco'], a_ * math.pi / 3)
for gx, gy, gw in PUERTAS_AZUL_VERDE:                    # accesos Azul <-> Verde: panel azul sobre puerta doble de vidrio
    az.box((gx, gy - .1, Z_UP + 2.7), (gw + 3.0, .3, 2.6), MATS['muro_Azul'])
    for s_ in (-gw / 2, 0, gw / 2):
        az.box((gx + s_, gy, Z_UP), (.12, .12, 2.7), M['acero'])
    G[('sup', 'Pisos')].prism(rect(gx - gw / 2, gy - .6, gx + gw / 2, gy + 1.6), Z_UP - .45, .5, M['concreto'])   # umbral / pasarela""")
rep("G[('inf', 'Muros_bajos')].walls(ccw(ROJO), 0, WALL_LOW, .5, MATS['muro_Rojo'])",
    """walls_gaps(G[('inf', 'Muros_bajos')], ccw(ROJO), 0, WALL_LOW, .5, MATS['muro_Rojo'], PUERTAS_ROJO)
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
rr.box(((rx0 + rx1) / 2, ry0 + 15.8, H_LOW - 1.5), (rx1 - rx0 - 6, .9, .9), M['acero'])   # ducto de ventilacion""")

# ================= Pabellon Amarillo (fotos): nave con cerchas, vidrio alto, antepecho amarillo, ventiladores y el bloque
# de acceso desde el Hall (franja amarilla con oficina acristalada encima)
rep("def pavilion(poly, z0, h_total, key, grp, ext, roofed=True, low_h=WALL_LOW, t=.5, gaps=()):",
    """def nave(poly, z0, H, key, ext, abre=()):
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


def pavilion(poly, z0, h_total, key, grp, ext, roofed=True, low_h=WALL_LOW, t=.5, gaps=()):""")
rep("pavilion(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'base', 'ext_base')",
    "pavilion(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'base', None)\nnave(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'ext_base')")
rep("pavilion(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'base', 'ext_base', gaps=PUERTAS_AMARILLO)",
    """pavilion(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'base', None, gaps=PUERTAS_AMARILLO)
am = nave(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'ext_base')
_amx0 = bbox(E['Amarillo_B'])[0]
am.box((_amx0 + .9, -10.0, 3.6), (1.4, 15.0, 1.1), MATS['muro_Amarillo'])          # franja amarilla sobre el acceso al Hall
am.box((_amx0 + 1.1, -10.0, 4.7), (1.8, 15.0, 3.0), M['vidrio'])                    # oficina acristalada encima
for ys_ in (-17.4, -13.7, -10.0, -6.3, -2.6):
    am.box((_amx0 + .3, ys_, 0), (.14, .14, 3.6), M['acero'])                       # montantes de las puertas de vidrio""")

# ================= Hall principal mas alto que Rojo, Amarillo y Zona de Comidas (fotos y nota de Alexander): plataforma + gradas
rep("def is_up(c):", """ZH_HALL = 1.2                                  # el Hall queda 1.2 m sobre Rojo / Amarillo / Zona de Comidas


def is_up(c):""")
rep("'caja': 0.}.get(reg, Z_UP if is_up(c) else 0.)", "'caja': 0.}.get(reg, Z_UP if is_up(c) else (ZH_HALL if pip(c, E['Hall']) else 0.))")
rep("PUERTAS_HALL = [(22.5, 1.8, 14.0), (46.3, -10.0, 12.0), (-1.2, -3.6, 9.6), (-1.2, -17.5, 7.0), (20.0, -22.2, 12.0)]",
    "PUERTAS_HALL = [(12.0, 1.8, 6.0), (33.0, 1.8, 6.0), (46.3, -12.0, 8.0), (-1.2, -3.6, 9.6), (-1.2, -17.5, 7.0), (13.5, -22.2, 6.0), (30.5, -22.2, 4.6)]")
rep("PUERTAS_BLANCO = [(22.5, 1.8, 14.0), (22.5, 98.0, 18.0)]", "PUERTAS_BLANCO = [(12.0, 1.8, 6.0), (33.0, 1.8, 6.0), (22.5, 98.0, 18.0)]")
rep("PUERTAS_AMARILLO = [(46.9, -10.0, 12.0)]", "PUERTAS_AMARILLO = [(46.9, -12.0, 8.0), (47.4, -24.0, 3.2)]      # al Hall y a la Zona de Comidas")
rep("_hp = ccw(E['Hall']); hx0, hy0, hx1, hy1 = bbox(E['Hall'])",
    """_hp = ccw(E['Hall']); hx0, hy0, hx1, hy1 = bbox(E['Hall'])
_plat = [(hx0, hy0), (hx1, hy0), (hx1, -16.0), (hx1 - 2.4, -16.0), (hx1 - 2.4, -8.0), (hx1, -8.0), (hx1, hy1), (hx0, hy1)]
G[('base', 'Pisos')].prism(_plat, 0, ZH_HALL, M['concreto'], top=MATS.get('int_Hall', MATS['piso_Hall']))
gh = G[('base', 'Gradas_Hall')]


def gradas(mb, x0, y0, x1, y1, hacia, zh, n=8):
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


gradas(gh, hx1 - 2.4, -16.0, hx1, -8.0, 'E', ZH_HALL)            # bajan al Pabellon Amarillo
gradas(gh, hx0 - 2.6, -21.0, hx0 - .2, -14.0, 'O', ZH_HALL)       # bajan al Pabellon Rojo
gradas(gh, 10.5, hy0 - 2.6, 16.5, hy0 - .2, 'S', ZH_HALL)         # bajan a la Zona de Comidas (2 accesos)
gradas(gh, 28.2, hy0 - 2.6, 32.8, hy0 - .2, 'S', ZH_HALL)
gradas(gh, 9.0, hy1 + .2, 15.0, hy1 + 2.6, 'N', ZH_HALL)          # paso al Pabellon Blanco (2 accesos)
gradas(gh, 30.0, hy1 + .2, 36.0, hy1 + 2.6, 'N', ZH_HALL)
for _x in (10.5, 13.5, 16.5, 28.2, 32.8):                         # pasamanos de las gradas a la Zona de Comidas
    beam(gh, (_x, hy0 - .2, ZH_HALL + .9), (_x, hy0 - 2.6, .9), .04, M['acero'])""")
rep("hl.box((hx0 + .5, -17.5, 0), (.4, 8.0, 1.2), MATS['muro_Rojo'])                  # antepecho rojo del acceso al Rojo",
    "aviso(hl, 'ZONA DE COMIDAS', (21.5, hy0 + .5), 24, 4.4, math.pi, .9, .5)             # pared sur: salida a la Zona de Comidas")
rep("hy1 - .8), 0, (i + 1) * Z_UP / n_g, M['concreto'])", "hy1 - .8), 0, ZH_HALL + (i + 1) * (Z_UP - ZH_HALL) / n_g, M['concreto'])")
rep("beam(hl, (hx0 + 10.0, yb, 1.0), (hx0, yb, Z_UP + 1.0), .05, M['acero'])", "beam(hl, (hx0 + 10.0, yb, ZH_HALL + 1.0), (hx0, yb, Z_UP + 1.0), .05, M['acero'])")
rep("    xe = hx0 + .6 + i * (MX0 + 1.0 - hx0 - .6) / n_e", "    xe = 16.0 - (i + 1) * 10.0 / n_e                  # escalera al mezanine: arranca junto a la Sala Unmerco y sube al occidente")
rep("    hl.prism(rect(xe, MY0 + 4.6, xe + (MX0 + 1.0 - hx0 - .6) / n_e + .02, MY0 + 7.0), 0, (i + 1) * (Z_UP - .5) / n_e, M['concreto'])",
    "    hl.prism(rect(xe, MY1 + .2, xe + 10.0 / n_e + .02, MY1 + 2.4), 0, ZH_HALL + (i + 1) * (Z_UP - .5 - ZH_HALL) / n_e, M['concreto'])")
rep("G[('base', 'Muros_bajos')].walls(ccw(E[k]), 0, 3.6, .25, M['stand_lado'])", "G[('base', 'Muros_bajos')].walls(ccw(E[k]), ZH_HALL, 3.6, .25, M['stand_lado'])")

# ================= Amarillo: UNA sola nave (la division con el Auditorio Marketing es temporal, solo un muro bajo) y salidas a comidas
rep("pavilion(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'base', None)\nnave(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'ext_base')",
    """pavilion(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'base', None, gaps=[(47.0, -60.0, 6.0)])
_aA = ccw(E['Amarillo_A']); _aB = ccw(E['Amarillo_B'])
nave(E['Amarillo_A'], 0, 14.5, 'Amarillo', 'ext_base',
     abre=tuple(i for i in range(len(_aA)) if min(_aA[i][1], _aA[(i + 1) % len(_aA)][1]) > bbox(_aA)[3] - 1.5))
G[('ext_base', 'Cubiertas')].prism(rect(bbox(_aB)[0], bbox(_aA)[3] - .3, bbox(_aB)[2], bbox(_aB)[1] + .3), 14.5, 1.5,
                                   MATS.get('techo_Amarillo', MATS['muro_Amarillo']), side=MATS['muro_Amarillo'])
for _xw in (bbox(_aB)[0], bbox(_aB)[2]):                     # vidrio alto en el tramo de union
    G[('ext_base', 'Muros_altos')].seg((_xw, bbox(_aA)[3]), (_xw, bbox(_aB)[1]), .12, WALL_LOW, 14.5 - WALL_LOW, M['vidrio'])
G[('base', 'Muros_bajos')].box(((bbox(_aB)[0] + bbox(_aB)[2]) / 2, (bbox(_aA)[3] + bbox(_aB)[1]) / 2, WALL_LOW), (bbox(_aB)[2] - bbox(_aB)[0], 1.6, 2.6),
                               mat('division_temporal', (.05, .05, .06), .9))   # division temporal (telon negro) del Auditorio Marketing""")
rep("am = nave(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'ext_base')",
    "am = nave(E['Amarillo_B'], 0, 14.5, 'Amarillo', 'ext_base',\n          abre=tuple(i for i in range(len(_aB)) if max(_aB[i][1], _aB[(i + 1) % len(_aB)][1]) < bbox(_aB)[1] + 1.5))")
rep("am.box((_amx0 + .9, -10.0, 3.6), (1.4, 15.0, 1.1), MATS['muro_Amarillo'])", "am.box((_amx0 + .9, -12.0, 3.6), (1.4, 12.0, 1.1), MATS['muro_Amarillo'])")
rep("am.box((_amx0 + 1.1, -10.0, 4.7), (1.8, 15.0, 3.0), M['vidrio'])", "am.box((_amx0 + 1.1, -12.0, 4.7), (1.8, 12.0, 3.0), M['vidrio'])")
rep("for ys_ in (-17.4, -13.7, -10.0, -6.3, -2.6):", "for ys_ in (-16.0, -13.3, -10.7, -8.0):")
rep("aviso(hl, 'PABELLÓN AMARILLO', (hx1 - .5, -10), 20, 5.2, -math.pi / 2)", "aviso(hl, 'PABELLÓN AMARILLO', (hx1 - .5, -12), 14, 5.2, -math.pi / 2)")

# ================= Pabellon Verde (fotos): cerchas en arco de acero blanco, montantes amarillos del vidrio y ventiladores
rep("pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup', gaps=PUERTAS_AZUL_VERDE)",
    """pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup', gaps=PUERTAS_AZUL_VERDE)
vd = G[('ext_sup', 'Verde_estructura')]
_vp = ccw(VERDE); wx0_, wy0_, wx1_, wy1_ = bbox(VERDE)
MONT_AM = mat('montante_amarillo', (.90, .74, .05), .5)
ZS_V = Z_UP + 7.6
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
            vd.raw(*CYL12, M['blanco'], (_xv, _ye, Z_UP), (.3, .3, 7.6))
        if int(_xv) % 2 == 0:                               # ventilador de techo
            for a_ in range(3):
                vd.box((_xv + 5, (_ya + _yb) / 2, ZS_V + 1.5), (6.0, .3, .05), M['blanco'], a_ * math.pi / 3)
    _xv += 11.0
for k in range(len(_vp)):                                # montantes amarillos del cerramiento de vidrio
    a_, b_ = _vp[k], _vp[(k + 1) % len(_vp)]; n_ = max(1, int(math.dist(a_, b_) / 3.2))
    for i in range(n_):
        vd.box((a_[0] + (b_[0] - a_[0]) * (i + .5) / n_, a_[1] + (b_[1] - a_[1]) * (i + .5) / n_, Z_UP), (.16, .16, WALL_LOW + 1.4), MONT_AM)
_fin = None""")

# ================= Lobby del Gran Salon ("Hall principal" de Convenciones, fotos del recorrido 360): frente de vidrio esmerilado
# con el aviso GRAN SALON, pilares redondos, murales en el antepecho del piso 2, salas de convenciones (Zona Black) al fondo
# y pasillo lateral occidental con pilares y puertas de vidrio esmerilado.
rep("gd = G[('gs', 'Gran_Salon_puertas')]",
    """lb = G[('gs', 'Lobby_Gran_Salon')]
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
aviso(lb, 'ZONA BLACK  ·  SALAS DE CONVENCIONES', (_ex1 - .6, 184.5), 18, Z_GS + 2.85, -math.pi / 2, .9, .5, 'gs')
_yp = _sy0 + 4.0
while _yp < _sy1 - 2:                                                                        # pasillo lateral occidental: pilares
    lb.raw(*CYL12, M['concreto'], (_ex0 + 2.2, _yp, Z_GS), (.4, .4, 4.0)); _yp += 7.5
lb.box((_ex0 + .3, (_sy0 + _sy1) / 2, Z_GS + .4), (.08, _sy1 - _sy0 - 4, 3.2), M['vidrio'])   # vidriera hacia el jardin
for _yd in (_sy0 + 7.0, _sy0 + 15.0, _sy0 + 30.0):                                           # ingresos laterales de vidrio esmerilado
    lb.box((_sx0 - .35, _yd, Z_GS), (.1, 4.6, 3.0), VID_GS)
    for _s in (-2.3, 0, 2.3):
        lb.box((_sx0 - .35, _yd + _s, Z_GS), (.14, .12, 3.0), M['acero'])
mur = G[('multi', 'Lobby_murales')]
MURAL = [mat('mural_gs_%d' % i, c, .6) for i, c in enumerate(((.35, .55, .25), (.70, .20, .18), (.20, .40, .65), (.80, .62, .20), (.25, .50, .45)))]
for _ya, _sg in ((vy0, 1), (vy1, -1)):                                                       # antepecho de concreto con murales fotograficos
    mur.box(((vx0 + vx1) / 2, _ya, Z_MULTI - 1.3), (vx1 - vx0, .25, 1.3), M['concreto'])
    for _i in range(5):
        mur.box((vx0 + (vx1 - vx0) * (_i + .5) / 5, _ya + _sg * .14, Z_MULTI - 1.15), (3.6, .05, 1.0), MURAL[_i])
for _xa, _sg in ((vx0, 1), (vx1, -1)):
    mur.box((_xa, (vy0 + vy1) / 2, Z_MULTI - 1.3), (.25, vy1 - vy0, 1.3), M['concreto'])
    mur.box((_xa + _sg * .14, (vy0 + vy1) / 2, Z_MULTI - 1.15), (.05, 5.0, 1.0), MURAL[(2 + _sg) % 5])
gd = G[('gs', 'Gran_Salon_puertas')]""")

# ================= Pasillo Azul <-> Verde (zona VIP): sin el muro verde que lo cortaba (pedido de Alexander al validar en local)
VANOS_VERDE_PASILLO = "[(-36.2, 50.25, 19.4), (-29.55, 61.55, 8.4)]"
rep("pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup', gaps=PUERTAS_AZUL_VERDE)",
    "pavilion(VERDE, Z_UP, 16.5 - Z_UP + .6, 'Verde', 'sup', 'ext_sup', gaps=PUERTAS_AZUL_VERDE + " + VANOS_VERDE_PASILLO + ")")
rep("        G[(ext, 'Muros_altos')].walls(poly, z0 + low_h, h_total - low_h, t, MATS['fachada_pab'] if key in ('Amarillo', 'Blanco', 'Azul', 'Verde', 'Hall') else MATS['muro_' + key])",
    "        walls_gaps(G[(ext, 'Muros_altos')], poly, z0 + low_h, h_total - low_h, t, MATS['fachada_pab'] if key in ('Amarillo', 'Blanco', 'Azul', 'Verde', 'Hall') else MATS['muro_' + key], [g_ for g_ in gaps if g_[2] > 8])")

# ================= Zona Black: salas de comisiones al costado oriental del Gran Salon (fotos "Acceso Comisiones" y "Comisiones 5+6")
rep("aviso(lb, 'ZONA BLACK  ·  SALAS DE CONVENCIONES', (_ex1 - .6, 184.5), 18, Z_GS + 2.85, -math.pi / 2, .9, .5, 'gs')",
    """aviso(lb, 'SALA DE NEGOCIOS  ·  PRENSA  ·  SALA VIP', (_ex1 - .6, 184.5), 18, Z_GS + 2.85, -math.pi / 2, .9, .5, 'gs')
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
    lb.box((_xs, BY0 - 3.4, Z_GS), (2.2, .9, .75), M['negro'])""")
rep("(33.0, 178.4), Z_GS + 5, 'gs', 'Convenciones · piso 1')", "(36.4, 226.0), Z_GS + 5, 'gs', 'Convenciones · piso 1')")
# sin muros en la Sala Unmerco del Hall (pedido de Alexander)
rep("for k in ('Sala_Unmerco',):", "for k in ():")

# ================= Plancha de comidas al nivel del Hall + gradas anchas hacia la Zona de Comidas (correccion de Alexander)
rep("ZH_HALL = 1.2 ", "PLANCHA_COMIDAS = [(-1.2, -35.0), (47.2, -35.0), (47.2, -22.2), (-1.2, -22.2)]\nZH_HALL = 1.2 ")
rep("(ZH_HALL if pip(c, E['Hall']) else 0.)", "(ZH_HALL if (pip(c, E['Hall']) or pip(c, PLANCHA_COMIDAS)) else 0.)")
rep("gradas(gh, 10.5, hy0 - 2.6, 16.5, hy0 - .2, 'S', ZH_HALL)         # bajan a la Zona de Comidas (2 accesos)\ngradas(gh, 28.2, hy0 - 2.6, 32.8, hy0 - .2, 'S', ZH_HALL)",
    """G[('base', 'Pisos')].prism(PLANCHA_COMIDAS, 0, ZH_HALL, M['concreto'], top=M['pav'])      # plancha de comidas al nivel del Hall
gradas(gh, hx0, -37.8, 47.2, -35.0, 'S', ZH_HALL)                 # gradas a todo el ancho: bajan a la Zona de Comidas
beam(gh, (hx0, -22.4, ZH_HALL + .9), (hx0, -35.0, ZH_HALL + .9), .05, M['acero'])""")
rep("for _x in (10.5, 13.5, 16.5, 28.2, 32.8):                         # pasamanos de las gradas a la Zona de Comidas\n    beam(gh, (_x, hy0 - .2, ZH_HALL + .9), (_x, hy0 - 2.6, .9), .04, M['acero'])",
    "for _x in (hx0 + .2, 8.5, 18.2, 27.9, 37.6, 47.0):                # pasamanos de las gradas a la Zona de Comidas\n    beam(gh, (_x, -35.0, ZH_HALL + .9), (_x, -37.8, .9), .04, M['acero'])")
rep("crowd('base', (0, -118, 46, -24), 160, 0)", "crowd('base', (0, -118, 46, -24), 160, lambda x, y: ZH_HALL if y > -35.0 else (0 if y < -37.8 else ZH_HALL * (y + 37.8) / 2.8))")
rep("(47.4, -24.0, 3.2)]", "(47.4, -51.0, 3.5)]")

# ================= Puente Verde <-> Blanco <-> parte baja del Verde (marcado por Alexander en el visor local)
rep("PUERTAS_BLANCO = [(12.0, 1.8, 6.0), (33.0, 1.8, 6.0), (22.5, 98.0, 18.0)]", "PUERTAS_BLANCO = [(12.0, 1.8, 6.0), (33.0, 1.8, 6.0), (22.5, 98.0, 18.0), (5.9, 41.5, 5.0)]")
rep("gaps=PUERTAS_AZUL_VERDE + [(-36.2, 50.25, 19.4), (-29.55, 61.55, 8.4)])", "gaps=PUERTAS_AZUL_VERDE + [(-36.2, 50.25, 19.4), (-29.55, 61.55, 8.4), (-2.4, 72.8, 5.0)])")
rep("ex.walls(ccw(VERDE), 0, H_LOW, .5, MATS['muro_Verde_bajo'])", "walls_gaps(ex, ccw(VERDE), 0, H_LOW, .5, MATS['muro_Verde_bajo'], [(0.4, 76.5, 5.0)])")
rep("G[('sup', 'Pisos')].prism(ANEXO, Z_UP - .45, .5, MATS['piso_Verde'])",
    """G[('sup', 'Pisos')].prism(ANEXO, Z_UP - .45, .5, MATS['piso_Verde'])
pu = G[('base', 'Puente_Verde_Blanco')]
RX0, RX1, RY0, RY1 = -5.0, .2, 44.0, 72.8                 # rampa (rojo): baja del Verde alto (norte) hacia el Blanco (sur)
_v = [(RX0, RY1, Z_UP), (RX1, RY1, Z_UP), (RX1, RY0, .15), (RX0, RY0, .15)]
_v += [(x, y, z - .45) for x, y, z in _v]
pu.raw(_v, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['concreto'])
for _xr in (RX0 + .1, RX1 - .1):                          # barandas
    beam(pu, (_xr, RY1, Z_UP + 1.0), (_xr, RY0, 1.15), .06, M['acero'])
    for k in range(9):
        u = k / 8; pu.box((_xr, RY1 + (RY0 - RY1) * u, Z_UP + (.15 - Z_UP) * u), (.06, .06, 1.0), M['acero'])
for k in range(1, 4):                                     # apoyos de la rampa
    u = k / 4.6; zc = Z_UP + (.15 - Z_UP) * u - .45
    for _xr in (RX0 + .6, RX1 - .6):
        pu.raw(*CYL8, M['concreto'], (_xr, RY1 + (RY0 - RY1) * u, 0), (.28, .28, zc))
pu.prism(rect(RX0, 38.6, 5.9, RY0), 0, .15, M['concreto'])                 # descanso frente a la puerta del Blanco
pu.prism(rect(.6, RY0, 5.7, 81.0), 0, .12, M['concreto'])                  # paso (azul): del Blanco a la parte baja del Verde
for _yb in (RY0 + 2, 81.0):
    pass
beam(pu, (5.6, RY0 + 6, 1.0), (5.6, 81.0, 1.0), .05, M['acero'])
aviso(pu, 'PABELLÓN BLANCO', (5.5, 41.5), 6.0, 3.3, -math.pi / 2, .8, .4, 'base')
aviso(pu, 'AUDITORIO COMUNIDADES', (.7, 76.5), 6.0, 3.3, math.pi / 2, .8, .36, 'base')""")

# ================= Escaleras del Hall segun el plano tecnico enviado por Alexander
rep("ZH_HALL = 1.2 ", "HALL_ALTO = [(-1.2, -22.2), (34.6, -22.2), (34.6, 1.8), (-1.2, 1.8)]     # el extremo oriental del Hall queda al nivel del Amarillo\nZH_HALL = 1.2 ")
rep("(pip(c, E['Hall']) or pip(c, PLANCHA_COMIDAS))", "(pip(c, HALL_ALTO) or pip(c, PLANCHA_COMIDAS))")
rep("PLANCHA_COMIDAS = [(-1.2, -35.0), (47.2, -35.0)", "PLANCHA_COMIDAS = [(-1.2, -34.4), (47.2, -34.4)")
rep("PUERTAS_HALL = [(12.0, 1.8, 6.0), (33.0, 1.8, 6.0), (46.3, -12.0, 8.0), (-1.2, -3.6, 9.6), (-1.2, -17.5, 7.0), (13.5, -22.2, 6.0), (30.5, -22.2, 4.6)]",
    "PUERTAS_HALL = [(12.0, 1.8, 6.0), (30.5, 1.8, 6.0), (46.3, -14.0, 8.0), (-1.2, -5.45, 8.5), (-1.2, -16.3, 5.0), (2.5, -22.2, 3.0), (13.5, -22.2, 6.0), (30.5, -22.2, 4.6)]")
rep("(33.0, 1.8, 6.0), (22.5, 98.0, 18.0), (5.9, 41.5, 5.0)]", "(30.5, 1.8, 6.0), (22.5, 98.0, 18.0), (5.9, 41.5, 5.0)]")
rep("PUERTAS_AMARILLO = [(46.9, -12.0, 8.0)", "PUERTAS_AMARILLO = [(46.9, -14.0, 8.0)")
rep("_plat = [(hx0, hy0), (hx1, hy0), (hx1, -16.0), (hx1 - 2.4, -16.0), (hx1 - 2.4, -8.0), (hx1, -8.0), (hx1, hy1), (hx0, hy1)]", "_plat = HALL_ALTO")
rep("gradas(gh, hx1 - 2.4, -16.0, hx1, -8.0, 'E', ZH_HALL)", """def rampa(mb, x0, y0, x1, y1, hacia, zh, m_=None):
    # rampa que baja de zh a 0 hacia 'E' o 'S' dentro del rectangulo
    if hacia == 'E':
        v = [(x0, y0, zh), (x0, y1, zh), (x1, y1, .03), (x1, y0, .03)]
    else:
        v = [(x0, y1, zh), (x1, y1, zh), (x1, y0, .03), (x0, y0, .03)]
    v = v + [(x, y, 0) for x, y, z in v]
    mb.raw(v, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], m_ or M['concreto'])


RAMPA_M = mat('rampa_hall', (.62, .66, .50), .8)
gradas(gh, 34.6, -17.8, 37.8, -2.3, 'E', ZH_HALL)                 # gradas anchas que bajan al nivel del Amarillo (plano tecnico)
rampa(gh, 34.6, -20.2, 41.0, -18.2, 'E', ZH_HALL, RAMPA_M)
for _yb in (-17.8, -10.0, -2.3):
    beam(gh, (34.6, _yb, ZH_HALL + .9), (37.8, _yb, .9), .04, M['acero'])
for _ya, _yb in ((hy0 + .3, -20.2), (-2.3, hy1 - .3)):            # baranda del borde alto
    beam(gh, (34.6, _ya, ZH_HALL + .9), (34.6, _yb, ZH_HALL + .9), .05, M['acero'])
G[('base', 'Tapetes')].prism(rect(.2, -14.2, 11.2, 1.2), ZH_HALL + .01, .05, mat('tapete_grupo_effi', (.05, .22, .55), .9))
flat_text('AUDITORIO GRUPO EFFI', (5.7, -6.5, ZH_HALL + .08), 1.0, M['blanco'], 'base')""")
rep("gradas(gh, hx0 - 2.6, -21.0, hx0 - .2, -14.0, 'O', ZH_HALL)", "gradas(gh, hx0 - 2.8, -18.8, hx0 - .2, -13.8, 'O', ZH_HALL)")
rep("gradas(gh, hx0, -37.8, 47.2, -35.0, 'S', ZH_HALL)", """gradas(gh, 1.7, -39.8, 47.2, -34.4, 'S', ZH_HALL, 12)
for _xr in (-1.2, 20.2, 34.8):                                    # rampas junto a las gradas (rayadas en el plano)
    rampa(gh, _xr, -46.5, _xr + 2.9, -34.4, 'S', ZH_HALL, RAMPA_M)""")
rep("(hx0, -35.0, ZH_HALL + .9), .05, M['acero'])", "(hx0, -34.4, ZH_HALL + .9), .05, M['acero'])")
rep("for _x in (hx0 + .2, 8.5, 18.2, 27.9, 37.6, 47.0):", "for _x in (1.8, 10.5, 20.1, 23.2, 29.0, 34.7, 37.8, 47.0):")
rep("beam(gh, (_x, -35.0, ZH_HALL + .9), (_x, -37.8, .9), .04, M['acero'])", "beam(gh, (_x, -34.4, ZH_HALL + .9), (_x, -39.8, .9), .04, M['acero'])")
rep("ZH_HALL if y > -35.0 else (0 if y < -37.8 else ZH_HALL * (y + 37.8) / 2.8)", "ZH_HALL if y > -34.4 else (0 if y < -39.8 else ZH_HALL * (y + 39.8) / 5.4)")
rep("gradas(gh, 30.0, hy1 + .2, 36.0, hy1 + 2.6, 'N', ZH_HALL)", "gradas(gh, 27.5, hy1 + .2, 33.5, hy1 + 2.6, 'N', ZH_HALL)")
# escaleras al Azul: por fuera del borde occidental del Hall (plano), con vano en el piso del Azul
rep("hl.box((hx0 + 2.6, -11.0, 0), (4.6, 4.8, HH - 1.6), MATS['muro_Azul'])", "hl.box((hx0 - 2.2, -11.6, 0), (2.6, 2.6, HH - 1.6), MATS['muro_Azul'])")
rep("hl.box((hx0 + 5.0, -11.0, 0), (.2, 2.2, 2.4), M['acero'])", "hl.box((hx0 - .85, -11.6, ZH_HALL), (.12, 1.6, 2.3), M['acero'])")
rep("    xa = hx0 + 10.0 - (i + 1) * (10.0 / n_g)", "    xa = hx0 - (i + 1) * (5.5 / n_g)")
rep("    hl.prism(rect(xa, -8.2, xa + 10.0 / n_g + .02, hy1 - .8), 0,", "    hl.prism(rect(xa, -9.7, xa + 5.5 / n_g + .02, -1.2), 0,")
rep("for yb in (-8.2, -3.4, hy1 - .8):", "for yb in (-9.7, -5.45, -1.2):")
rep("beam(hl, (hx0 + 10.0, yb, ZH_HALL + 1.0), (hx0, yb, Z_UP + 1.0), .05, M['acero'])", "beam(hl, (hx0, yb, ZH_HALL + 1.0), (hx0 - 5.5, yb, Z_UP + 1.0), .05, M['acero'])")
rep("aviso(hl, 'PABELLÓN AZUL', (hx0 + 6.5, -4.5), 9, 7.4, math.pi / 2)", "aviso(hl, 'PABELLÓN AZUL', (hx0 + .5, -5.45), 8.5, 7.4, math.pi / 2)")
rep("aviso(hl, 'PABELLÓN ROJO', (hx0 + .6, -17.5), 7, 3.4, math.pi / 2, .8, .42)", "aviso(hl, 'PABELLÓN ROJO', (hx0 + .6, -16.3), 5, 4.6, math.pi / 2, .8, .42)")
rep("pavilion(AZUL, Z_UP, 7.5, 'Azul', 'sup', None, gaps=PUERTAS_AZUL_VERDE)",
    """AZUL_N = [(-61.6, -22.2), (-1.9, -22.2), (-1.9, -9.7), (-6.7, -9.7), (-6.7, -1.2), (-1.9, -1.2), (-1.9, 19.6), (-61.6, 19.6)]   # vano de la escalera
pavilion(AZUL_N, Z_UP, 7.5, 'Azul', 'sup', None, gaps=PUERTAS_AZUL_VERDE + [(-6.7, -5.45, 8.5)])""")

# ================= Zona VIP del Amarillo con catenarias + pasos en la division del Auditorio Marketing (plano tecnico)
rep("PUERTAS_AMARILLO = ", "PASOS_DIV_AM = [(49.6, -55.2, 4.0), (86.0, -55.2, 4.0), (59.3, -55.2, 1.8), (76.9, -55.2, 1.8)]   # salida, ingreso y 2 accesos VIP\nPUERTAS_AMARILLO = ")
rep("(47.4, -51.0, 3.5)]", "(47.4, -51.0, 3.5)] + PASOS_DIV_AM")
rep("gaps=[(47.0, -60.0, 6.0)])", "gaps=[(47.0, -98.0, 3.0), (47.0, -75.0, 3.0)] + PASOS_DIV_AM)")
rep("mat('division_temporal', (.05, .05, .06), .9))", """mat('division_temporal', (.05, .05, .06), .9))
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
_fin_vip = None""")
# tarima pequena del Auditorio Grupo Effi, contra el costado norte del Hall (marcada por Alexander); sin muros ni divisiones
rep("flat_text('AUDITORIO GRUPO EFFI', (5.7, -6.5, ZH_HALL + .08), 1.0, M['blanco'], 'base')",
    "flat_text('AUDITORIO GRUPO EFFI', (5.7, -6.5, ZH_HALL + .08), 1.0, M['blanco'], 'base')\nG[('base', 'Tarimas')].box((5.4, .2, ZH_HALL), (5.0, 2.2, .4), M['negro'])   # tarima pequena del Auditorio Grupo Effi")

# ================= Zona VIP del puente Azul <-> Verde: catenarias en el perimetro punteado (sin mas divisiones)
rep("G[('ext_sup', 'Cubiertas')].prism(VIPV, Z_UP + 8, .5, M['vip'])",
    """G[('ext_sup', 'Cubiertas')].prism(VIPV, Z_UP + 8, .5, M['vip'])
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
flat_text('ZONA VIP', (-31.0, 38.0, Z_UP + .42), 1.6, M['blanco'], 'sup')""")

# ================= Dos puentes Verde <-> zona verde HV1/HV2 <-> Blanco (plano tecnico) y bloque de la Zona IA (enfermeria, banos, HV3)
rep("def is_up(c):\n    return pip(c, AZUL) or pip(c, VERDE) or pip(c, VIPV) or pip(c, ANEXO)",
    "BLOQUE_IA = [(-8.2, 72.8), (5.7, 72.8), (5.7, 97.5), (-8.2, 97.5)]     # enfermeria, banos y auditorio HV3 (nivel alto del Verde)\n\n\ndef is_up(c):\n    return pip(c, AZUL) or pip(c, VERDE) or pip(c, VIPV) or pip(c, ANEXO) or pip(c, BLOQUE_IA)")
rep("(22.5, 98.0, 18.0), (5.9, 41.5, 5.0)]", "(22.5, 98.0, 18.0)]")
rep("(-2.4, 72.8, 5.0)])", "(-8.95, 72.8, 5.5), (-8.2, 88.8, 15.2), (-3.9, 81.25, 8.8), (0.4, 77.0, 8.6)])")
rep("[(0.4, 76.5, 5.0)])", "[(-1.2, 72.8, 4.0)])")
block("pu = G[('base', 'Puente_Verde_Blanco')]", "aviso(pu, 'AUDITORIO COMUNIDADES'", """pu = G[('base', 'Puentes_Verde_Blanco')]
P1X0, P1X1, P2X0, P2X1, PY0_, PY1_ = -11.7, -6.2, -3.2, .75, 37.7, 72.8
pu.prism(rect(P1X0, PY0_, P1X1, PY1_), Z_UP - .45, .5, M['concreto'])        # puente 1: a nivel, zona verde HV1/HV2 <-> Verde alto
for _xr in (P1X0 + .1, P1X1 - .1):
    beam(pu, (_xr, PY0_, Z_UP + 1.05), (_xr, PY1_, Z_UP + 1.05), .06, M['acero'])
    for k in range(13):
        pu.box((_xr, PY0_ + (PY1_ - PY0_) * k / 12, Z_UP), (.06, .06, 1.05), M['acero'])
_v = [(P2X0, PY0_, Z_UP), (P2X1, PY0_, Z_UP), (P2X1, PY1_, .15), (P2X0, PY1_, .15)]   # puente 2: baja a la planta baja del Verde
_v += [(x, y, z - .45) for x, y, z in _v]
pu.raw(_v, [(3, 2, 1, 0), (4, 5, 6, 7), (1, 5, 4, 0), (2, 6, 5, 1), (3, 7, 6, 2), (0, 4, 7, 3)], M['concreto'])
for _xr in (P2X0 + .1, P2X1 - .1):
    beam(pu, (_xr, PY0_, Z_UP + 1.05), (_xr, PY1_, 1.2), .06, M['acero'])
    for k in range(13):
        u = k / 12; pu.box((_xr, PY0_ + (PY1_ - PY0_) * u, Z_UP + (.15 - Z_UP) * u), (.06, .06, 1.05), M['acero'])
for k in range(1, 4):                                     # apoyos de los dos puentes
    yc = PY0_ + (PY1_ - PY0_) * k / 4
    for _xr in (P1X0 + .7, P1X1 - .7):
        pu.raw(*CYL8, M['concreto'], (_xr, yc, 0), (.28, .28, Z_UP - .45))
    zc = Z_UP + (.15 - Z_UP) * k / 4 - .45
    if zc > .4:
        for _xr in (P2X0 + .5, P2X1 - .5):
            pu.raw(*CYL8, M['concreto'], (_xr, yc, 0), (.25, .25, zc))
pu.prism(rect(5.3, 24.0, 8.3, 27.0), Z_UP - .3, .3, M['concreto'])           # descanso y escalera de la zona verde al Blanco
gradas(pu, 6.1, 27.0, 8.3, 39.0, 'N', Z_UP - .3, 26)
beam(pu, (8.3, 27.0, Z_UP + .7), (8.3, 39.0, .9), .05, M['acero'])
# bloque de la Zona IA (nivel alto del Verde, junto al Blanco): enfermeria, banos y auditorio HV3 Lucid Bot
ia = G[('sup', 'Zona_IA_bloque')]
G[('sup', 'Pisos')].prism(BLOQUE_IA, Z_UP - .45, .5, MATS['piso_Verde'])
for a_, b_ in (((5.7, 72.8), (5.7, 97.5)), ((5.7, 97.5), (-8.2, 97.5)), ((-8.2, 97.5), (-8.2, 96.3)), ((.4, 72.8), (5.7, 72.8))):
    G[('sup', 'Muros_bajos')].seg(a_, b_, .5, Z_UP, WALL_LOW, MATS['muro_Verde'])
    G[('ext_sup', 'Muros_altos')].seg(a_, b_, .5, Z_UP + WALL_LOW, 16.5 - Z_UP + .6 - WALL_LOW, MATS['fachada_pab'])
G[('ext_sup', 'Cubiertas')].prism(BLOQUE_IA, 17.1, 1.5, MATS.get('techo_Verde', MATS['muro_Verde']), side=MATS['muro_Verde'])
for _c in ((5.2, 73.3), (5.2, 85.0), (5.2, 97.0), (-7.7, 85.0), (-7.7, 97.0), (.9, 73.3)):
    G[('ext_base', 'Cerramiento_nivel_inferior')].raw(*CYL8, M['concreto'], (_c[0], _c[1], 0), (.4, .4, Z_UP - .45))
ia.walls(rect(.9, 73.3, 5.4, 81.0), Z_UP, 2.8, .15, M['blanco'], skip=(3,))                    # enfermeria
ia.box((3.1, 77.1, Z_UP + 2.8), (4.5, 7.7, .12), M['blanco'])
wall_text('ENFERMERÍA', (.75, 77.1, Z_UP + 2.1), .42, mat('cruz_roja', (.75, .05, .08), .5), 'sup', math.pi / 2)
ia.box((1.1, 84.8, Z_UP), (9.0, 6.4, 2.9), M['concreto'])                                       # banos
wall_text('BAÑOS', (-3.5, 84.8, Z_UP + 2.0), .5, M['negro'], 'sup', math.pi / 2)
ia.box((-3.5, 89.6, Z_UP), (.2, 2.6, 2.5), mat('puerta_auditorio_ia', (.10, .35, .18), .5))     # entrada del auditorio (marcada en rojo)
aviso(ia, 'AUDITORIO ZONA IA  ·  LUCID BOT', (-3.6, 92.6), 9.0, Z_UP + 2.7, math.pi / 2, .9, .42, 'sup')
""")
rep("aviso(pu, 'AUDITORIO COMUNIDADES', (.7, 76.5), 6.0, 3.3, math.pi / 2, .8, .36, 'base')", "aviso(pu, 'AUDITORIO COMUNIDADES', (-1.2, 72.5), 4.2, 3.3, 0, .8, .26, 'base')")

# ================= Zona verde HV1/HV2 al nivel del Blanco (aclaracion de Alexander): puente 1 sube al Verde alto, puente 2 a nivel
rep("pip(c, ANEXO) or pip(c, BLOQUE_IA)", "pip(c, BLOQUE_IA)")
rep("G[('sup', 'Pisos')].prism(ANEXO, Z_UP - .45, .5, MATS['piso_Verde'])", "G[('base', 'Pisos')].prism(ANEXO, -.25, .32, MATS['piso_Verde'])")
rep("ex.walls(ANEXO, 0, H_LOW, .4, MATS['muro_Verde_bajo'], skip=(3,))",
    "walls_gaps(ex, ANEXO, 0, WALL_LOW, .4, MATS['muro_Verde_bajo'], [(-8.95, 37.7, 5.5), (-1.2, 37.7, 4.0), (5.3, 27.7, 3.2)], skip=(3,))")
rep("(22.5, 98.0, 18.0)]", "(22.5, 98.0, 18.0), (5.9, 27.7, 3.2)]")
rep("pu.prism(rect(P1X0, PY0_, P1X1, PY1_), Z_UP - .45, .5, M['concreto'])",
    """_w = [(P1X0, PY0_, .15), (P1X1, PY0_, .15), (P1X1, PY1_, Z_UP), (P1X0, PY1_, Z_UP)]
_w += [(x, y, max(0, z - .45)) for x, y, z in _w]
pu.raw(_w, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['concreto'])""")
rep("    beam(pu, (_xr, PY0_, Z_UP + 1.05), (_xr, PY1_, Z_UP + 1.05), .06, M['acero'])", "    beam(pu, (_xr, PY0_, 1.2), (_xr, PY1_, Z_UP + 1.05), .06, M['acero'])")
rep("        pu.box((_xr, PY0_ + (PY1_ - PY0_) * k / 12, Z_UP), (.06, .06, 1.05), M['acero'])", "        pu.box((_xr, PY0_ + (PY1_ - PY0_) * k / 12, .15 + (Z_UP - .15) * k / 12), (.06, .06, 1.05), M['acero'])")
rep("_v = [(P2X0, PY0_, Z_UP), (P2X1, PY0_, Z_UP), (P2X1, PY1_, .15), (P2X0, PY1_, .15)]", "_v = [(P2X0, PY0_, .5), (P2X1, PY0_, .5), (P2X1, PY1_, .5), (P2X0, PY1_, .5)]")
rep("    beam(pu, (_xr, PY0_, Z_UP + 1.05), (_xr, PY1_, 1.2), .06, M['acero'])", "    beam(pu, (_xr, PY0_, 1.55), (_xr, PY1_, 1.55), .06, M['acero'])")
rep("        u = k / 12; pu.box((_xr, PY0_ + (PY1_ - PY0_) * u, Z_UP + (.15 - Z_UP) * u), (.06, .06, 1.05), M['acero'])", "        u = k / 12; pu.box((_xr, PY0_ + (PY1_ - PY0_) * u, .5), (.06, .06, 1.05), M['acero'])")
rep("        pu.raw(*CYL8, M['concreto'], (_xr, yc, 0), (.28, .28, Z_UP - .45))", "        pu.raw(*CYL8, M['concreto'], (_xr, yc, 0), (.28, .28, max(.2, Z_UP * k / 4 - .45)))")
rep("    zc = Z_UP + (.15 - Z_UP) * k / 4 - .45", "    zc = 0")
rep("pu.prism(rect(5.3, 24.0, 8.3, 27.0), Z_UP - .3, .3, M['concreto'])", "_sin_escalera = None")
rep("gradas(pu, 6.1, 27.0, 8.3, 39.0, 'N', Z_UP - .3, 26)", "_sin_escalera = None")
rep("beam(pu, (8.3, 27.0, Z_UP + .7), (8.3, 39.0, .9), .05, M['acero'])", "_sin_escalera = None")

# ================= Pabellon Blanco en tres terrazas (gradas transversales marcadas por Alexander)
rep("def is_up(c):", """def z_blanco(y):
    # el Blanco baja en dos lineas de gradas desde el nivel del Hall (sur) hasta el nivel de la Plazoleta (norte)
    return ZH_HALL if y < 31.35 else (ZH_HALL / 2 if y < 44.85 else 0.)


def is_up(c):""")
rep("(ZH_HALL if (pip(c, HALL_ALTO) or pip(c, PLANCHA_COMIDAS)) else 0.)",
    "(ZH_HALL if (pip(c, HALL_ALTO) or pip(c, PLANCHA_COMIDAS) or pip(c, ANEXO)) else (z_blanco(c[1]) if pip(c, E['Blanco']) else 0.))")
rep("pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', None, gaps=PUERTAS_BLANCO)",
    """pavilion(E['Blanco'], 0, 13.5, 'Blanco', 'base', None, gaps=PUERTAS_BLANCO)
_b = bbox(E['Blanco']); PISO_BL = MATS.get('int_Blanco', MATS['piso_Blanco'])
G[('base', 'Pisos')].prism(rect(_b[0], _b[1], _b[2], 30.0), 0, ZH_HALL, M['concreto'], top=PISO_BL)
G[('base', 'Pisos')].prism(rect(_b[0], 30.0, _b[2], 43.5), 0, ZH_HALL / 2, M['concreto'], top=PISO_BL)
gb = G[('base', 'Gradas_Blanco')]
for _y0, _zb in ((30.0, ZH_HALL / 2), (43.5, 0.)):
    for i in range(4):
        gb.prism(rect(_b[0], _y0 + i * .675, _b[2] - 3.4, _y0 + (i + 1) * .675 + .01), 0, _zb + ZH_HALL / 2 * (4 - i) / 5, M['arenisca'] if i % 2 else M['concreto'])
    _r = [(_b[2] - 3.4, _y0, _zb + ZH_HALL / 2), (_b[2], _y0, _zb + ZH_HALL / 2), (_b[2], _y0 + 6.0, _zb + .03), (_b[2] - 3.4, _y0 + 6.0, _zb + .03)]
    _r += [(x, y, 0) for x, y, z in _r]
    gb.raw(_r, [(3, 2, 1, 0), (4, 5, 6, 7), (1, 5, 4, 0), (2, 6, 5, 1), (3, 7, 6, 2), (0, 4, 7, 3)], mat('rampa_blanco', (.62, .66, .50), .8))
    for _x in (_b[0] + 8.0, (_b[0] + _b[2]) / 2, _b[2] - 3.4):
        beam(gb, (_x, _y0, _zb + ZH_HALL / 2 + .9), (_x, _y0 + 2.7, _zb + .9), .04, M['acero'])""")
rep("gradas(gh, 9.0, hy1 + .2, 15.0, hy1 + 2.6, 'N', ZH_HALL)", "_sin_gradas_blanco = None")
rep("gradas(gh, 27.5, hy1 + .2, 33.5, hy1 + 2.6, 'N', ZH_HALL)", "_sin_gradas_blanco = None")
rep("G[('base', 'Pisos')].prism(ANEXO, -.25, .32, MATS['piso_Verde'])", "G[('base', 'Pisos')].prism(ANEXO, 0, ZH_HALL, M['concreto'], top=MATS['piso_Verde'])")
rep("_w = [(P1X0, PY0_, .15), (P1X1, PY0_, .15),", "_w = [(P1X0, PY0_, ZH_HALL), (P1X1, PY0_, ZH_HALL),")
rep(".15 + (Z_UP - .15) * k / 12), (.06, .06, 1.05)", "ZH_HALL + (Z_UP - ZH_HALL) * k / 12), (.06, .06, 1.05)")
rep("beam(pu, (_xr, PY0_, 1.2), (_xr, PY1_, Z_UP + 1.05), .06, M['acero'])", "beam(pu, (_xr, PY0_, ZH_HALL + 1.05), (_xr, PY1_, Z_UP + 1.05), .06, M['acero'])")
rep("_v = [(P2X0, PY0_, .5), (P2X1, PY0_, .5), (P2X1, PY1_, .5), (P2X0, PY1_, .5)]", "_v = [(P2X0, PY0_, ZH_HALL), (P2X1, PY0_, ZH_HALL), (P2X1, PY1_, .46), (P2X0, PY1_, .46)]")
rep("beam(pu, (_xr, PY0_, 1.55), (_xr, PY1_, 1.55), .06, M['acero'])", "beam(pu, (_xr, PY0_, ZH_HALL + 1.05), (_xr, PY1_, 1.5), .06, M['acero'])")
rep("u = k / 12; pu.box((_xr, PY0_ + (PY1_ - PY0_) * u, .5), (.06, .06, 1.05), M['acero'])", "u = k / 12; pu.box((_xr, PY0_ + (PY1_ - PY0_) * u, ZH_HALL + (.46 - ZH_HALL) * u), (.06, .06, 1.05), M['acero'])")
rep("crowd('base', (7, 3, 37, 96), 130, 0)", "crowd('base', (7, 3, 37, 96), 130, lambda x, y: z_blanco(y))")

# ================= Pasillo Grupo Effi: conecta el Hall con la zona verde HV1/HV2 (planta media), con tapete azul
rep("PUERTAS_HALL = [(12.0, 1.8, 6.0),", "PUERTAS_HALL = [(1.4, 1.8, 3.0), (12.0, 1.8, 6.0),")
rep("[(-8.95, 37.7, 5.5), (-1.2, 37.7, 4.0), (5.3, 27.7, 3.2)], skip=(3,))", "[(-8.95, 37.7, 5.5), (-1.2, 37.7, 4.0), (5.3, 27.7, 3.2), (2.7, 20.1, 5.4)])")
rep("G[('base', 'Pisos')].prism(ANEXO, 0, ZH_HALL, M['concreto'], top=MATS['piso_Verde'])",
    """G[('base', 'Pisos')].prism(ANEXO, 0, ZH_HALL, M['concreto'], top=MATS['piso_Verde'])
G[('base', 'Pisos')].prism(rect(-.2, 1.8, 5.6, 20.1), 0, ZH_HALL, M['concreto'], top=mat('tapete_grupo_effi', (.05, .22, .55), .9))   # pasillo Grupo Effi
beam(G[('base', 'Gradas_Hall')], (-.2, 2.0, ZH_HALL + .95), (-.2, 20.0, ZH_HALL + .95), .05, M['acero'])
flat_text('GRUPO EFFI', (2.7, 11.0, ZH_HALL + .06), .9, M['blanco'], 'base')""")

# ================= Gradas Hall -> Azul visibles tambien en la vista por niveles (capa base) y mas anchas en planta
rep("    hl.prism(rect(xa, -9.7, xa + 5.5 / n_g + .02, -1.2), 0,", "    gh.prism(rect(xa, -9.7, xa + 5.5 / n_g + .02, -1.2), 0,")
rep("beam(hl, (hx0, yb, ZH_HALL + 1.0), (hx0 - 5.5, yb, Z_UP + 1.0), .05, M['acero'])", "beam(gh, (hx0, yb, ZH_HALL + 1.0), (hx0 - 5.5, yb, Z_UP + 1.0), .05, M['acero'])")

# ================= Mas altura (pedido de Alexander): Rojo al doble -> sube el nivel Azul/Verde; Hall a 2.4 m; pabellones mas altos
rep("Z_UP, H_LOW = 5.6, 5.2 ", "Z_UP, H_LOW = 11.0, 10.5 ")
rep("ZH_HALL = 1.2 ", "Z_MEZ = 8.0                                    # mezanine de Grupo Effi en el Hall\nZH_HALL = 2.4 ")
_a = s.index("mz = G[('sup', 'Hall_mezanine_Grupo_Effi')]"); _b = s.index("for k in ():", _a)
s = s[:_a] + s[_a:_b].replace('Z_UP', 'Z_MEZ') + s[_b:]
rep("(20, -17.5), Z_UP + 9.5, 'sup'", "(20, -17.5), Z_MEZ + 13.5, 'sup'")
s = s.replace("aviso(hl, ", "aviso_h(hl, ")
rep("AVISO = mat('aviso_negro', (.03, .03, .04), .5)", "AVISO = mat('aviso_negro', (.03, .03, .04), .5)\naviso_h = lambda mb, texto, c, largo, z, *a_, **k_: aviso(mb, texto, c, largo, z + 2.2, *a_, **k_)   # avisos del Hall: suben con el piso")
# escalera Hall -> Azul mas larga (sube 8.6 m)
rep("n_g = 28 ", "n_g = 52 ")
rep("    xa = hx0 - (i + 1) * (5.5 / n_g)", "    xa = hx0 - (i + 1) * (13.0 / n_g)")
rep("xa + 5.5 / n_g + .02, -1.2), 0,", "xa + 13.0 / n_g + .02, -1.2), 0,")
rep("(hx0 - 5.5, yb, Z_UP + 1.0)", "(hx0 - 13.0, yb, Z_UP + 1.0)")
rep("(-6.7, -9.7), (-6.7, -1.2)", "(-14.2, -9.7), (-14.2, -1.2)")
rep("[(-6.7, -5.45, 8.5)]", "[(-14.2, -5.45, 8.5)]")
# pabellones mas altos
s = s.replace("0, 14.5, 'Amarillo'", "0, 19.0, 'Amarillo'")
rep("bbox(_aB)[1] + .3), 14.5, 1.5,", "bbox(_aB)[1] + .3), 19.0, 1.5,")
rep(".12, WALL_LOW, 14.5 - WALL_LOW, M['vidrio'])", ".12, WALL_LOW, 19.0 - WALL_LOW, M['vidrio'])")
rep("pavilion(E['Blanco'], 0, 13.5,", "pavilion(E['Blanco'], 0, 18.0,")
rep("HB = 13.5", "HB = 18.0")
rep("pavilion(E['Hall'], 0, 11.5,", "pavilion(E['Hall'], 0, 18.0,")
rep("HH = 11.5", "HH = 18.0")
rep("pavilion(AZUL_N, Z_UP, 7.5,", "pavilion(AZUL_N, Z_UP, 9.5,")
rep("HA = 7.5", "HA = 9.5")
s = s.replace("16.5 - Z_UP + .6", "24.0 - Z_UP + .6")
rep("prism(BLOQUE_IA, 17.1, 1.5,", "prism(BLOQUE_IA, 24.6, 1.5,")
rep("ZS_V = Z_UP + 7.6", "ZS_V = Z_UP + 8.4")
rep("(_xv, _ye, Z_UP), (.3, .3, 7.6))", "(_xv, _ye, Z_UP), (.3, .3, 8.4))")
# pines por encima de las cubiertas nuevas
s = s.replace("Z_UP + 14.5, 'sup'", "Z_UP + 16.5, 'sup'")
rep("Z_UP + 11, 'sup'", "Z_UP + 13, 'sup'")
rep("(30, -6), 14.5)", "(30, -6), 21.5)")
rep("(22, 52), 16.5)", "(22, 52), 21.5)")
rep("(68, -18), 17.5)", "(68, -18), 22.5)")
rep("(68, -80), 17.5)", "(68, -80), 22.5)")
# gradas mas altas: mas peldanos y mas fondo (como en el plano tecnico)
rep("def gradas(mb, x0, y0, x1, y1, hacia, zh, n=8):", "def gradas(mb, x0, y0, x1, y1, hacia, zh, n=14):")
rep("gradas(gh, 34.6, -17.8, 37.8, -2.3, 'E', ZH_HALL)", "gradas(gh, 34.6, -17.8, 40.4, -2.3, 'E', ZH_HALL)")
rep("beam(gh, (34.6, _yb, ZH_HALL + .9), (37.8, _yb, .9), .04, M['acero'])", "beam(gh, (34.6, _yb, ZH_HALL + .9), (40.4, _yb, .9), .04, M['acero'])")
rep("gradas(gh, hx0 - 2.8, -18.8, hx0 - .2, -13.8, 'O', ZH_HALL)", "gradas(gh, hx0 - 6.6, -18.8, hx0 - .2, -13.8, 'O', ZH_HALL)")
rep("    for i in range(4):\n        gb.prism(rect(_b[0], _y0 + i * .675, _b[2] - 3.4, _y0 + (i + 1) * .675 + .01), 0, _zb + ZH_HALL / 2 * (4 - i) / 5,",
    "    for i in range(8):\n        gb.prism(rect(_b[0], _y0 + i * .3375, _b[2] - 3.4, _y0 + (i + 1) * .3375 + .01), 0, _zb + ZH_HALL / 2 * (8 - i) / 9,")

# ================= Hall central y tramo trasero del Blanco casi al doble de altura (4.5 m): gradas mas altas, subida al Azul mas corta
rep("ZH_HALL = 2.4 ", "ZH_HALL = 4.5 ")
rep("Z_MEZ = 8.0 ", "Z_MEZ = 9.6 ")
rep("largo, z + 2.2, *a_, **k_)", "largo, z + 4.3, *a_, **k_)")
rep("def gradas(mb, x0, y0, x1, y1, hacia, zh, n=14):", "def gradas(mb, x0, y0, x1, y1, hacia, zh, n=26):")
rep("gradas(gh, 1.7, -39.8, 47.2, -34.4, 'S', ZH_HALL, 12)", "gradas(gh, 1.7, -39.8, 47.2, -34.4, 'S', ZH_HALL, 26)")
rep("    for i in range(8):\n        gb.prism(rect(_b[0], _y0 + i * .3375, _b[2] - 3.4, _y0 + (i + 1) * .3375 + .01), 0, _zb + ZH_HALL / 2 * (8 - i) / 9,",
    "    for i in range(12):\n        gb.prism(rect(_b[0], _y0 + i * .225, _b[2] - 3.4, _y0 + (i + 1) * .225 + .01), 0, _zb + ZH_HALL / 2 * (12 - i) / 13,")
rep("n_g = 52 ", "n_g = 40 ")

# ================= Escalera en C Hall -> segundo piso Grupo Effi (plano tecnico)
rep("mz.prism(rect(MX0, MY0, MX1, MY1), Z_MEZ - .5, .5,", "mz.prism([(MX0, MY0), (MX1, MY0), (MX1, MY1), (MX0, MY1), (MX0, -15.0), (10.4, -15.0), (10.4, -19.4), (MX0, -19.4)], Z_MEZ - .5, .5,")
rep("for xm in (MX0 + 4, (MX0 + MX1) / 2 - 6,", "for xm in (MX0 + 9.5, (MX0 + MX1) / 2 - 4,")
rep("    hl.prism(rect(xe, MY1 + .2, xe + 10.0 / n_e + .02, MY1 + 2.4), 0, ZH_HALL + (i + 1) * (Z_MEZ - .5 - ZH_HALL) / n_e, M['concreto'])",
    """    _h = ZH_HALL + (i + 1) * (Z_MEZ - ZH_HALL) / n_e; _p = 4.6 / (n_e // 2)
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
    gh.box((9.8, _ys, ZH_HALL), (1.4, .25, 1.1), mat('acceso_vip_verde', (.15, .65, .2), .5))""")

# ================= Lateral occidental del Gran Salon: pasillo interior (VIP, networking) y pasillo exterior (plano tecnico)
rep("lb.box((_ex0 + .3, (_sy0 + _sy1) / 2, Z_GS + .4), (.08, _sy1 - _sy0 - 4, 3.2), M['vidrio'])",
    "lb.box((-19.7, 233.5, Z_GS + .1), (.08, 61.0, 3.6), M['vidrio'])")
rep("mur = G[('multi', 'Lobby_murales')]",
    """for _ym in range(205, 264, 4):                           # montantes de la vidriera entre pasillo interior y exterior
    lb.box((-19.7, _ym, Z_GS), (.12, .12, 3.7), M['acero'])
zona_vip('Gran_Salon_1', -19.3, 209.8, -11.9, 230.3, Z_GS, 'gs', cortes=(230.3,))
zona_vip('Gran_Salon_2', -19.3, 231.8, -13.6, 262.0, Z_GS, 'gs', cortes=(231.8,))
lb.box((-17.0, 223.5, Z_GS), (1.9, 3.9, 1.1), M['negro'], top=M['blanco'])                    # barra 4x2 de la zona VIP
MESA_AZ = mat('mesa_networking', (.10, .22, .62), .5)
for _ym in [181.0 + 2.3 * k for k in range(15)]:          # mesas altas de networking junto a la vidriera
    lb.raw(*CYL8, M['acero'], (-21.0, _ym, Z_GS), (.06, .06, 1.05)); lb.raw(*CYL8, MESA_AZ, (-21.0, _ym, Z_GS + 1.05), (.38, .38, .05))
for _c in ((-18.0, 192.0), (-18.0, 194.6), (-16.2, 200.6), (-16.2, 203.0), (-18.4, 200.6), (-18.4, 203.0)):
    lb.raw(*CYL8, M['acero'], (_c[0], _c[1], Z_GS), (.06, .06, 1.05)); lb.raw(*CYL8, MESA_AZ, (_c[0], _c[1], Z_GS + 1.05), (.38, .38, .05))
lb.box((-20.2, 197.3, Z_GS + .9), (.14, 4.2, 2.3), M['negro'])                                # pantalla de la zona de networking
lb.box((-20.1, 197.3, Z_GS + 1.0), (.06, 3.9, 2.1), mat('pantalla_networking', (.05, .08, .14), .3, 0, (.30, .55, 1.0), 1.6))
for _r in range(3):
    for _k in range(10):
        lb.box((-18.6 + _r * .75, 195.3 + _k * .45, Z_GS), (.4, .4, .45), MESA_AZ)
flat_text('NETWORKING', (-17.2, 197.3, Z_GS + .1), .7, M['negro'], 'gs')
flat_text('ZONA DE PRENSA', (-16.5, 167.2, Z_GS + .1), .7, M['negro'], 'gs')
flat_text('PASILLO EXTERIOR', (-21.8, 240.0, Z_GS + .1), .6, M['negro'], 'gs')
mur = G[('multi', 'Lobby_murales')]""")

# ================= Pasillo exterior hundido al occidente del Gran Salon, visible desde la plaza (foto satelital de Alexander)
rep("for rc in (rect(PX0, 168.0, PX1, cy0), rect(PX0, cy1, PX1, PY1), rect(PX0, cy0, cx0, cy1), rect(cx1, cy0, PX1, cy1)):   # sin tapar el piso 3 de la Caja",
    "LX0 = -19.9                                  # la plaza no cubre el pasillo exterior occidental\nfor rc in (rect(PX0, 168.0, PX1, 172.0), rect(LX0, 172.0, PX1, cy0), rect(LX0, cy1, PX1, PY1), rect(LX0, cy0, cx0, cy1), rect(cx1, cy0, PX1, cy1)):   # sin tapar el piso 3 de la Caja")
rep("skip=tuple(i for i in range(len(_gp)) if max(_gp[i][1], _gp[(i + 1) % len(_gp)][1]) < 169))",
    "skip=tuple(i for i in range(len(_gp)) if max(_gp[i][1], _gp[(i + 1) % len(_gp)][1]) < 169 or max(_gp[i][0], _gp[(i + 1) % len(_gp)][0]) < -23))")
rep("lambda x, y: not (12 < x < 40 and 236 < y < 256))", "lambda x, y: x > -18.5 and not (12 < x < 40 and 236 < y < 256))")
rep("flat_text('PASILLO EXTERIOR', (-21.8, 240.0, Z_GS + .1), .6, M['negro'], 'gs')",
    """flat_text('PASILLO EXTERIOR', (-21.8, 240.0, Z_GS + .1), .6, M['negro'], 'gs')
tal = G[('terreno', 'Talud_pasillo_exterior')]
_t = [(PX0, 172.0, -.1), (PX0, PY1, -.1), (-24.6, PY1, Z_GS + .5), (-24.6, 172.0, Z_GS + .5)]            # talud verde hacia la Carrera 57
_t += [(x, y, Z_GS) for x, y, z in _t]
tal.raw(_t, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['cesped'])
tal.seg((-24.6, 172.0), (-24.6, PY1), .3, Z_GS, .5, M['arenisca'])                               # bordillo del pasillo
tal.seg((LX0, 172.0), (LX0, PY1), .25, -.6, .7, M['concreto'])                                    # borde de la plaza
for _yb in range(174, int(PY1), 3):
    tal.box((LX0, _yb, .1), (.06, .06, 1.0), M['acero'])
beam(tal, (LX0, 172.0, 1.1), (LX0, PY1, 1.1), .06, M['acero'])
beam(tal, (PX0, 172.0, 1.0), (PX0, PY1, 1.0), .06, M['acero'])""")

# ================= Carrera 57 entre el Teatro Metropolitano y la Caja de Madera (foto satelital de Alexander)
rep("def oblique(mbx, o0, o1, m, z=.02, h=.06, y0=-240, y1=260):",
    """for x0, x1, m, z in ((-82, -64, 'cesped', .06), (-64, -56, 'asfalto', .04), (-56, -50, 'cesped', .08), (-50, -42, 'asfalto', .04),
                     (-42, PX0 - .3, 'cesped', .06)):                # Carrera 57: zona verde, calzada, separador, calzada, zona verde
    mb.prism(rect(x0, 166, x1, 300), z - .06 + .1, .06, M[m])
for x in (-60, -46):
    for y in range(168, 300, 9):
        mk.box((x, y + 2, .15), (.15, 4, .02), M['linea'])


def oblique(mbx, o0, o1, m, z=.02, h=.06, y0=-240, y1=260):""")
rep("crowd('base', (-55, 170, -33, 290), 40, 0)", "crowd('base', (-29, 170, -21, 290), 0, 0)")
rep("label('TEATRO METROPOLITANO', (-124, 178), 30, (.55, .25, .15), 3.2)",
    """label('TEATRO METROPOLITANO', (-124, 178), 30, (.55, .25, .15), 3.2)
flat_text('CARRERA 57', (-60, 235, .2), 2.2, M['blanco'], 'vias')
flat_text('CARRERA 57', (-46, 235, .2), 2.2, M['blanco'], 'vias')
for _yt in range(176, 296, 13):
    tree(-36 + random.uniform(-2, 2), _yt, random.uniform(.8, 1.15), force=True); tree(-53, _yt + 5, random.uniform(.6, .9), force=True)
    tree(-72 + random.uniform(-3, 3), _yt + 3, random.uniform(.8, 1.1), force=True)
for _i, (_xc, _yc, _an) in enumerate(((-58, 190, math.pi / 2), (-62, 248, math.pi / 2), (-44, 215, -math.pi / 2), (-48, 270, -math.pi / 2))):
    car(_xc, _yc, _an)""")

# ================= Muro diagonal entre pasillo exterior e interior del Gran Salon; el balcon de la plaza sigue la misma linea
rep("LX0 = -19.9                                  # la plaza no cubre el pasillo exterior occidental\nfor rc in (rect(PX0, 168.0, PX1, 172.0), rect(LX0, 172.0, PX1, cy0), rect(LX0, cy1, PX1, PY1), rect(LX0, cy0, cx0, cy1), rect(cx1, cy0, PX1, cy1)):",
    """LX0 = -19.9


def fxw(y):
    # linea diagonal del muro que separa el pasillo exterior del interior (y del borde de la plaza encima)
    return -20.3 + (y - 172.0) * .0705


for rc in (rect(PX0, 168.0, PX1, 172.0), [(fxw(172.0), 172.0), (PX1, 172.0), (PX1, cy0), (fxw(cy0), cy0)],
           [(fxw(cy1), cy1), (PX1, cy1), (PX1, PY1), (fxw(PY1), PY1)], [(fxw(cy0), cy0), (cx0, cy0), (cx0, cy1), (fxw(cy1), cy1)], rect(cx1, cy0, PX1, cy1)):""")
rep("lb.box((-19.7, 233.5, Z_GS + .1), (.08, 61.0, 3.6), M['vidrio'])", "lb.seg((fxw(186.0), 186.0), (fxw(PY1 - 1), PY1 - 1), .1, Z_GS + .1, 3.6, M['vidrio'])")
rep("    lb.box((-19.7, _ym, Z_GS), (.12, .12, 3.7), M['acero'])", "    lb.box((fxw(_ym), _ym, Z_GS), (.12, .12, 3.7), M['acero'])")
rep("for _ym in range(205, 264, 4):                           # montantes", "for _ym in range(187, 270, 4):                           # montantes")
rep("lb.raw(*CYL12, M['concreto'], (_ex0 + 2.2, _yp, Z_GS), (.4, .4, 4.0))", "lb.raw(*CYL12, M['concreto'], (fxw(_yp) - 1.9, _yp, Z_GS), (.4, .4, 4.0))")
rep("zona_vip('Gran_Salon_1', -19.3, 209.8, -11.9, 230.3,", "zona_vip('Gran_Salon_1', -15.6, 209.8, -8.2, 230.3,")
rep("zona_vip('Gran_Salon_2', -19.3, 231.8, -13.6, 262.0,", "zona_vip('Gran_Salon_2', -13.3, 231.8, -8.2, 262.0,")
rep("lb.box((-17.0, 223.5, Z_GS), (1.9, 3.9, 1.1)", "lb.box((-13.4, 223.5, Z_GS), (1.9, 3.9, 1.1)")
rep("lb.raw(*CYL8, M['acero'], (-21.0, _ym, Z_GS), (.06, .06, 1.05)); lb.raw(*CYL8, MESA_AZ, (-21.0, _ym, Z_GS + 1.05), (.38, .38, .05))",
    "lb.raw(*CYL8, M['acero'], (fxw(_ym) + 1.1, _ym, Z_GS), (.06, .06, 1.05)); lb.raw(*CYL8, MESA_AZ, (fxw(_ym) + 1.1, _ym, Z_GS + 1.05), (.38, .38, .05))")
rep("for _ym in [181.0 + 2.3 * k for k in range(15)]:", "for _ym in [187.5 + 2.3 * k for k in range(9)]:")
rep("((-18.0, 192.0), (-18.0, 194.6), (-16.2, 200.6), (-16.2, 203.0), (-18.4, 200.6), (-18.4, 203.0))", "((-15.4, 192.0), (-15.4, 194.6), (-13.6, 200.6), (-13.6, 203.0), (-15.8, 200.6), (-15.8, 203.0))")
rep("lb.box((-20.2, 197.3, Z_GS + .9), (.14, 4.2, 2.3), M['negro'])", "lb.box((-17.2, 197.3, Z_GS + .9), (.14, 4.2, 2.3), M['negro'])")
rep("lb.box((-20.1, 197.3, Z_GS + 1.0), (.06, 3.9, 2.1),", "lb.box((-17.1, 197.3, Z_GS + 1.0), (.06, 3.9, 2.1),")
rep("lb.box((-18.6 + _r * .75, 195.3 + _k * .45, Z_GS), (.4, .4, .45), MESA_AZ)", "lb.box((-15.9 + _r * .75, 195.3 + _k * .45, Z_GS), (.4, .4, .45), MESA_AZ)")
rep("flat_text('NETWORKING', (-17.2, 197.3,", "flat_text('NETWORKING', (-13.0, 197.3,")
rep("tal.seg((LX0, 172.0), (LX0, PY1), .25, -.6, .7, M['concreto'])", "tal.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .25, -.6, .7, M['concreto'])")
rep("    tal.box((LX0, _yb, .1), (.06, .06, 1.0), M['acero'])", "    tal.box((fxw(_yb), _yb, .1), (.06, .06, 1.0), M['acero'])")
rep("beam(tal, (LX0, 172.0, 1.1), (LX0, PY1, 1.1), .06, M['acero'])", "beam(tal, (fxw(172.0), 172.0, 1.1), (fxw(PY1), PY1, 1.1), .06, M['acero'])")
rep("lambda x, y: x > -18.5 and not", "lambda x, y: x > fxw(y) + 1 and not")

# ================= Pasillo exterior parejo (pedido de Alexander): ancho uniforme, fachada continua bajo el balcon y talud paralelo
rep("_t = [(PX0, 172.0, -.1), (PX0, PY1, -.1), (-24.6, PY1, Z_GS + .5), (-24.6, 172.0, Z_GS + .5)]",
    """tal.prism([(PX0 - .3, 172.0), (fxw(172.0) - 10.0, 172.0), (fxw(PY1) - 10.0, PY1), (PX0 - .3, PY1)], Z_GS, -Z_GS + .06, M['cesped'])   # relleno verde a nivel
fac = G[('losa', 'Fachada_pasillo_exterior')]
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .35, Z_GS + 3.7, -Z_GS - 3.7 - .5, M['arenisca'])     # fachada del piso 2 sobre la vidriera
fac.seg((fxw(172.0), 172.0), (fxw(186.0), 186.0), .12, Z_GS + .1, 3.6, M['vidrio'])
fac.seg((fxw(172.0) - 5.0, 172.0), (fxw(172.0), 172.0), .4, Z_GS, -Z_GS - .5, M['arenisca'])          # remates sur y norte del pasillo
fac.seg((fxw(PY1) - 5.0, PY1), (fxw(PY1), PY1), .4, Z_GS, -Z_GS - .5, M['arenisca'])
_t = [(fxw(172.0) - 10.0, 172.0, -.1), (fxw(PY1) - 10.0, PY1, -.1), (fxw(PY1) - 4.8, PY1, Z_GS + .5), (fxw(172.0) - 4.8, 172.0, Z_GS + .5)]""")
rep("tal.seg((-24.6, 172.0), (-24.6, PY1), .3, Z_GS, .5, M['arenisca'])", "tal.seg((fxw(172.0) - 4.8, 172.0), (fxw(PY1) - 4.8, PY1), .3, Z_GS, .5, M['arenisca'])")
rep("beam(tal, (PX0, 172.0, 1.0), (PX0, PY1, 1.0), .06, M['acero'])", "beam(tal, (fxw(172.0) - 10.0, 172.0, 1.0), (fxw(PY1) - 10.0, PY1, 1.0), .06, M['acero'])")
rep("lb.raw(*CYL12, M['concreto'], (fxw(_yp) - 1.9, _yp, Z_GS), (.4, .4, 4.0))", "lb.raw(*CYL12, M['concreto'], (fxw(_yp) - 2.2, _yp, Z_GS), (.4, .4, 8.4))")
rep("flat_text('PASILLO EXTERIOR', (-21.8, 240.0, Z_GS + .1), .6, M['negro'], 'gs')", "flat_text('PASILLO EXTERIOR', (fxw(225.0) - 3.4, 225.0, Z_GS + .1), .7, M['negro'], 'gs')")
rep("OFI = [(x, max(y, 170.5)) for x, y in E['Multi_oficina']]", "OFI = [(max(x, -18.6), max(y, 170.5)) for x, y in E['Multi_oficina']]   # sin sobresalir al pasillo exterior")
rep("mu.box((-19.5, 168 + k * 5.5, Z_MULTI), (3.2, 1.4, .75), M['mesa'])", "mu.box((-16.2, 172 + k * 5.5, Z_MULTI), (3.2, 1.4, .75), M['mesa'])")

# ================= Banderas sobre el borde de la plaza (ya no flotan sobre el pasillo exterior)
rep("    ls.raw(*CYL6, M['poste'], (-24, y, 0), (.07, .07, 9.0))", "    ls.raw(*CYL6, M['poste'], (fxw(y) + 1.6, y, 0), (.07, .07, 9.0))")
rep("    ls.box((-24, y + .8, 6.0), (.06, 1.4, 2.9), M['efx_r'] if i % 2 == 0 else M['efx_n'])", "    ls.box((fxw(y) + 1.6, y + .8, 6.0), (.06, 1.4, 2.9), M['efx_r'] if i % 2 == 0 else M['efx_n'])")

# ================= Convenciones un piso mas arriba: Plazoleta/Carrera 57 = piso 2, plaza de la Caja = +4.5, Gran Salon = -4.5
rep("Z_GS, Z_MULTI = -9.0, -4.5", "Z_GS, Z_MULTI = -9.0, -4.5\nDZ_CONV = 4.5                       # el edificio de Convenciones se sube completo al final (Plazoleta = piso 2)")
rep("'pos': [round(xy[0], 2), round(xy[1], 2), round(z, 2)], 'grupo': grp})", "'pos': [round(xy[0], 2), round(xy[1], 2), round(z + (DZ_CONV if grp in ('gs', 'multi', 'caja') else 0), 2)], 'grupo': grp})")
rep("bpy.ops.wm.save_as_mainfile(filepath=str(R / 'Plaza_Mayor_mapa_v04.blend'))",
    """_raices = set(ROOT.values())
for _c in ('gs', 'multi', 'caja', 'shell', 'losa', 'huella', 'pins_gs', 'pins_multi', 'pins_caja'):
    for _o in COLL[_c].objects:
        if _o not in _raices and (_o.parent is None or _o.parent in _raices):
            _o.location.z += DZ_CONV
for _n in ('Foso_Gran_Salon_y_gradas', 'Talud_pasillo_exterior'):
    bpy.data.objects[_n].location.z += DZ_CONV
bpy.ops.wm.save_as_mainfile(filepath=str(R / 'Plaza_Mayor_mapa_v04.blend'))""")
# gradas de la Plazoleta: solo un piso (el primer tramo queda a nivel)
rep(".6 - Z_GS + Z_MULTI * (i + 1) / n1,", ".6 - Z_GS + Z_MULTI,")
rep("    beam(mb, (x, sy0, 1.0), (x, yl0, Z_MULTI + 1.0), .08, M['acero']); beam(mb, (x, yl1, Z_MULTI + 1.0), (x, sy1, Z_GS + 1.0), .08, M['acero'])",
    "    beam(mb, (x, yl1, Z_MULTI + 1.0), (x, sy1, Z_GS + 1.0), .08, M['acero'])")
rep("    beam(mb, (x, sy0, 1.0), (x, sy1, Z_GS + 1.0), .06, M['acero'])", "    beam(mb, (x, yl1, Z_MULTI + 1.0), (x, sy1, Z_GS + 1.0), .06, M['acero'])")
rep("lambda x, y: Z_GS * min(1, max(0, (y - sy0) / (sy1 - sy0))))", "lambda x, y: (Z_GS - Z_MULTI) * min(1, max(0, (y - (sy0 + 6.1)) / (sy1 - (sy0 + 6.1)))))")
rep("mb.box((sx0 + 20, sy0 - 2.5, 0), (.7, 1.2, 6.0), M['negro']); mb.box((sx0 + 20, sy0 - 3.12, 2.0)", "mb.box((sx0 + 20, sy0 - 2.5, Z_MULTI), (.7, 1.2, 6.0), M['negro']); mb.box((sx0 + 20, sy0 - 3.12, Z_MULTI + 2.0)")
rep("(((PX0 - .3, sy0), (PX0 - .3, PY1 + .3)), ((PX0 - .3, PY1 + .3), (PX1 + .3, PY1 + .3)),", "(((PX0 - .3, sy0), (PX0 - .3, 172.0)), ((-18.2, PY1 + .3), (PX1 + .3, PY1 + .3)),")
# terreno: la manga occidental baja desde la calle; ya no hay plaza a nivel ahi
rep("HX0, HY0, HX1, HY1 = PX0, sy0, PX1, PY1", "HX0, HY0, HX1, HY1 = -41.5, sy0, PX1, PY1")
rep("for poly in (rect(-62, 166, PX0, 300), rect(PX1, 166, 97, 300), rect(PX0, PY1, PX1, 300)):\n    mb.prism(poly, -.1, .12, M['pav_plaza'])",
    "for poly in (rect(-62, 166, -41.5, 300), rect(-41.5, PY1, PX0, 300), rect(PX1, 166, 97, 300), rect(PX0, PY1, PX1, 300)):\n    mb.prism(poly, -.1, .12, M['pav_plaza'])\nmb.prism(rect(-41.5, sy0, PX0 - .3, 172.0), -.6, .62, M['pav_plaza'])")
rep("(-42, PX0 - .3, 'cesped', .06)", "(-42, -41.4, 'cesped', .06)")
rep("tal.prism([(PX0 - .3, 172.0), (fxw(172.0) - 10.0, 172.0), (fxw(PY1) - 10.0, PY1), (PX0 - .3, PY1)], Z_GS, -Z_GS + .06, M['cesped'])",
    "tal.seg((-41.5, 172.0), (fxw(172.0) - 4.8, 172.0), .3, Z_GS, Z_MULTI - Z_GS, M['arenisca']); tal.seg((-41.5, PY1), (fxw(PY1) - 4.8, PY1), .3, Z_GS, Z_MULTI - Z_GS, M['arenisca'])")
rep("_t = [(fxw(172.0) - 10.0, 172.0, -.1), (fxw(PY1) - 10.0, PY1, -.1), (fxw(PY1) - 4.8, PY1, Z_GS + .5), (fxw(172.0) - 4.8, 172.0, Z_GS + .5)]",
    "_t = [(-41.5, 172.0, Z_MULTI + .1), (-41.5, PY1, Z_MULTI + .1), (fxw(PY1) - 4.8, PY1, Z_GS + .5), (fxw(172.0) - 4.8, 172.0, Z_GS + .5)]   # manga suave desde la calle")
rep("beam(tal, (fxw(172.0) - 10.0, 172.0, 1.0), (fxw(PY1) - 10.0, PY1, 1.0), .06, M['acero'])", "_sin_baranda = None")
# fachada occidental como en Street View: bandas de concreto, persiana de madera del piso 2 y antepecho de piedra de la plaza
rep("fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .35, Z_GS + 3.7, -Z_GS - 3.7 - .5, M['arenisca'])",
    """fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .5, Z_GS + 3.7, .4, M['concreto'])
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .3, Z_GS + 4.1, 3.0, PERS)
for _k in range(0, 96, 7):
    fac.seg((fxw(174.0 + _k) - .2, 174.0 + _k), (fxw(177.5 + _k) - .2, 177.5 + _k), .1, Z_GS + 5.0 + (_k % 3) * .7, .35, M['negro'])
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .5, -1.9, .4, M['concreto'])
fac.seg((fxw(172.0), 172.0), (fxw(PY1), PY1), .4, -1.5, 2.4, M['arenisca'])
tp = G[('terreno', 'Taludes_plaza_alta')]                 # taludes de cesped y gradas que suben a la plaza de la Caja (coordenadas reales)
_zh = DZ_CONV + .1
rampa(tp, PX1 + .6, 172.0, PX1 + 12.0, PY1 + .6, 'E', _zh, M['cesped'])
for _xa, _xb in ((-13.2, 6.0), (18.0, PX1 + .6)):
    _n = [(_xa, PY1 + .6, _zh), (_xb, PY1 + .6, _zh), (_xb, PY1 + 13.6, .05), (_xa, PY1 + 13.6, .05)]
    _n += [(x, y, 0) for x, y, z in _n]
    tp.raw(_n, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M['cesped'])
gradas(tp, 6.0, PY1 + .6, 18.0, PY1 + 13.6, 'N', _zh, 28)
for _x in (6.0, 12.0, 18.0):
    beam(tp, (_x, PY1 + .6, _zh + .9), (_x, PY1 + 13.6, .9), .05, M['acero'])""")

# ================= Sin el muro cafe del pasillo exterior ni el remate sur; columnas alineadas al borde del balcon (pedido de Alexander)
rep("or max(_gp[i][0], _gp[(i + 1) % len(_gp)][0]) < -23))", "or (_gp[i][0] + _gp[(i + 1) % len(_gp)][0]) / 2 < -15))")
rep("fac.seg((fxw(172.0) - 5.0, 172.0), (fxw(172.0), 172.0), .4, Z_GS, -Z_GS - .5, M['arenisca'])", "_sin_remate_sur = None")
rep("tal.seg((-41.5, 172.0), (fxw(172.0) - 4.8, 172.0), .3, Z_GS, Z_MULTI - Z_GS, M['arenisca']); ", "")
rep("lb.raw(*CYL12, M['concreto'], (fxw(_yp) - 2.2, _yp, Z_GS), (.4, .4, 8.4))", "lb.raw(*CYL12, M['concreto'], (fxw(_yp) - .25, _yp, Z_GS), (.42, .42, 8.5))")
rep("_yp = _sy0 + 4.0\nwhile _yp < _sy1 - 2:", "_yp = 175.0\nwhile _yp < PY1 - 1:")

# ================= Fachada occidental corrida hacia afuera (lo de adentro queda adentro) y muros de las gradas solo hasta la Plazoleta
rep("    return -20.3 + (y - 172.0) * .0705", "    return -23.6 + (y - 172.0) * .0705")
rep("(((PX0 - .3, sy0), (PX0 - .3, 172.0)), ((-18.2, PY1 + .3), (PX1 + .3, PY1 + .3)),", "(((-21.4, PY1 + .3), (PX1 + .3, PY1 + .3)),")
rep("    mb.seg(a_, b_, 1.0, Z_GS, -Z_GS - .05, M['arenisca'])", "    mb.seg(a_, b_, 1.0, Z_GS, Z_MULTI - Z_GS + .9, M['arenisca'])")

# ================= Curva que une la Carrera 57 con la via transversal (pedido de Alexander)
rep("for x in (-60, -46):\n    for y in range(168, 300, 9):",
    """mb.prism(rect(-64, 136, -42, 166.2), .0, .08, M['asfalto'])                    # empalme de las dos calzadas con la via transversal
mb.prism(rect(-56, 150, -50, 166.2), .02, .12, M['cesped'])
mb.raw(*CYL12, M['cesped'], (-53, 150, .02), (3.0, 3.0, .12))
for _cx, _sg in ((-78.0, 1), (-28.0, -1)):                                     # esquinas en curva (radio 14 m)
    _arc = [(_cx + _sg * 14 * math.cos(math.radians(a_)), 151.0 - 14 * math.sin(math.radians(a_))) for a_ in range(0, 91, 9)]
    _pol = [(_cx + _sg * 14, 137.0)] + _arc
    mb.prism(_pol if _sg > 0 else list(reversed(_pol)), .0, .08, M['asfalto'])
    for a_ in range(10, 90, 20):                                              # demarcacion de la curva
        mk.box((_cx + _sg * 17.5 * math.cos(math.radians(a_)), 151.0 - 17.5 * math.sin(math.radians(a_)), .1), (.15, 2.6, .02), M['linea'], -_sg * math.radians(a_))
for x in (-60, -46):
    for y in range(168, 300, 9):""")

# ================= La esquina del edificio de Convenciones es la de Convertmate: sin el pedazo de plaza/balcon que sobresalia al occidente
rep("for rc in (rect(PX0, 168.0, PX1, 172.0), [(fxw(172.0), 172.0),", "FX0 = -23.9\nfor rc in (rect(FX0, 168.0, PX1, 172.0), [(fxw(172.0), 172.0),")
_a = s.index("FY = 167.8"); _b = s.index("# --- muros laterales de piedra", _a)
s = s[:_a] + s[_a:_b].replace('PX0', 'FX0') + s[_b:]

# ================= Zona VIP exterior del Gran Salon: en el pasillo exterior, con catenaria y mesas (plano tecnico)
rep("zona_vip('Gran_Salon_2', -13.3, 231.8, -8.2, 262.0, Z_GS, 'gs', cortes=(231.8,))",
    """zve = G[('gs', 'Zona_VIP_Gran_Salon_exterior')]
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
flat_text('ZONA VIP EXTERIOR', (fxw(250.0) - 1.6, 250.0, Z_GS + .12), .7, M['blanco'], 'gs')""")
rep("flat_text('PASILLO EXTERIOR', (fxw(225.0) - 3.4, 225.0,", "flat_text('PASILLO EXTERIOR', (fxw(205.0) - 3.4, 205.0,")

# ================= Rampa oriental: sube de la Plazoleta Interamericana a la plaza de la Caja (ingreso principal), balcon y gradas arriba
rep("rampa(tp, PX1 + .6, 172.0, PX1 + 12.0, PY1 + .6, 'E', _zh, M['cesped'])",
    """RX_A, RX_B = PX1 + .5, PX1 + 8.0
rampa(tp, RX_A, 160.0, RX_B, 238.0, 'S', _zh, M['pav_plaza'])                      # rampa peatonal (recuadro negro)
tp.prism(rect(RX_A, 238.0, RX_B, 258.0), 0, _zh, M['arenisca'], top=M['pav_plaza'])   # llegada a nivel de la plaza
for _xr in (RX_A + .1, RX_B - .1):
    beam(tp, (_xr, 160.0, 1.0), (_xr, 238.0, _zh + 1.0), .06, M['acero'])
    for k in range(27):
        tp.box((_xr, 160.0 + 3 * k, _zh * k / 26), (.06, .06, 1.0), M['acero'])
gradas(tp, RX_B, 240.0, RX_B + 9.0, 258.0, 'E', _zh, 28)                           # gradas (lineas moradas)
for _yb in (240.0, 249.0, 258.0):
    beam(tp, (RX_B, _yb, _zh + .9), (RX_B + 9.0, _yb, .9), .05, M['acero'])
for _yb in range(172, 238, 3):                                                      # balcon de la plaza sobre la rampa (linea naranja)
    tp.box((PX1 + .1, _yb, _zh), (.06, .06, 1.0), M['acero'])
beam(tp, (PX1 + .1, 172.0, _zh + 1.0), (PX1 + .1, 238.0, _zh + 1.0), .06, M['acero'])
tp.seg((PX1 + .25, 172.0), (PX1 + .25, 238.0), .5, 0, _zh, M['arenisca'])
rampa(tp, RX_B, 172.0, RX_B + 9.0, 238.0, 'E', 2.6, M['cesped'])                    # talud verde al costado de la rampa
tp.prism(rect(RX_B, 258.0, RX_B + 9.0, PY1 + .6), 0, .05, M['cesped'])
rampa(tp, RX_A, 258.0, RX_B + 2.0, PY1 + .6, 'E', _zh, M['cesped'])""")

# ================= Gradas del lado de la plaza (donde las pinto Alexander): la rampa llega a un descanso y las gradas suben a la plaza
rep("[(fxw(cy1), cy1), (PX1, cy1), (PX1, PY1), (fxw(PY1), PY1)],", "[(fxw(cy1), cy1), (PX1 - 6.0, cy1), (PX1 - 6.0, PY1), (fxw(PY1), PY1)], rect(PX1 - 6.0, cy1, PX1, 240.0), rect(PX1 - 6.0, 258.0, PX1, PY1),")
rep("rampa(tp, RX_A, 160.0, RX_B, 238.0, 'S', _zh, M['pav_plaza'])", "ZR = 3.0\nrampa(tp, RX_A, 160.0, RX_B, 238.0, 'S', ZR, M['pav_plaza'])")
rep("tp.prism(rect(RX_A, 238.0, RX_B, 258.0), 0, _zh, M['arenisca'], top=M['pav_plaza'])", "tp.prism(rect(PX1, 238.0, RX_B, 260.0), 0, ZR, M['arenisca'], top=M['pav_plaza'])")
rep("    beam(tp, (_xr, 160.0, 1.0), (_xr, 238.0, _zh + 1.0), .06, M['acero'])", "    beam(tp, (_xr, 160.0, 1.0), (_xr, 238.0, ZR + 1.0), .06, M['acero'])")
rep("        tp.box((_xr, 160.0 + 3 * k, _zh * k / 26), (.06, .06, 1.0), M['acero'])", "        tp.box((_xr, 160.0 + 3 * k, ZR * k / 26), (.06, .06, 1.0), M['acero'])")
rep("gradas(tp, RX_B, 240.0, RX_B + 9.0, 258.0, 'E', _zh, 28)", """for i in range(10):                                        # gradas que suben del descanso a la plaza (hacia el occidente)
    tp.prism(rect(PX1 - 6.0 + i * .6, 240.0, PX1 - 6.0 + (i + 1) * .6 + .02, 258.0), ZR - .4, _zh - (_zh - ZR) * (i + 1) / 11 - ZR + .4, M['arenisca'] if i % 2 else M['concreto'])
beam(tp, (RX_B - .1, 238.0, ZR + 1.0), (RX_B - .1, 260.0, ZR + 1.0), .06, M['acero'])""")
rep("for _yb in (240.0, 249.0, 258.0):\n    beam(tp, (RX_B, _yb, _zh + .9), (RX_B + 9.0, _yb, .9), .05, M['acero'])", "for _yb in (240.0, 249.0, 258.0):\n    beam(tp, (PX1 - 6.0, _yb, _zh + .9), (PX1, _yb, ZR + .9), .05, M['acero'])")
rep("rampa(tp, RX_B, 172.0, RX_B + 9.0, 238.0, 'E', 2.6, M['cesped'])", "rampa(tp, RX_B, 172.0, RX_B + 9.0, 260.0, 'E', 2.4, M['cesped'])")
rep("tp.prism(rect(RX_B, 258.0, RX_B + 9.0, PY1 + .6), 0, .05, M['cesped'])\nrampa(tp, RX_A, 258.0, RX_B + 2.0, PY1 + .6, 'E', _zh, M['cesped'])", "rampa(tp, RX_A, 260.0, RX_B + 2.0, PY1 + .6, 'E', _zh, M['cesped'])")

# ================= Parques del Rio: parque sobre la autopista (soterrada) junto al Teatro Metropolitano y el rio (fotos de Alexander)
rep("mb.prism(rect(-165, 142, -82, 214), 0, .2, M['pav'])                                 # Teatro Metropolitano",
    """mb.prism(rect(-165, 142, -82, 214), 0, .2, M['pav'])                                 # Teatro Metropolitano
pr = G[('entorno', 'Parques_del_Rio')]
PRY0, PRY1 = 150, 388
TUNEL = mat('tunel_parques', (.02, .02, .025), .9)
for _o0, _o1 in ((34, 86), (-86, -34)):                    # losa del parque sobre las calzadas, a ambos lados del rio
    oblique(pr, _o0, _o1, 'concreto', 1.6, 1.6, PRY0, PRY1)
    oblique(pr, _o0 + 1.5, _o1 - 1.5, 'pav', 1.72, .12, PRY0 + 1.5, PRY1)
    oblique(pr, _o0 + 5 if _o0 > 0 else _o0 + 20, _o1 - 20 if _o0 > 0 else _o1 - 5, 'cesped', 1.86, .14, PRY0 + 8, PRY1 - 6)
    for _a, _b in ((_o0 + 9, _o0 + 22), (_o0 + 27, _o0 + 40)) if _o0 > 0 else ((_o1 - 40, _o1 - 27), (_o1 - 22, _o1 - 9)):
        pr.box((river_x(PRY0) + (_a + _b) / 2, PRY0 - .2, .05), (_b - _a, .5, 1.3), TUNEL, math.radians(15.5))   # bocas del tunel
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
            tree(river_x(_yt) + _of + random.uniform(-3, 3), _yt + random.uniform(-3, 3), random.uniform(.7, 1.1), force=True)""")
rep("flat_text('CARRERA 57', (-60, 235, .2), 2.2, M['blanco'], 'vias')", "label('PARQUES DEL RÍO', (river_x(290) + 60, 290), 22, (.20, .50, .25), 3.0)\nflat_text('CARRERA 57', (-60, 235, .2), 2.2, M['blanco'], 'vias')")

# ================= Rio Medellin visible (quedaba tapado por el terreno) y bocas del tunel de Parques del Rio mas grandes
rep("oblique(mb, -32, 32, 'agua', -1.2, .06, -240, 390)", "oblique(mb, -32, 32, 'agua', -1.2, .06, -240, 390)\noblique(mb, -29, 29, 'agua', .0, .1, -240, 390)\noblique(mb, -33, -29, 'cesped', .25, .3, -240, 390); oblique(mb, 29, 33, 'cesped', .25, .3, -240, 390)")
rep("(_b - _a, .5, 1.3), TUNEL, math.radians(15.5))", "(_b - _a, .8, 1.45), TUNEL, math.radians(15.5))")
rep("oblique(pr, _o0, _o1, 'concreto', 1.6, 1.6, PRY0, PRY1)", "oblique(pr, _o0, _o1, 'concreto', 1.6, 1.6, PRY0 + .6, PRY1)")

# ================= Gradas anchas de madera oscura (y 222-262, 11 m de fondo); balcon solo hasta donde empiezan
rep("(PX1 - 6.0, cy1), (PX1 - 6.0, PY1), (fxw(PY1), PY1)], rect(PX1 - 6.0, cy1, PX1, 240.0), rect(PX1 - 6.0, 258.0, PX1, PY1),",
    "(PX1 - 11.0, cy1), (PX1 - 11.0, PY1), (fxw(PY1), PY1)], rect(PX1 - 11.0, cy1, PX1, 222.0), rect(PX1 - 11.0, 262.0, PX1, PY1),")
rep("rampa(tp, RX_A, 160.0, RX_B, 238.0, 'S', ZR, M['pav_plaza'])", "rampa(tp, RX_A, 160.0, RX_B, 220.0, 'S', ZR, M['pav_plaza'])")
rep("tp.prism(rect(PX1, 238.0, RX_B, 260.0), 0, ZR,", "tp.prism(rect(PX1, 220.0, RX_B, 264.0), 0, ZR,")
rep("beam(tp, (_xr, 160.0, 1.0), (_xr, 238.0, ZR + 1.0), .06, M['acero'])", "beam(tp, (_xr, 160.0, 1.0), (_xr, 220.0, ZR + 1.0), .06, M['acero'])")
rep("tp.box((_xr, 160.0 + 3 * k, ZR * k / 26), (.06, .06, 1.0), M['acero'])", "tp.box((_xr, 160.0 + 2.3 * k, ZR * k / 26), (.06, .06, 1.0), M['acero'])")
rep("for i in range(10):                                        # gradas que suben del descanso a la plaza (hacia el occidente)",
    "MAD_GR = [mat('madera_gradas_a', (.16, .10, .06), .7), mat('madera_gradas_b', (.21, .13, .08), .7)]\nfor i in range(10):                                        # gradas anchas de madera oscura")
rep("    tp.prism(rect(PX1 - 6.0 + i * .6, 240.0, PX1 - 6.0 + (i + 1) * .6 + .02, 258.0), ZR - .4, _zh - (_zh - ZR) * (i + 1) / 11 - ZR + .4, M['arenisca'] if i % 2 else M['concreto'])",
    "    tp.prism(rect(PX1 - 11.0 + i * 1.1, 222.0, PX1 - 11.0 + (i + 1) * 1.1 + .02, 262.0), ZR - .4, _zh - (_zh - ZR) * (i + 1) / 11 - ZR + .4, MAD_GR[i % 2])")
rep("beam(tp, (RX_B - .1, 238.0, ZR + 1.0), (RX_B - .1, 260.0, ZR + 1.0), .06, M['acero'])", "beam(tp, (RX_B - .1, 220.0, ZR + 1.0), (RX_B - .1, 264.0, ZR + 1.0), .06, M['acero'])")
rep("for _yb in (240.0, 249.0, 258.0):\n    beam(tp, (PX1 - 6.0, _yb, _zh + .9), (PX1, _yb, ZR + .9), .05, M['acero'])", "for _yb in (222.0, 262.0):\n    beam(tp, (PX1 - 11.0, _yb, _zh + .9), (PX1, _yb, ZR + .9), .05, M['acero'])")
rep("rampa(tp, RX_B, 172.0, RX_B + 9.0, 260.0, 'E', 2.4, M['cesped'])", "rampa(tp, RX_B, 172.0, RX_B + 9.0, 264.0, 'E', 2.4, M['cesped'])")
rep("rampa(tp, RX_A, 260.0, RX_B + 2.0, PY1 + .6, 'E', _zh, M['cesped'])", "rampa(tp, RX_A, 264.0, RX_B + 2.0, PY1 + .6, 'E', _zh, M['cesped'])")
rep("for _yb in range(172, 238, 3):", "for _yb in range(172, 221, 3):")
rep("beam(tp, (PX1 + .1, 172.0, _zh + 1.0), (PX1 + .1, 238.0, _zh + 1.0), .06, M['acero'])", "beam(tp, (PX1 + .1, 172.0, _zh + 1.0), (PX1 + .1, 220.0, _zh + 1.0), .06, M['acero'])")
rep("tp.seg((PX1 + .25, 172.0), (PX1 + .25, 238.0), .5, 0, _zh, M['arenisca'])", "tp.seg((PX1 + .25, 172.0), (PX1 + .25, 220.0), .5, 0, _zh, M['arenisca'])")
rep("lambda x, y: x > fxw(y) + 1 and not", "lambda x, y: x > fxw(y) + 1 and not (x > PX1 - 12 and 220 < y < 264) and not")

# ================= Sin muro entre el descanso de la rampa y las gradas de madera
rep("((PX1 + .3, PY1 + .3), (PX1 + .3, PY0))):\n    mb.seg(a, b, .6, Z_GS, -Z_GS + .02, M['arenisca'])",
    "((PX1 + .3, PY1 + .3), (PX1 + .3, 262.0)), ((PX1 + .3, 222.0), (PX1 + .3, PY0))):\n    mb.seg(a, b, .6, Z_GS, -Z_GS + .02, M['arenisca'])\nmb.seg((PX1 + .3, 262.0), (PX1 + .3, 222.0), .6, Z_GS, -Z_GS - DZ_CONV + 2.6, M['arenisca'])")
(R / 'construir_mapa_v04.py').write_text(s, encoding='utf8')

# render v04
t = (R / 'render_mapa_v03.py').read_text(encoding='utf8')
for a, b in (("Plaza_Mayor_mapa_v03.blend --python render_mapa_v03.py", "Plaza_Mayor_mapa_v04.blend --python render_mapa_v04.py"),
             ("OUT = R / 'renders_v03'", "OUT = R / 'renders_v04'"),
             ("    s.world.node_tree.nodes['Cielo_visible'].inputs[0].default_value = (.38, .62, .95, 1) if mode == 'foto' else (.80, .87, .97, 1)\n", "")):
    assert a in t, a[:50]
    t = t.replace(a, b)
VIEWS_EXTRA = ["'maqueta_gradas': ('foto', 'Cam_Gradas', (2400, 1680)),", "'maqueta_fachada_gs': ('foto', 'Cam_Fachada_GS', (2400, 1680)),", "'maqueta_carros': ('foto', 'Cam_Carros', (2400, 1680)),", "'detalle_gran_salon': ('planta_inf', 'Cam_Planta_GS', (2400, 1800)),", "'maqueta_portico': ('foto', 'Cam_Portico', (2400, 1680)),", "'mapa_verde_tarima': ('foto', 'Cam_Verde_Tarima', (2400, 1680)),"]
t = t.replace("    " + VIEWS_EXTRA[0], chr(10).join("    " + v for v in VIEWS_EXTRA))
(R / 'render_mapa_v04.py').write_text(t, encoding='utf8')
print('ok')
