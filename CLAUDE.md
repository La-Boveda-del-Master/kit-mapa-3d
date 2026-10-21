# Kit Mapa 3D de Recintos — instrucciones para el agente

Este repo convierte el **plano de un recinto** (centro de convenciones, feria, coliseo, campus, centro comercial) en un
**mapa 3D navegable en la web**: pabellones por niveles, stands buscables, pines de lugares, renders y video de recorrido.
Nació del mapa de Plaza Mayor Medellín para Feria Effix 2026 (ver `ejemplos/plaza-mayor/`).

Quien abre este repo normalmente **no es técnico**. Tu trabajo es guiarlo de punta a punta: preguntar lo que falta,
pedirle el plano, construir, mostrarle el resultado y publicarlo. Habla en su idioma (por defecto español), sin jerga.

## Cómo trabajar

1. **Empieza con el skill `mapa-3d-recinto`** (`.claude/skills/mapa-3d-recinto/SKILL.md`). Es el orquestador: dice en qué
   fase estás y qué skill usar en cada una.
2. **Entrevista antes de construir.** Las preguntas están en `docs/ENTREVISTA.md`. No inventes medidas, niveles ni
   alturas: si no las tienes, pregunta o márcalas como "aproximado" en `evento.nota`.
3. **Un recinto = una carpeta** `proyectos/<id>/` (créala con `python pipeline/nuevo_proyecto.py <id> "Nombre"`).
   Lo que entrega la persona va en `proyectos/<id>/entrada/`; lo que se genera, en `proyectos/<id>/salida/`.
4. **Muestra avances seguido.** Después de cada construcción: renders de vista previa (`pipeline/renders.py --preview`)
   y el visor local. La persona corrige mejor sobre una imagen que sobre una descripción.
5. **No publiques sin permiso.** Desplegar a internet, crear repos o tocar la app de alguien se confirma antes.

## Pipeline (resumen; detalle en cada skill)

```
python pipeline/generar_texturas.py                                    # una vez
python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.pdf
python pipeline/extraer_plano.py extraer proyectos/<id>/plano.json     # stands/sillas/zonas en metros
python pipeline/validar_recinto.py proyectos/<id>/recinto.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- proyectos/<id>/recinto.json
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/exportar_web.py -- proyectos/<id>/recinto.json
python -m http.server 8765 --directory proyectos/<id>/salida/web      # ver en http://localhost:8765
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/recinto.json --preview
```

En Windows Blender suele estar en `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`.

## Reglas que salieron caras en Plaza Mayor (no las repitas)

- **Mundo: +X Este, +Y Norte, Z arriba, 1 unidad = 1 metro.** En three.js es `(x, z, -y)`. Todo el pipeline lo asume.
- **Calibra y valida la escala antes de modelar.** Cuadrícula de fondo por FFT o una medida conocida; luego compara los
  stands rotulados "6x3" contra su tamaño dibujado. Si coincide menos del 90 %, la escala o la región están mal.
- **Los planos dibujan "al lado" lo que va "encima".** Pregunta explícitamente qué piso queda sobre cuál. En el mapa los
  niveles de arriba **flotan sobre** los de abajo (misma planta), nunca se dibujan desplazados a un lado.
- **Medidas en conflicto (PDF vs. plano oficial vs. realidad): pregunta cuál manda** y anótalo.
- **Peso del GLB ≤ 10 MB** para celular: une mallas, Draco nivel 6, nada de geometría que no se ve.
- **Versiona el GLB** (`?v=`): el exportador ya sella la versión; si sirves desde otra app, cambia el número.
- **Blender 5:** busca nodos por tipo (`BSDF_PRINCIPLED`), no por nombre (cambia con el idioma); el VSE usa
  `strips` (antes `sequences`).
- **No escribas parches de Python dentro de heredocs de Bash** (rompen `\n` y comillas): usa Write/Edit.

Más en `docs/PROBLEMAS.md` y en el caso real `docs/CASO-PLAZA-MAYOR.md`.

## Cuando lo genérico no alcanza

`construir_modelo.py` cubre pabellones, puertas, cubiertas, niveles, zonas, stands, tarimas con pantalla LED, sillas,
carpas, árboles y cajas. Para detalles únicos (gradas, escaleras eléctricas, celosías, puentes, fachadas especiales)
escribe un script aparte `proyectos/<id>/detalles.py` que abra `salida/modelo.blend`, agregue la geometría con el mismo
patrón (`MB`, propiedad `grupo`, padre `RAIZ_<nivel>`) y guarde. El original de Plaza Mayor
(`ejemplos/plaza-mayor/fuente-original/construir_mapa_v04.py`, unas 2.100 líneas) es la referencia de todo lo que se puede hacer.
