# Ejemplo: Oficina Demo (un edificio de 3 pisos, plano CAD en DXF)

Es una oficina inventada, dibujada como la entregaría un arquitecto:
- un **DXF en milímetros**;
- los **3 pisos lado a lado** en el mismo archivo;
- capas separadas para edificio, muros, espacios (salas), textos y mobiliario.

El kit lee las capas, apila los pisos (cubierta solo en el último) y rotula cada sala con su nombre.
En "Por niveles" se ven los tres pisos por dentro, con escaleras, escritorios y el auditorio.

```bash
python pipeline/generar_texturas.py
python ejemplos/oficina-demo/entrada/generar_dxf_demo.py           # crea entrada/plano.dxf
python pipeline/extraer_plano.py inspeccionar ejemplos/oficina-demo/entrada/plano.dxf
python pipeline/extraer_plano.py extraer ejemplos/oficina-demo/plano.json
python pipeline/validar_mapa.py ejemplos/oficina-demo/mapa.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- ejemplos/oficina-demo/mapa.json
blender -b ejemplos/oficina-demo/salida/modelo.blend --python pipeline/renders.py -- ejemplos/oficina-demo/mapa.json --estilo=ilustrado --vistas=niveles --tam=hd
python pipeline/componer_lamina.py ejemplos/oficina-demo/salida/renders/niveles_ilustrado.png
blender -b ejemplos/oficina-demo/salida/modelo.blend --python pipeline/exportar_web.py -- ejemplos/oficina-demo/mapa.json
python -m http.server 8766 --directory ejemplos/oficina-demo/salida/web
```

Lo que debe salir en la extracción: "3 edificios - 39 muros - 16 espacios (0 sin codigo) - 9 objetos".
