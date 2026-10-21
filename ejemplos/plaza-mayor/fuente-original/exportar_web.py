"""Exporta el modelo v04 a glTF binario para el mapa web (web/mapa.glb + web/datos.json).

Uso: blender -b Plaza_Mayor_mapa_v04.blend --python exportar_web.py
- Quita lo que el visor dibuja por su cuenta (pines, rotulos, calco del PDF, camaras, luces).
- Une los codigos de stand de cada nivel en una sola malla (menos llamadas de dibujo).
- Cada objeto lleva en `extras.grupo` su nivel, y los niveles flotantes cuelgan de los vacios RAIZ_*.
No guarda cambios en el .blend.
"""
import bpy, bmesh, json, pathlib

R = pathlib.Path(r'D:/Usuario/Documents/ChatGPT/Mapa Plaza mayor')
WEB = R / 'web'
WEB.mkdir(exist_ok=True)
s = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# 1) fuera: pines, rotulos de contexto, calco, camaras y luces
for o in list(bpy.data.objects):
    g = o.get('grupo', '')
    if g.startswith('pins_') or g in ('ctx', 'ref') or o.type in ('CAMERA', 'LIGHT') or o.name == 'Orientacion_rotulos':
        bpy.data.objects.remove(o, do_unlink=True)

# 2) textos -> mallas. Codigos de stand: una sola malla por nivel; avisos y letreros: uno a uno.
dg.update()
codes = {}
for o in [o for o in bpy.data.objects if o.type == 'FONT']:
    is_code = o.name.startswith('Txt_')
    if is_code:
        o.data.extrude = 0.0
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
    me = bpy.data.meshes.new('Codigos_stands_' + g); bm.to_mesh(me); bm.free(); me.materials.append(m)
    n = bpy.data.objects.new('Codigos_stands_' + g, me); coll.objects.link(n); n.parent = parent; n['grupo'] = g

# 3) niveles en su sitio (sin separar) y exportacion
for name in ('RAIZ_nivel_superior', 'RAIZ_multiproposito', 'RAIZ_caja_piso3', 'RAIZ_caja_caparazon'):
    bpy.data.objects[name].location.z = 0.0
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = False
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
bpy.ops.export_scene.gltf(
    filepath=str(WEB / 'mapa.glb'), export_format='GLB', export_extras=True, export_cameras=False, export_lights=False,
    export_apply=True, export_yup=True, export_image_format='AUTO', export_animations=False,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=16, export_draco_normal_quantization=10, export_draco_texcoord_quantization=16)

# 4) datos del visor: pines, separacion de niveles
pins = json.loads((R / 'leyenda_v04.json').read_text(encoding='utf8'))
datos = {'lift': {k[5:]: s[k] for k in s.keys() if k.startswith('LIFT_')},
         'raices': {'sup': 'RAIZ_nivel_superior', 'multi': 'RAIZ_multiproposito', 'caja': 'RAIZ_caja_piso3', 'shell': 'RAIZ_caja_caparazon'},
         'pines': pins}
(WEB / 'datos.json').write_text(json.dumps(datos, ensure_ascii=False), encoding='utf8')
# sello de version en la pagina para que el navegador no use el modelo en cache
import re, time
_v = str(int(time.time()))
for _f, _pat in (('app.js', r"const VER = '\d+';"), ('index.html', None)):
    _p = WEB / _f; _t = _p.read_text(encoding='utf8')
    if _pat:
        _t = re.sub(_pat, "const VER = '%s';" % _v, _t)
    else:
        _t = re.sub(r'app\.js\?v=\d+', 'app.js?v=' + _v, _t); _t = re.sub(r'estilos\.css\?v=\d+', 'estilos.css?v=' + _v, _t)
    _p.write_text(_t, encoding='utf8')
print('EXPORT OK', tris, 'triangulos;', round((WEB / 'mapa.glb').stat().st_size / 1e6, 2), 'MB')
