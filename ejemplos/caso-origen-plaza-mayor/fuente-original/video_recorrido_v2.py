"""Video recorrido completo de la feria: exterior + interior de cada pabellon y auditorio.

Uso: blender -b Plaza_Mayor_mapa_v04.blend --python video_recorrido_v2.py -- [--prueba | --codificar]
  (sin opciones) renderiza los fotogramas JPG en renders_v04/video2_frames (reanudable).
  --codificar: une esos fotogramas en el MP4.
  --prueba: renderiza un fotograma por tramo a 640x360 (renders_v04/video2_prueba_NN.png) para revisar el recorrido.
  --solo=11,12: con --prueba, solo esos tramos, y de cada uno 3 fotogramas (inicio, medio, fin).
Salida: renders_v04/recorrido_completo_effix_2026.mp4 (1280x720, 24 fps). No guarda cambios en el .blend.

El recorrido va por tramos; entre tramo y tramo hay un corte (la camara salta de un plano al siguiente).
Dentro de cada tramo la camara se mueve con suavidad entre sus puntos. Coordenadas: X este, Y norte, Z alto (m).
Niveles: nivel principal z=0 . Rojo/Comunidades z=0 . Azul/Verde z=5.6 . Multiproposito z=-4.5 . Gran Salon z=-9 . Caja piso 3 z=0.
"""
import bpy, sys, pathlib

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
OUT = R / 'renders_v04'
OUT.mkdir(exist_ok=True)
prueba = '--prueba' in sys.argv
s = bpy.context.scene

OCULTAR = ('00', '19a', '19b', '19c', '19d', '19e', '19f', '20', '21', '22')     # sin pines, rotulos, guias ni calco
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = lc.name.split('_')[0] in OCULTAR
for n in ('RAIZ_nivel_superior', 'RAIZ_multiproposito', 'RAIZ_caja_piso3', 'RAIZ_caja_caparazon'):
    bpy.data.objects[n].location.z = 0.0                                          # todo en su sitio (modo exterior)

FPS = 24
E = 1.7            # altura de ojos sobre el piso (auditorios, registro)
P = 4.0            # altura de camara en los pabellones de stands: por encima de los stands (~3 m), mirando algo hacia abajo
UP, GS, MU = 5.6, -9.0, -4.5

# (nombre, duracion_s, [(pos_camara, objetivo), ...])  - el primer y ultimo punto son el plano de entrada y salida del tramo
TRAMOS = [
    ('Panoramica oriente',        5, [((330, 150, 190), (0, 95, 0)), ((190, 290, 110), (10, 200, 5))]),
    ('Caja de Madera - ingreso',  5, [((60, 300, 22), (12, 222, 8)), ((22, 262, 9), (12, 222, 6))]),
    ('Registro y taquillas',      6, [((12, 216, E), (12, 190, 1)), ((13, 196, E), (8, 180, 0)), ((20, 186, E), (4, 180, -2))]),
    ('Salon Multiproposito',      5, [((-8, 168, MU + E), (30, 180, MU + 1)), ((20, 188, MU + E), (34, 170, MU + 1))]),
    ('Gran Salon - lobby',        4, [((-18, 170, GS + E), (20, 180, GS + 1)), ((5, 180, GS + E), (12, 210, GS + 2))]),
    ('Gran Salon - auditorio',    7, [((11, 206, GS + 1.9), (11, 255, GS + 5.5)), ((11, 236, GS + 2.6), (11, 268, GS + 4.5)), ((11, 252, GS + 2.2), (11, 268, GS + 3.2))]),
    ('Gran Salon - cielo e ingresos', 5, [((11, 254, GS + 1.8), (11, 204, GS + 6.0)), ((11, 232, GS + 1.8), (11, 202, GS + 3.2))]),
    ('Gradas y Plazoleta',        5, [((45, 190, 18), (0, 150, 0)), ((70, 140, 14), (20, 135, 2))]),
    ('Auditorio UGC',             5, [((28, 128, 3.5), (-2, 140, 3)), ((-2, 118, E), (-2, 150, 4))]),
    ('Ingreso y Pabellon Blanco', 7, [((40, 112, 8), (22, 98, 3)), ((22, 90, P), (22, 60, 1.2)), ((22, 24, P), (22, 2, 1.5))]),
    ('Hall',                      3, [((42, -10, P), (10, -10, 1.2)), ((16, -10, P), (2, -10, 1.5))]),
    ('Pabellon Rojo',             5, [((-12, -2, 3.8), (-40, -2, 1.2)), ((-52, -4, 3.8), (-22, 8, 1.2))]),
    ('Pabellon Azul',             6, [((-56, -3, UP + 3.8), (-20, -2, UP + 1.2)), ((-26, -3, UP + 3.8), (-6, 6, UP + 1.2))]),
    ('Verde - Zona VIP',          3, [((-38, 24, UP + 5.5), (-30, 46, UP + .5)), ((-34, 34, UP + 5.0), (-28, 54, UP + .5))]),
    ('Verde - Zona IA',           3, [((-20, 70, UP + 5.5), (-13, 90, UP + .5)), ((-17, 78, UP + 5.0), (-11, 92, UP + .8))]),
    ('Verde - Auditorio Effix',   6, [((-30, 40, UP + E), (-70, 50, UP + 3)), ((-72, 30, UP + 2.5), (-66, 70, UP + 4))]),
    ('Auditorio Comunidades',     5, [((-33, 68, E), (-45, 84, 2)), ((-50, 70, E), (-36, 86, 2))]),
    ('Amarillo y Marketing',      8, [((68, 24, 12), (68, -20, 2)), ((68, 6, P), (68, -50, 1.2)), ((68, -60, P), (68, -100, 2.5))]),
    ('Zona de Comidas',           4, [((50, -110, 14), (18, -72, 1)), ((-10, -95, 8), (24, -60, 2))]),
    ('Panoramica cierre',         6, [((-150, -70, 115), (-28, 22, 8)), ((-215, 150, 235), (0, 95, 0))]),
]

obj = bpy.data.objects.new('Video_objetivo', None); s.collection.objects.link(obj)
cd = bpy.data.cameras.new('Cam_Video'); cd.lens = 24; cd.clip_start = .3; cd.clip_end = 5000
cam = bpy.data.objects.new('Cam_Video', cd); s.collection.objects.link(cam)
tr = cam.constraints.new('TRACK_TO'); tr.target = obj; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'

f = 1; CORTES = []                       # CORTES: (nombre, primer fotograma, ultimo fotograma) de cada tramo
for nombre, dur, pts in TRAMOS:
    n = round(dur * FPS); CORTES.append((nombre, f, f + n - 1))
    for i, (p, t) in enumerate(pts):
        fr = f + round(i * (n - 1) / max(len(pts) - 1, 1))
        cam.location = p; cam.keyframe_insert('location', frame=fr)
        obj.location = t; obj.keyframe_insert('location', frame=fr)
    f += n
def fcurves_de(ob):                      # Blender 4.4+ (acciones por capas/slots) o API clasica
    ac = ob.animation_data.action
    if hasattr(ac, 'layers') and len(ac.layers):
        return [fc for ly in ac.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
    return list(ac.fcurves)


for ob in (cam, obj):                    # suave dentro del tramo; el salto entre tramos cae en un solo fotograma (corte)
    for fc in fcurves_de(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'; kp.easing = 'EASE_IN_OUT'
s.camera = cam
s.frame_start, s.frame_end = 1, f - 1
s.render.fps = FPS
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
try:
    s.eevee.taa_render_samples = 8
    s.eevee.use_raytracing = False
    s.eevee.shadow_pool_size = '1024'
except Exception as e:
    print('eevee cfg', e)

# suelo hasta el horizonte (fuera del modelo) para que no se vea el borde
me = bpy.data.meshes.new('Suelo_lejano')
B = 6000; x0, x1, y0, y1 = -340, 300, -240, 390
me.from_pydata([(-B, -B, -.15), (B, -B, -.15), (B, y0, -.15), (-B, y0, -.15), (-B, y1, -.15), (B, y1, -.15), (B, B, -.15), (-B, B, -.15),
                (-B, y0, -.15), (x0, y0, -.15), (x0, y1, -.15), (-B, y1, -.15), (x1, y0, -.15), (B, y0, -.15), (B, y1, -.15), (x1, y1, -.15)],
               [], [(0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11), (12, 13, 14, 15)])
m = bpy.data.materials.new('suelo_lejano'); m.use_nodes = True
bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs[0].default_value = (.60, .61, .60, 1)
me.materials.append(m)
s.collection.objects.link(bpy.data.objects.new('Suelo_lejano', me))

FRAMES = OUT / 'video2_frames'
print('RECORRIDO', s.frame_end, 'fotogramas =', round(s.frame_end / FPS, 1), 's')
if '--codificar' in sys.argv:
    files = sorted(fn.name for fn in FRAMES.glob('f_*.jpg'))
    vs = bpy.data.scenes.new('Video'); bpy.context.window.scene = vs
    vs.render.fps = FPS; vs.render.resolution_x, vs.render.resolution_y, vs.render.resolution_percentage = 1280, 720, 100
    se = vs.sequence_editor_create(); strips = se.strips if hasattr(se, 'strips') else se.sequences
    st = strips.new_image('recorrido', str(FRAMES / files[0]), 1, 1)
    for fn in files[1:]:
        st.elements.append(fn)
    vs.frame_start, vs.frame_end = 1, len(files)
    im = vs.render.image_settings
    if hasattr(im, 'media_type'):
        im.media_type = 'VIDEO'
    im.file_format = 'FFMPEG'
    ff = vs.render.ffmpeg
    ligero = '--ligero' in sys.argv      # copia de menos peso para compartir por chat (< 30 MB)
    ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'MEDIUM' if ligero else 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = 24; ff.audio_codec = 'NONE'
    vs.render.filepath = str(OUT / ('recorrido_completo_effix_2026_ligero.mp4' if ligero else 'recorrido_completo_effix_2026.mp4'))
    bpy.ops.render.render(animation=True, scene=vs.name)
    print('VIDEO OK', len(files), 'fotogramas ->', vs.render.filepath)
elif prueba:                             # fotograma central de cada tramo, a baja resolucion
    s.render.resolution_percentage = 50
    s.eevee.taa_render_samples = 6
    solo = [int(v) for a_ in sys.argv if a_.startswith('--solo=') for v in a_[7:].split(',')]
    for k, (nombre, a, b) in enumerate(CORTES):
        if solo and k not in solo:
            continue
        for j, fr in enumerate(((a + b) // 2,) if not solo else (a + 2, (a + b) // 2, b - 2)):
            s.frame_set(fr)
            s.render.filepath = str(OUT / (f'video2_prueba_{k:02d}.png' if not solo else f'video2_prueba_{k:02d}_{j}.png'))
            bpy.ops.render.render(write_still=True)
        print('prueba', k, nombre)
else:
    FRAMES.mkdir(exist_ok=True)
    im = s.render.image_settings
    if hasattr(im, 'media_type'):
        im.media_type = 'IMAGE'
    im.file_format = 'JPEG'; im.quality = 92
    s.render.use_overwrite = False; s.render.use_placeholder = False
    s.render.filepath = str(FRAMES / 'f_')
    bpy.ops.render.render(animation=True)
    print('FOTOGRAMAS OK', len(list(FRAMES.glob('f_*.jpg'))))
