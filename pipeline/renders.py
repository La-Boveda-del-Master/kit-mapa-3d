"""Renders fijos del modelo (para presentar, imprimir o revisar contra el plano) y video de recorrido.

Uso:
  blender -b proyectos/<recinto>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<recinto>/recinto.json [opciones]

Opciones:
  --vistas=iso,planta,niveles     vistas fijas (por defecto las tres). Salen en salida/renders/<vista>.png
  --preview                       baja resolucion y muestras: para revisar rapido antes del render final
  --video                         en vez de vistas fijas, video del recorrido (tramos de "recorrido" en recinto.json,
                                  o un giro de 360 grados si no hay tramos). Fotogramas reanudables en salida/video_frames/
  --codificar                     une los fotogramas ya renderizados en salida/recorrido.mp4
  --prueba                        con --video: un solo fotograma por tramo, para revisar el encuadre antes de las horas de render

Vistas:
  iso      exterior con cubiertas, en diagonal
  planta   desde arriba, ortografica, norte arriba (para comparar con el PDF)
  niveles  sin cubiertas y con los niveles separados (como el modo "Por niveles" del visor)
No guarda cambios en el .blend.
"""
import bpy, json, math, sys, pathlib
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CFG = json.loads(pathlib.Path(argv[0]).read_text(encoding='utf8'))
OUT = pathlib.Path(argv[0]).resolve().parent / 'salida'
op = {a.split('=')[0]: (a.split('=', 1)[1] if '=' in a else True) for a in argv[1:]}
preview = 'preview' in [k.lstrip('-') for k in op]
s = bpy.context.scene
cx, cy = s.get('CENTRO', (0, 0)); R = float(s.get('RADIO', 200))

s.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
if hasattr(s, 'eevee'):
    s.eevee.taa_render_samples = 16 if preview or '--video' in op else 64
s.view_settings.view_transform = 'AgX' if 'AgX' in [v.identifier for v in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'

sol = bpy.data.objects.get('Sol')
if not sol:
    sol = bpy.data.objects.new('Sol', bpy.data.lights.new('Sol', 'SUN')); s.collection.objects.link(sol)
    sol.data.energy = 3.5; sol.rotation_euler = (math.radians(50), 0, math.radians(35))


def grupos(niveles):
    """niveles=True: sin cubiertas y con cada RAIZ subida su separacion."""
    for o in bpy.data.objects:
        g = o.get('grupo', '')
        o.hide_render = niveles and g.startswith('techo_')
        if o.name.startswith('RAIZ_'):
            o.location.z = float(s.get('LIFT_' + o.name[5:], 0)) if niveles else 0.0


def camara(nombre, pos, mira, lente=40, orto=None):
    cam = bpy.data.objects.get(nombre) or bpy.data.objects.new(nombre, bpy.data.cameras.new(nombre))
    if cam.name not in s.collection.objects:
        s.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lente; cam.data.clip_end = R * 30
    if orto:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = orto
    s.camera = cam
    return cam


def render(ruta, w, h):
    f = .5 if preview else 1
    s.render.resolution_x, s.render.resolution_y = int(w * f), int(h * f)
    s.render.filepath = str(ruta); s.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    print('RENDER', ruta)


if '--video' not in op and '--codificar' not in op:
    (OUT / 'renders').mkdir(parents=True, exist_ok=True)
    d = R * 2.3
    for v in str(op.get('--vistas', 'iso,planta,niveles')).split(','):
        if v == 'iso':
            grupos(False); camara('Cam_Iso', (cx + d * .55, cy - d * .75, d * .6), (cx, cy, 0))
        elif v == 'planta':
            grupos(False); camara('Cam_Planta', (cx, cy, R * 6), (cx, cy + .001, 0), orto=R * 2.2)
        elif v == 'niveles':
            grupos(True); camara('Cam_Niveles', (cx + d * .55, cy - d * .75, d * .75), (cx, cy, 8))
        else:
            print('Vista desconocida:', v); continue
        render(OUT / 'renders' / f'{v}.png', 2400, 1600)
    grupos(False)
    sys.exit(0)

# ---------------------------------------------------------------- video
FPS = 24
FR = OUT / 'video_frames'; FR.mkdir(parents=True, exist_ok=True)
if '--codificar' in op:
    se = s.sequence_editor_create()
    strips = se.strips if hasattr(se, 'strips') else se.sequences      # Blender 5 renombro sequences -> strips
    fotos = sorted(FR.glob('f_*.jpg'))
    if not fotos:
        raise SystemExit('No hay fotogramas: corre primero con --video')
    st = strips.new_image('frames', str(fotos[0]), 1, 1)
    for f in fotos[1:]:
        st.elements.append(f.name)
    s.frame_start, s.frame_end = 1, len(fotos)
    s.render.fps = FPS; s.render.resolution_x, s.render.resolution_y = 1280, 720
    s.render.image_settings.file_format = 'FFMPEG'; s.render.ffmpeg.format = 'MPEG4'; s.render.ffmpeg.codec = 'H264'
    s.render.ffmpeg.constant_rate_factor = 'MEDIUM'; s.render.filepath = str(OUT / 'recorrido.mp4')
    bpy.ops.render.render(animation=True)
    print('VIDEO', OUT / 'recorrido.mp4')
    sys.exit(0)

grupos(False)
s.render.resolution_x, s.render.resolution_y = (640, 360) if '--prueba' in op else (1280, 720)
s.render.image_settings.file_format = 'JPEG'
# tramos: [{"nombre": "...", "segundos": 5, "puntos": [[[cam x, y, z], [mira x, y, z]], ...]}]
tramos = CFG.get('recorrido') or [{
    'nombre': 'Giro', 'segundos': 16,
    'puntos': [[[cx + R * 2 * math.cos(a), cy + R * 2 * math.sin(a), R * .9], [cx, cy, 0]] for a in [i * math.pi / 4 for i in range(9)]]}]
cam = camara('Cam_Video', (0, 0, 0), (0, 0, -1), 28)
n = 0
for t in tramos:
    pts = t['puntos']; N = max(2, int(t['segundos'] * FPS))
    cuadros = [0] if '--prueba' in op else range(N)
    for k in cuadros:
        u = k / (N - 1) * (len(pts) - 1); i = min(int(u), len(pts) - 2); f = u - i
        f = f * f * (3 - 2 * f)                                     # suave entre puntos
        p = Vector(pts[i][0]).lerp(Vector(pts[i + 1][0]), f); m = Vector(pts[i][1]).lerp(Vector(pts[i + 1][1]), f)
        cam.location = p; cam.rotation_euler = (m - p).to_track_quat('-Z', 'Y').to_euler()
        ruta = (OUT / f"video_prueba_{t['nombre']}.jpg") if '--prueba' in op else FR / f'f_{n + k:05d}.jpg'
        if ruta.exists() and '--prueba' not in op:
            continue                                                # reanudable
        s.render.filepath = str(ruta); bpy.ops.render.render(write_still=True)
    n += N
print('FOTOGRAMAS OK', n)
