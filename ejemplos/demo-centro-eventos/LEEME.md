# Demo: Centro de Eventos Demo

Recinto inventado para probar el kit de punta a punta. Tiene:
- 4 edificios y 3 niveles: el Pabellón B tiene un auditorio encima que flota en "Por niveles";
- zonas (plaza, jardín, espejo de agua, comidas);
- 15 stands: 9 escritos a mano y 6 extraídos del plano PDF de juguete;
- 2 tarimas con pantalla LED, sillas, una carpa, árboles y 5 pines.

```bash
python pipeline/generar_texturas.py
python ejemplos/demo-centro-eventos/entrada/generar_plano_demo.py      # crea entrada/plano.pdf
python pipeline/extraer_plano.py inspeccionar ejemplos/demo-centro-eventos/entrada/plano.pdf
python pipeline/extraer_plano.py extraer ejemplos/demo-centro-eventos/plano.json
python pipeline/validar_recinto.py ejemplos/demo-centro-eventos/recinto.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- ejemplos/demo-centro-eventos/recinto.json
blender -b ejemplos/demo-centro-eventos/salida/modelo.blend --python pipeline/exportar_web.py -- ejemplos/demo-centro-eventos/recinto.json
blender -b ejemplos/demo-centro-eventos/salida/modelo.blend --python pipeline/renders.py -- ejemplos/demo-centro-eventos/recinto.json --preview
python -m http.server 8765 --directory ejemplos/demo-centro-eventos/salida/web
```

Resultado esperado:
- extracción: "6 stands (0 sin codigo) - 180 sillas" y "6 de 6 stands rotulados coinciden";
- exportación: un GLB de ~1 MB con 5 pines y 15 stands.
