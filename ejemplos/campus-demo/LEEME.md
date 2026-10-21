# Ejemplo: Campus Demo (exteriores, varios edificios, plano PDF)

Es un lugar inventado. Tiene:
- 4 edificios y 3 niveles: el Edificio B tiene un auditorio encima que flota en "Por niveles";
- plaza, jardín, espejo de agua y cafetería en carpa;
- 15 locales: 9 escritos a mano y 6 extraídos de un **plano PDF de juguete** con cuadrícula de 1 m;
- tarimas con pantalla, sillas, árboles y 5 lugares numerados;
- marca en azul y la etiqueta "Locales".

```bash
python pipeline/generar_texturas.py
python ejemplos/campus-demo/entrada/generar_plano_demo.py          # crea entrada/plano.pdf
python pipeline/extraer_plano.py inspeccionar ejemplos/campus-demo/entrada/plano.pdf
python pipeline/extraer_plano.py extraer ejemplos/campus-demo/plano.json
python pipeline/validar_mapa.py ejemplos/campus-demo/mapa.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- ejemplos/campus-demo/mapa.json
blender -b ejemplos/campus-demo/salida/modelo.blend --python pipeline/renders.py -- ejemplos/campus-demo/mapa.json --estilo=realista --vistas=axo,niveles --tam=hd
python pipeline/componer_lamina.py ejemplos/campus-demo/salida/renders/niveles_realista.png
blender -b ejemplos/campus-demo/salida/modelo.blend --python pipeline/exportar_web.py -- ejemplos/campus-demo/mapa.json
python -m http.server 8765 --directory ejemplos/campus-demo/salida/web
```

Lo que debe salir:
- **extracción**: "6 espacios (0 sin codigo) - 180 sillas" y "6 de 6 espacios rotulados coinciden";
- **exportación**: GLB de ~1 MB, 5 lugares y 15 espacios.
