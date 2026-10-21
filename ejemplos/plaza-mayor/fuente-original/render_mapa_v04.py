"""Renders del mapa Effix 2026 (v03).

Uso: blender -b Plaza_Mayor_mapa_v04.blend --python render_mapa_v04.py -- [vistas] [--preview] [--tag=x]

Modo mapa (niveles flotando, sin techos, con pines):  mapa_iso, mapa_niveles_caja, mapa_niveles_azul_verde
Maqueta exterior (todo en su sitio, con cubiertas):    maqueta_iso, maqueta_ingreso, maqueta_ugc, maqueta_gradas
Plantas (norte a la derecha, como el PDF):             mapa_planta (nivel principal + superior + Caja piso 3),
                                                       mapa_planta_inferior (Rojo, Comunidades, Gran Salon piso 1),
                                                       mapa_planta_intermedia (Salon Multiproposito piso 2),
                                                       detalle_registro (interior de la Caja: taquillas y registro)
"""
import bpy, sys, pathlib

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
preview = '--preview' in argv
tag = next((a.split('=', 1)[1] for a in argv if a.startswith('--tag=')), '')
views = [a for a in argv if not a.startswith('--')] or ['mapa_iso', 'maqueta_iso', 'mapa_planta', 'mapa_planta_inferior']
s = bpy.context.scene
OUT = R / 'renders_v04'
OUT.mkdir(exist_ok=True)
LC = {c.name[:3].rstrip('_'): c for c in bpy.context.view_layer.layer_collection.children}
KEY = {'ref': '00', 'ext_base': '05', 'sup': '06', 'ext_sup': '07', 'inf': '08', 'gs': '09', 'multi': '10', 'caja': '11', 'shell': '12',
       'losa': '13', 'pins_base': '19a', 'pins_sup': '19b', 'pins_inf': '19c', 'pins_gs': '19d', 'pins_multi': '19e', 'pins_caja': '19f',
       'ctx': '20', 'guias': '21', 'huella': '22'}
ROOTS = {'sup': 'RAIZ_nivel_superior', 'multi': 'RAIZ_multiproposito', 'caja': 'RAIZ_caja_piso3', 'shell': 'RAIZ_caja_caparazon'}

VIEWS = {  # vista: (modo, camara, resolucion)
    'mapa_iso': ('mapa', 'Cam_Iso', (2800, 1960)),
    'mapa_niveles_caja': ('mapa', 'Cam_Niveles_Caja', (2400, 1800)),
    'mapa_niveles_azul_verde': ('mapa', 'Cam_Niveles_Azul_Verde', (2400, 1680)),
    'maqueta_iso': ('maqueta', 'Cam_Iso', (2800, 1960)),
    'maqueta_ingreso': ('foto', 'Cam_Ingreso_Caja', (2400, 1680)),
    'maqueta_ugc': ('foto', 'Cam_UGC', (2400, 1680)),
    'maqueta_gradas': ('foto', 'Cam_Gradas', (2400, 1680)),
    'maqueta_fachada_gs': ('foto', 'Cam_Fachada_GS', (2400, 1680)),
    'maqueta_carros': ('foto', 'Cam_Carros', (2400, 1680)),
    'detalle_gran_salon': ('planta_inf', 'Cam_Planta_GS', (2400, 1800)),
    'maqueta_portico': ('foto', 'Cam_Portico', (2400, 1680)),
    'mapa_verde_tarima': ('foto', 'Cam_Verde_Tarima', (2400, 1680)),
    'mapa_planta': ('planta', 'Cam_Planta', (3000, 2100)),
    'mapa_planta_inferior': ('planta_inf', 'Cam_Planta', (3000, 2100)),
    'mapa_planta_intermedia': ('planta_mid', 'Cam_Planta', (3000, 2100)),
    'detalle_registro': ('detalle', 'Cam_Planta_Caja', (2400, 1680)),
}
ALL_PINS = ('pins_base', 'pins_sup', 'pins_inf', 'pins_gs', 'pins_multi', 'pins_caja')
MODES = {  # modo: (niveles flotando, colecciones ocultas)
    'mapa': (True, ('ext_base', 'ext_sup', 'losa')),
    'maqueta': (False, ('guias', 'huella', 'pins_inf', 'pins_gs', 'pins_multi', 'pins_caja')),
    'foto': (False, ('guias', 'huella', 'ctx') + ALL_PINS),
    'planta': (False, ('ext_base', 'ext_sup', 'shell', 'guias', 'pins_inf', 'pins_gs', 'pins_multi')),
    'detalle': (False, ('ext_base', 'ext_sup', 'shell', 'guias', 'ctx') + ALL_PINS),
    'planta_inf': (False, ('ext_base', 'ext_sup', 'sup', 'caja', 'huella', 'shell', 'multi', 'losa', 'guias', 'pins_sup', 'pins_caja', 'pins_multi')),
    'planta_mid': (False, ('ext_base', 'ext_sup', 'sup', 'caja', 'huella', 'shell', 'losa', 'guias', 'pins_sup', 'pins_caja', 'pins_gs')),
}


def show(k, on):
    LC[KEY[k]].exclude = not on


def render(view):
    mode, cam, res = VIEWS[view]
    floating, hidden = MODES[mode]
    for k in KEY:
        show(k, k not in hidden and k != 'ref')
    for k, name in ROOTS.items():
        bpy.data.objects[name].location.z = s['LIFT_' + k] if floating else 0.0
    for k in ('sup', 'multi', 'caja', 'shell'):          # los niveles flotantes no proyectan sombra sobre lo de abajo
        for ob in LC[KEY[k]].collection.objects:
            ob.visible_shadow = not floating
    s.camera = bpy.data.objects[cam]
    bpy.data.objects['Orientacion_rotulos'].rotation_euler = s.camera.rotation_euler
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 50 if preview else 100
    s.render.filepath = str(OUT / f'{view}{"_" + tag if tag else ""}{"_preview" if preview else ""}.png')
    bpy.ops.render.render(write_still=True)
    print('render', s.render.filepath)


try:
    s.eevee.taa_render_samples = 16 if preview else 64
    s.eevee.use_shadows = True
    s.eevee.shadow_pool_size = '1024'
    s.eevee.use_raytracing = not preview
except Exception as e:
    print('eevee cfg', e)
for v in views:
    render(v)
