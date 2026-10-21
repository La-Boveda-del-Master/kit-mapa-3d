"""Renders profesionales del modelo (presentar, imprimir, revisar contra el plano) y video de recorrido.

Uso:
  blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/mapa.json [opciones]

Vistas (--vistas=axo,planta,niveles  por defecto):
  axo        axonometrica ortografica (isometrica real, la vista clasica de "mapa 3D")
  aerea      perspectiva aerea a tres cuartos, mas fotografica
  planta     desde arriba, ortografica, norte arriba (escala grafica exacta; para comparar con el plano)
  niveles    axonometrica sin cubiertas y con los niveles separados ("Por niveles")
  corte      axonometrica sin cubiertas, todo en su sitio (ver interiores)
Estilos (--estilo=realista  por defecto):
  realista   materiales y texturas, cielo fisico, sombras suaves, bordes biselados
  maqueta    maqueta blanca de arquitectura: todo en un material claro, luz suave, oclusion
  ilustrado  colores planos y contorno de linea (estilo mapa turistico / infografia)
  noche      cielo nocturno, pantallas y luces encendidas
Otras opciones:
  --motor=eevee|cycles   eevee rapido (defecto); cycles mas fiel (sombras y rebotes), mas lento
  --tam=preview|hd|4k|8k|a3|a2|a1   tamano de salida (a3/a2/a1 = 300 ppp horizontal). Defecto 4k; --preview = preview
  --muestras=N           muestras de render (defecto segun motor y tamano)
  --azimut=35            de donde mira la camara en axo/aerea/niveles (grados desde el sur, sentido horario)
  --transparente         fondo transparente (PNG con alfa) para montar sobre otro diseno
  --calco                muestra la imagen del plano bajo el modelo (si mapa.json tiene "calco")
  --sin-bisel            no biselar bordes (mas rapido)
  --video / --prueba / --codificar   video de recorrido (ver abajo)

Cada render deja salida/renders/<vista>_<estilo>.png y un .json con la posicion en pantalla de cada lugar (pin),
la direccion del norte y, en planta, los pixeles por metro: componer_lamina.py los usa para la lamina final.

Video: --video renderiza los fotogramas (reanudables) de los tramos de "recorrido" en mapa.json o un giro de 360;
--prueba saca un fotograma por tramo; --codificar une los fotogramas en salida/recorrido.mp4.
No guarda cambios en el .blend.
"""
import bpy, json, math, sys, pathlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CFG = json.loads(pathlib.Path(argv[0]).read_text(encoding='utf8'))
OUT = pathlib.Path(argv[0]).resolve().parent / 'salida'
op = {a.split('=')[0].lstrip('-'): (a.split('=', 1)[1] if '=' in a else True) for a in argv[1:]}
s = bpy.context.scene
NIV = {n['id']: n for n in CFG['niveles']}
LIFT = {n['id']: float(n.get('separacion', 0)) for n in CFG['niveles']}
ESTILO = op.get('estilo', 'realista')
MOTOR = op.get('motor', 'eevee')
TAM = 'preview' if op.get('preview') else op.get('tam', '4k')
SIZES = {'preview': (1200, 800), 'hd': (1920, 1280), '4k': (3840, 2560), '8k': (7680, 5120),
         'a3': (4961, 3508), 'a2': (7016, 4961), 'a1': (9933, 7016)}
if ESTILO not in ('realista', 'maqueta', 'ilustrado', 'noche'):
    raise SystemExit(f'Estilo desconocido: {ESTILO}')


# ---------------------------------------------------------------- motor y color
def motor():
    if MOTOR == 'cycles':
        try:
            bpy.ops.preferences.addon_enable(module='cycles')
        except Exception:
            pass
        s.render.engine = 'CYCLES'
        s.cycles.samples = int(op.get('muestras', 48 if TAM == 'preview' else 256))
        s.cycles.use_denoising = True
        try:                                            # GPU si hay
            prefs = bpy.context.preferences.addons['cycles'].preferences
            for t in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
                try:
                    prefs.compute_device_type = t; prefs.get_devices()
                    if any(d.type == t for d in prefs.devices):
                        for d in prefs.devices:
                            d.use = True
                        s.cycles.device = 'GPU'; break
                except Exception:
                    continue
        except Exception:
            pass
    else:
        s.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
        e = s.eevee
        e.taa_render_samples = int(op.get('muestras', 24 if TAM == 'preview' else 96))
        for k, v in (('use_raytracing', True), ('use_fast_gi', True), ('use_shadows', True), ('shadow_ray_count', 2), ('shadow_step_count', 8)):
            if hasattr(e, k):
                setattr(e, k, v)
    vs = s.view_settings
    vs.view_transform = 'AgX' if 'AgX' in [v.identifier for v in type(vs).bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    for look in ('AgX - Medium High Contrast', 'AgX - Base Contrast', 'Medium High Contrast'):
        try:
            vs.look = look; break
        except TypeError:
            continue
    s.render.film_transparent = bool(op.get('transparente'))
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA' if op.get('transparente') else 'RGB'
    s.render.image_settings.color_depth = '8'


# ---------------------------------------------------------------- luz y cielo por estilo
def nodo(nt, tipo):
    return next((n for n in nt.nodes if n.type == tipo), None)


def cielo(az):
    w = s.world or bpy.data.worlds.new('Cielo'); s.world = w; w.use_nodes = True; nt = w.node_tree
    for n in list(nt.nodes):
        if n.type not in ('OUTPUT_WORLD',):
            nt.nodes.remove(n)
    out = nodo(nt, 'OUTPUT_WORLD'); bg = nt.nodes.new('ShaderNodeBackground')
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    sun = bpy.data.objects.get('Sol') or bpy.data.objects.new('Sol', bpy.data.lights.new('Sol', 'SUN'))
    if sun.name not in s.collection.objects:
        s.collection.objects.link(sun)
    elev = 38 if ESTILO != 'noche' else 25
    # el sol entra desde la izquierda-atras de la camara: sombras que dan volumen sin tapar fachadas
    sun_az = math.radians(az + 130)
    sun.rotation_euler = (math.radians(90 - elev), 0, sun_az)
    if ESTILO == 'realista':
        sky = nt.nodes.new('ShaderNodeTexSky')
        for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'HOSEK_WILKIE'):
            try:
                sky.sky_type = t; break
            except TypeError:
                continue
        if hasattr(sky, 'sun_elevation'):
            sky.sun_elevation = math.radians(elev); sky.sun_rotation = sun_az + math.pi
            if hasattr(sky, 'sun_disc'):
                sky.sun_disc = False
        nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = .22
        sun.data.energy = 4.6; sun.data.angle = math.radians(1.5); sun.data.color = (1, .96, .9)
    elif ESTILO == 'maqueta':
        bg.inputs['Color'].default_value = (.92, .93, .95, 1); bg.inputs['Strength'].default_value = .8
        sun.data.energy = 3.4; sun.data.angle = math.radians(8); sun.data.color = (1, 1, 1)
    elif ESTILO == 'ilustrado':
        bg.inputs['Color'].default_value = (.96, .95, .92, 1); bg.inputs['Strength'].default_value = 1.4
        sun.data.energy = 2.2; sun.data.angle = math.radians(4); sun.data.color = (1, .98, .94)
    else:                                                       # noche
        bg.inputs['Color'].default_value = (.010, .016, .040, 1); bg.inputs['Strength'].default_value = 1
        sun.data.energy = .25; sun.data.angle = math.radians(1); sun.data.color = (.6, .7, 1)
        bg.inputs['Strength'].default_value = 2.2
        for m in bpy.data.materials:                            # ventanas encendidas
            if m.name.startswith('vidrio') and m.node_tree:
                b = nodo(m.node_tree, 'BSDF_PRINCIPLED')
                b.inputs['Emission Color'].default_value = (1, .72, .42, 1); b.inputs['Emission Strength'].default_value = 3.5
        for i, p in enumerate(CFG.get('pines', [])):            # luz calida y baja en cada lugar (alumbrado)
            g = p.get('nivel', 'base'); pos = list(p['pos']) + [2] * (3 - len(p['pos']))
            L = bpy.data.objects.new(f'Luz_{i}', bpy.data.lights.new(f'Luz_{i}', 'POINT'))
            L.data.energy = 2500; L.data.color = (1, .78, .52); L.data.shadow_soft_size = 6
            L.location = (pos[0], pos[1], float(NIV.get(g, {}).get('z', 0)) + 4); L['grupo'] = g
            s.collection.objects.link(L)
            raiz = bpy.data.objects.get('RAIZ_' + g)
            if raiz:
                L.parent = raiz
        for m in bpy.data.materials:                            # pantallas mas brillantes
            if m.get('led') and m.node_tree:
                b = nodo(m.node_tree, 'BSDF_PRINCIPLED'); b.inputs['Emission Strength'].default_value = 6


def piso_infinito():
    """Suelo amplio bajo el terreno para que el encuadre nunca muestre el vacio (en transparente no hace falta)."""
    if op.get('transparente'):
        return
    cx, cy = s.get('CENTRO', (0, 0)); R = float(s.get('RADIO', 100)) * 30
    z = min([float(n.get('z', 0)) for n in NIV.values()] + [0]) - .45
    me = bpy.data.meshes.new('PisoInfinito')
    me.from_pydata([(cx - R, cy - R, z), (cx + R, cy - R, z), (cx + R, cy + R, z), (cx - R, cy + R, z)], [], [(0, 1, 2, 3)])
    ter = bpy.data.objects.get('Terreno')
    if ter and ter.data.materials:
        me.materials.append(ter.data.materials[0])         # mismo material que el terreno: sin costura visible
        me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, R / 2.4, 0, R / 2.4, R / 2.4, 0, R / 2.4])
    else:
        m = bpy.data.materials.new('piso_infinito'); m.use_nodes = True; m.diffuse_color = (.6, .6, .58, 1)
        nodo(m.node_tree, 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.6, .6, .58, 1); me.materials.append(m)
    o = bpy.data.objects.new('PisoInfinito', me); o['grupo'] = 'entorno'; s.collection.objects.link(o)


def acabado():
    """Ajustes de materiales por estilo (en memoria; el .blend no se guarda)."""
    if ESTILO == 'maqueta':
        clay = bpy.data.materials.new('maqueta'); clay.use_nodes = True
        b = nodo(clay.node_tree, 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = (.86, .86, .84, 1)
        b.inputs['Roughness'].default_value = .85
        vidrio = bpy.data.materials.new('maqueta_vidrio'); vidrio.use_nodes = True
        bv = nodo(vidrio.node_tree, 'BSDF_PRINCIPLED'); bv.inputs['Base Color'].default_value = (.70, .80, .86, 1)
        bv.inputs['Roughness'].default_value = .1; bv.inputs['Alpha'].default_value = .45
        if hasattr(vidrio, 'surface_render_method'):
            vidrio.surface_render_method = 'BLENDED'
        acento = bpy.data.materials.new('maqueta_acento'); acento.use_nodes = True
        ba = nodo(acento.node_tree, 'BSDF_PRINCIPLED'); ba.inputs['Base Color'].default_value = (.72, .74, .76, 1)
        for o in bpy.data.objects:
            if o.type != 'MESH':
                continue
            for sl in o.material_slots:
                if not sl.material:
                    continue
                n = sl.material.name
                sl.link = 'OBJECT'
                if n.startswith('rotulo'):
                    continue
                sl.material = vidrio if n.startswith('vidrio') else (acento if o.get('grupo') == 'entorno' or n.startswith(('asfalto', 'agua')) else clay)
        for m in bpy.data.materials:                            # textos oscuros: se leen sobre lo blanco
            if m.name.startswith('rotulo') and m.node_tree:
                nodo(m.node_tree, 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.18, .19, .21, 1)
        s.view_settings.exposure = -.6
    elif ESTILO == 'ilustrado':
        for m in bpy.data.materials:
            if not m.node_tree:
                continue
            b = nodo(m.node_tree, 'BSDF_PRINCIPLED')
            if not b:
                continue
            for l in list(b.inputs['Base Color'].links):
                m.node_tree.links.remove(l)
            c = list(m.diffuse_color)
            b.inputs['Base Color'].default_value = (min(1, c[0] * 1.08), min(1, c[1] * 1.08), min(1, c[2] * 1.08), 1)
            b.inputs['Roughness'].default_value = 1
            for k in ('Specular IOR Level', 'Specular'):
                if k in b.inputs:
                    b.inputs[k].default_value = 0
            for l in list(b.inputs['Normal'].links):
                m.node_tree.links.remove(l)
        r = s.render; r.use_freestyle = True; r.line_thickness_mode = 'ABSOLUTE'
        r.line_thickness = max(1.0, s.render.resolution_x / 2400)
        vl = bpy.context.view_layer; vl.use_freestyle = True
        fs = vl.freestyle_settings; fs.crease_angle = math.radians(134)
        ls = fs.linesets[0] if fs.linesets else fs.linesets.new('contorno')
        for k in ('select_silhouette', 'select_border', 'select_crease'):
            setattr(ls, k, True)
        if not ls.linestyle:
            ls.linestyle = bpy.data.linestyles.new('contorno')
        ls.linestyle.color = (.16, .17, .2); ls.linestyle.thickness = 1.2
    if ESTILO in ('realista', 'maqueta') and not op.get('sin-bisel'):
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.get('grupo') not in ('entorno', 'calco') and not o.name.startswith(('Zona_', 'Codigos')):
                bv = o.modifiers.new('Bisel', 'BEVEL'); bv.width = .035; bv.segments = 2
                bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
                if hasattr(bv, 'harden_normals'):
                    bv.harden_normals = True


# ---------------------------------------------------------------- visibilidad, camaras y encuadre
def grupos(sin_techo, separar):
    for o in bpy.data.objects:
        g = o.get('grupo', '')
        o.hide_render = (sin_techo and g.startswith('techo_')) or (g == 'calco' and not op.get('calco'))
        if o.name.startswith('RAIZ_'):
            o.location.z = LIFT.get(o.name[5:], 0) if separar else 0.0
    bpy.context.view_layer.update()


def puntos_modelo():
    pts = []
    for o in bpy.data.objects:
        if o.type in ('MESH', 'FONT') and not o.hide_render and o.get('grupo') not in ('entorno', 'calco'):
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return pts or [Vector((0, 0, 0))]


def camara(nombre, az, elev, orto, lente=50):
    """Camara mirando el centro del modelo desde (azimut, elevacion); encuadre ajustado al modelo visible."""
    cam = bpy.data.objects.get(nombre) or bpy.data.objects.new(nombre, bpy.data.cameras.new(nombre))
    if cam.name not in s.collection.objects:
        s.collection.objects.link(cam)
    s.camera = cam
    pts = puntos_modelo()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    a, e = math.radians(az), math.radians(elev)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))   # az 0 = desde el sur
    R = (hi - lo).length
    cam.data.clip_start = .5; cam.data.clip_end = R * 20
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    asp = s.render.resolution_x / s.render.resolution_y
    if orto:
        cam.data.type = 'ORTHO'; cam.location = c + d * R * 3
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        q = [inv @ p for p in pts]
        w = max(p.x for p in q) - min(p.x for p in q); h = max(p.y for p in q) - min(p.y for p in q)
        cx = (max(p.x for p in q) + min(p.x for p in q)) / 2; cy = (max(p.y for p in q) + min(p.y for p in q)) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0))
        cam.data.ortho_scale = max(w, h * asp) * 1.10
    else:
        cam.data.type = 'PERSP'; cam.data.lens = lente
        lo_d, hi_d = R * .2, R * 6
        for _ in range(30):                                 # busqueda binaria de la distancia que encuadra todo
            mid = (lo_d + hi_d) / 2; cam.location = c + d * mid; bpy.context.view_layer.update()
            ok = all(.035 < v.x < .965 and .05 < v.y < .95 and v.z > 0 for v in (world_to_camera_view(s, cam, p) for p in pts))
            hi_d, lo_d = (mid, lo_d) if ok else (hi_d, mid)
        cam.location = c + d * hi_d
    bpy.context.view_layer.update()
    return cam


VISTAS = {  # vista: (sin techo, separar niveles, azimut relativo, elevacion, ortografica, lente)
    'axo': (False, False, 0, 35.264, True, 0),
    'aerea': (False, False, 0, 30, False, 45),
    'planta': (False, False, None, 90, True, 0),
    'niveles': (True, True, 0, 35.264, True, 0),
    'corte': (True, False, 0, 40, True, 0),
}


def meta_render(vista, cam, ruta):
    """Posicion en pantalla de cada lugar, direccion del norte y escala, para componer la lamina."""
    W, H = s.render.resolution_x, s.render.resolution_y
    sep = VISTAS[vista][1]; sin_techo = VISTAS[vista][0]
    pines = []
    for i, p in enumerate(CFG.get('pines', []), 1):
        g = p.get('nivel', 'base'); pos = list(p['pos']) + [2] * (3 - len(p['pos']))
        z = float(NIV.get(g, {}).get('z', 0)) + pos[2] + (LIFT.get(g, 0) if sep else 0)
        v = world_to_camera_view(s, cam, Vector((pos[0], pos[1], z)))
        oculto = NIV.get(g, {}).get('bajo_techo') and not (sep or sin_techo)
        pines.append({'n': p.get('n', i), 'nombre': p['nombre'], 'detalle': p.get('detalle', ''), 'color': p.get('color', [.85, .2, .25]),
                      'nivel': NIV.get(g, {}).get('nombre', g), 'x': round(v.x * W, 1), 'y': round((1 - v.y) * H, 1),
                      'visible': bool(0 < v.x < 1 and 0 < v.y < 1 and v.z > 0 and not oculto)})
    c = Vector((*s.get('CENTRO', (0, 0)), 0))
    a = world_to_camera_view(s, cam, c); b = world_to_camera_view(s, cam, c + Vector((0, 10, 0)))
    norte = math.degrees(math.atan2((b.x - a.x) * W, (b.y - a.y) * H))         # 0 = arriba, positivo = horario
    meta = {'vista': vista, 'estilo': ESTILO, 'ancho': W, 'alto': H, 'norte_grados': round(norte, 2), 'pines': pines,
            'px_por_m': round(W / cam.data.ortho_scale, 4) if vista == 'planta' else None,
            'transparente': bool(op.get('transparente'))}
    pathlib.Path(str(ruta)[:-4] + '.json').write_text(json.dumps(meta, ensure_ascii=False), encoding='utf8')


def render(vista):
    if vista not in VISTAS:
        print('Vista desconocida:', vista, '- opciones:', ', '.join(VISTAS)); return
    sin_techo, separar, az_rel, elev, orto, lente = VISTAS[vista]
    grupos(sin_techo, separar)
    az = 0 if az_rel is None else float(op.get('azimut', 35)) + az_rel
    cam = camara('Cam_' + vista, az, elev, orto, lente)
    ruta = OUT / 'renders' / f'{vista}_{ESTILO}.png'
    s.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)
    meta_render(vista, cam, ruta)
    print('RENDER', ruta)


# ---------------------------------------------------------------- vistas fijas
if not op.get('video') and not op.get('codificar'):
    (OUT / 'renders').mkdir(parents=True, exist_ok=True)
    s.render.resolution_x, s.render.resolution_y = SIZES[TAM]
    s.render.resolution_percentage = 100
    motor()
    cielo(float(op.get('azimut', 35)))
    piso_infinito()
    acabado()
    for v in str(op.get('vistas', 'axo,planta,niveles')).split(','):
        render(v.strip())
    grupos(False, False)
    sys.exit(0)

# ---------------------------------------------------------------- video
FPS = 24
FR = OUT / 'video_frames'; FR.mkdir(parents=True, exist_ok=True)
if op.get('codificar'):
    se = s.sequence_editor_create()
    strips = se.strips if hasattr(se, 'strips') else se.sequences      # Blender 5 renombro sequences -> strips
    fotos = sorted(FR.glob('f_*.jpg'))
    if not fotos:
        raise SystemExit('No hay fotogramas: corre primero con --video')
    st = strips.new_image('frames', str(fotos[0]), 1, 1)
    for f in fotos[1:]:
        st.elements.append(f.name)
    s.frame_start, s.frame_end = 1, len(fotos)
    s.render.fps = FPS; s.render.resolution_x, s.render.resolution_y = 1920, 1080
    s.render.image_settings.file_format = 'FFMPEG'; s.render.ffmpeg.format = 'MPEG4'; s.render.ffmpeg.codec = 'H264'
    s.render.ffmpeg.constant_rate_factor = 'HIGH'; s.render.filepath = str(OUT / 'recorrido.mp4')
    bpy.ops.render.render(animation=True)
    print('VIDEO', OUT / 'recorrido.mp4')
    sys.exit(0)

TAM = 'preview' if op.get('prueba') else TAM
s.render.resolution_x, s.render.resolution_y = (640, 360) if op.get('prueba') else (1920, 1080)
motor(); cielo(float(op.get('azimut', 35))); piso_infinito(); acabado(); grupos(False, False)
s.render.image_settings.file_format = 'JPEG'; s.render.image_settings.quality = 92
cx, cy = s.get('CENTRO', (0, 0)); R = float(s.get('RADIO', 200))
# tramos: [{"nombre": "...", "segundos": 5, "puntos": [[[cam x, y, z], [mira x, y, z]], ...]}]
tramos = CFG.get('recorrido') or [{
    'nombre': 'giro', 'segundos': 16,
    'puntos': [[[cx + R * 2.2 * math.cos(a), cy + R * 2.2 * math.sin(a), R * 1.1], [cx, cy, 0]] for a in [i * math.pi / 4 for i in range(9)]]}]
cam = bpy.data.objects.get('Cam_Video') or bpy.data.objects.new('Cam_Video', bpy.data.cameras.new('Cam_Video'))
if cam.name not in s.collection.objects:
    s.collection.objects.link(cam)
cam.data.lens = 28; cam.data.clip_end = R * 30; s.camera = cam
n = 0
for t in tramos:
    pts = t['puntos']; N = max(2, int(t['segundos'] * FPS))
    for k in ([0] if op.get('prueba') else range(N)):
        u = k / (N - 1) * (len(pts) - 1); i = min(int(u), len(pts) - 2); f = u - i
        f = f * f * (3 - 2 * f)                                     # suave entre puntos
        p = Vector(pts[i][0]).lerp(Vector(pts[i + 1][0]), f); m = Vector(pts[i][1]).lerp(Vector(pts[i + 1][1]), f)
        cam.location = p; cam.rotation_euler = (m - p).to_track_quat('-Z', 'Y').to_euler()
        ruta = (OUT / f"video_prueba_{t['nombre']}.jpg") if op.get('prueba') else FR / f'f_{n + k:05d}.jpg'
        if ruta.exists() and not op.get('prueba'):
            continue                                                # reanudable
        s.render.filepath = str(ruta); bpy.ops.render.render(write_still=True)
    n += N
print('FOTOGRAMAS OK', n)
