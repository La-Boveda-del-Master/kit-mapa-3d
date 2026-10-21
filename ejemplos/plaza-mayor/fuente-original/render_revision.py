"""Renders rapidos de revision: interior del Gran Salon (cielo y puertas) y exterior con las alturas de los pabellones.

Uso: blender -b Plaza_Mayor_mapa_v04.blend --python render_revision.py
Salida: renders_v04/revision_*.jpg (1280x720). No guarda cambios en el .blend.
"""
import bpy, pathlib

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
OUT = R / 'renders_v04'
s = bpy.context.scene
OCULTAR = ('00', '19a', '19b', '19c', '19d', '19e', '19f', '20', '21', '22')
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = lc.name.split('_')[0] in OCULTAR
for n in ('RAIZ_nivel_superior', 'RAIZ_multiproposito', 'RAIZ_caja_piso3', 'RAIZ_caja_caparazon'):
    bpy.data.objects[n].location.z = 0.0

GS = -9.0
VISTAS = [  # (nombre, camara, objetivo, lente); el prefijo x_ quita cubiertas y muros altos (corte)
    ('gs_cielo_tarima', (11, 212, GS + 1.7), (11, 262, GS + 5.5), 16),
    ('gs_lobby', (-15, 181, GS + 1.7), (36, 186, GS + 3.0), 14),             # lobby: escaleras electricas y Zona Black al fondo
    ('gs_frente', (12, 175, GS + 1.7), (6, 202, GS + 2.2), 16),              # frente de vidrio GRAN SALON
    ('gs_pasillo', (-20.5, 204, GS + 1.7), (-16, 265, GS + 2.0), 14),        # pasillo lateral occidental
    ('hall_gradas_comidas', (22, -46, 8), (22, -18, 2.5), 22),               # Hall desde la Zona de Comidas: gradas
    ('hall_interior', (40, -9, 5.6), (0, -8, 4.5), 14),                      # Hall hacia el Azul
    ('x_hall_corte', (22, -60, 45), (22, -8, 0), 30),                        # corte aereo del Hall y sus gradas
    ('rojo_gradas', (-30, -17, 4.3), (-1, -17.5, 1.5), 18),                  # Rojo: gradas que suben al Hall
    ('amarillo_hall', (76, -12, 6), (46, -12, 2), 16),                       # Amarillo: gradas que suben al Hall
    ('amarillo_division', (68, -15, 9), (68, -75, 3), 14),                   # Amarillo: nave unica y division temporal
    ('verde_nave', (-50, 30, 5.6 + 3), (-50, 92, 5.6 + 8), 14),              # Verde: arcos
    ('blanco_hacia_plazoleta', (22, 10, 1.7), (22, 98, 5.5), 16),
    ('x_black_corte', (60, 215, GS + 38), (36, 228, GS), 24),                # Zona Black: salas de comisiones (corte)
    ('x_verde_pasillo', (-10, 5, 40), (-36, 45, 5.6), 28),                   # pasillo Azul <-> Verde sin muro
    ('exterior_alturas', (150, -150, 70), (10, 20, 6), 30),
]
obj = bpy.data.objects.new('Rev_objetivo', None); s.collection.objects.link(obj)
cd = bpy.data.cameras.new('Cam_Rev'); cd.clip_start = .3; cd.clip_end = 5000
cam = bpy.data.objects.new('Cam_Rev', cd); s.collection.objects.link(cam)
tr = cam.constraints.new('TRACK_TO'); tr.target = obj; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
s.camera = cam
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
im = s.render.image_settings
if hasattr(im, 'media_type'):
    im.media_type = 'IMAGE'
im.file_format = 'JPEG'; im.quality = 90
try:
    s.eevee.taa_render_samples = 16
except Exception as e:
    print('eevee cfg', e)
for nombre, p, t, lente in VISTAS:
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name[:2] in ('05', '07'):
            lc.exclude = nombre.startswith('x_')
        if lc.name[:2] in ('10', '11', '12', '13'):
            lc.exclude = nombre.startswith('x_black')
    cam.location = p; obj.location = t; cd.lens = lente
    s.render.filepath = str(OUT / f'revision_{nombre}.jpg')
    bpy.ops.render.render(write_still=True)
    print('REVISION', nombre)
