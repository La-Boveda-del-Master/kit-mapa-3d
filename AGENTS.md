# Kit Mapa 3D — instrucciones para el agente

Este repo convierte **cualquier plano** (PDF, CAD/DXF o imagen) de **cualquier lugar** en tres entregables:
**renders y láminas de calidad profesional**, un **mapa web 3D navegable** y un **video de recorrido**.
Sirve para un edificio, una oficina, una casa, un campus, un centro comercial, un hotel, un hospital, un parque o un recinto de eventos.

Quien abre este repo normalmente **no es técnico**. Tu trabajo es guiarlo de punta a punta:
1. preguntar lo que falta;
2. pedirle el plano;
3. construir;
4. mostrar avances con imágenes;
5. entregar con calidad de agencia.

Habla en su idioma (por defecto español) y sin jerga.

## Cómo trabajar

1. **Empieza con el skill `mapa-3d`** (`.claude/skills/mapa-3d/SKILL.md`). Es el orquestador: te dice en qué fase
   estás y qué skill usar en cada una.
   - `mapa-plano-a-metros`
   - `mapa-modelo-blender`
   - `mapa-render-profesional`
   - `mapa-visor-web`
   - `mapa-video-recorrido`
   - `mapa-integrar-app`
   - `mapa-control-calidad`
2. **Entrevista antes de construir** (`docs/ENTREVISTA.md`). No inventes medidas, pisos ni alturas: pregunta, o márcalo
   como aproximado en `marca.nota`.
3. **Un lugar = una carpeta** `proyectos/<id>/`, creada con `python pipeline/nuevo_proyecto.py <id> "Nombre"`.
   - `entrada/`: lo que entrega la persona;
   - `salida/`: lo que se genera;
   - `mapa.json`: describe el lugar (formato en `docs/FORMATO-MAPA.md`).
4. **Muestra imágenes en cada vuelta.** Usa renders `--preview` y el visor local. La persona corrige mejor sobre una imagen.
5. **Pasa `mapa-control-calidad` antes de decir "terminado".**
6. **No publiques ni crees cuentas o repos sin permiso explícito.**

## Pipeline

```
python pipeline/generar_texturas.py                                         # una vez
python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.pdf|plano.dxf
python pipeline/calibrar_imagen.py proyectos/<id>/entrada/plano.jpg [--puntos ... --distancia ...]
python pipeline/extraer_plano.py extraer proyectos/<id>/plano.json          # -> salida/plano_m.json
python pipeline/validar_mapa.py proyectos/<id>/mapa.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- proyectos/<id>/mapa.json
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/mapa.json --estilo=realista --vistas=axo,planta,niveles
python pipeline/componer_lamina.py proyectos/<id>/salida/renders/axo_realista.png
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/exportar_web.py -- proyectos/<id>/mapa.json
python -m http.server 8765 --directory proyectos/<id>/salida/web
```

En Windows Blender suele estar en `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`.

## Reglas que se aprendieron caro (no las repitas)

- **Mundo: +X Este, +Y Norte, Z arriba, 1 unidad = 1 metro.** En three.js es `(x, z, -y)`. Todo el pipeline lo asume.
- **Calibra y valida la escala antes de modelar**: cuadrícula por FFT, unidad del DXF o dos puntos de medida conocida.
  Después compara contra medidas rotuladas.
- **Los planos dibujan "al lado" lo que va "encima".** Pregunta qué piso va sobre cuál. En el modelo los pisos de arriba
  **flotan sobre** los de abajo en la misma planta; nunca desplazados a un lado.
- **Si hay medidas en conflicto, pregunta cuál manda** y anótalo. No promedies.
- **El GLB web pesa como máximo 10 MB.** Une mallas, usa Draco y no metas geometría que nadie va a ver.
- **Blender 5**:
  - busca los nodos por tipo (`BSDF_PRINCIPLED`), no por nombre;
  - el editor de video usa `strips` (antes `sequences`);
  - Cycles se activa como addon.
- **No escribas parches de Python dentro de heredocs de Bash**, porque rompen `\n` y las comillas. Usa Write o Edit.

Más casos en `docs/PROBLEMAS.md`. El primer mapa real que dio origen al kit está en `docs/CASO-ORIGEN.md`.

## Cuando lo genérico no alcanza

`construir_modelo.py` cubre edificios por piso con fachada, ventanas, puertas y cubierta; muros interiores; espacios;
zonas; escaleras; mobiliario; tarimas con pantalla; sillas; carpas y árboles.

Para piezas únicas (gradas, rampas, escaleras eléctricas, puentes, celosías, cubiertas curvas) escribe
`proyectos/<id>/detalles.py`. Debe seguir el mismo patrón:
- acumular la geometría con `MB`;
- poner la propiedad `grupo`;
- colgar del padre `RAIZ_<nivel>` si el nivel se separa.

Cómo hacerlo está en el skill `mapa-modelo-blender`, y hay un catálogo de piezas en
`ejemplos/caso-origen-plaza-mayor/fuente-original/construir_mapa_v04.py`.
