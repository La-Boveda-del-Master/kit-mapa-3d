---
name: mapa-3d-recinto
description: Orquestador para crear el mapa 3D navegable de un recinto (centro de convenciones, feria, coliseo, campus) a partir de su plano. Úsalo al empezar, cuando alguien diga "quiero el mapa 3D de mi evento/recinto", o cuando no sepas en qué fase vas. Entrevista a la persona, pide el plano y encadena los demás skills mapa-*.
---

# Mapa 3D de un recinto — de punta a punta

La persona quiere un mapa como el de Plaza Mayor (`ejemplos/plaza-mayor/renders/`): el recinto en 3D, con niveles que
se separan, pines numerados de lugares, stands buscables, y que funcione en el celular. Tu trabajo es llevarla de
"tengo un PDF" a "tengo un link". Asume que no es técnica.

## Fase 0 · Preparar el entorno (una vez)

Verifica y, si falta algo, explica cómo instalarlo (no lo instales sin permiso):

| Necesita | Cómo verificar |
|---|---|
| Python 3.10+ | `python --version` |
| Librerías | `pip install -r requirements.txt` (PyMuPDF, numpy, Pillow) |
| Blender 4.2+ (probado en 5.2) | `blender --version`; en Windows: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --version` |
| Texturas | `python pipeline/generar_texturas.py` (crea `texturas/`, 54 archivos, todo procedural) |

Prueba rápida de que todo sirve: construye el demo (`ejemplos/demo-centro-eventos/`, ver su LEEME).

## Fase 1 · Entrevista (no la saltes)

Usa `docs/ENTREVISTA.md`. Pide primero lo imprescindible y deja el resto para cuando haya algo que mostrar:

1. **El plano**: PDF técnico (ideal: vectorial, con cuadrícula o cotas). Si solo hay imagen, sirve, pero se calibra a mano.
2. **Qué es cada edificio y en qué nivel está**: qué queda encima de qué, qué está en sótano, a qué nivel está la calle.
3. **Alturas** aproximadas de cada pabellón (o fotos para estimarlas).
4. **Lugares a marcar con pin** (ingreso, registro, auditorios, baños, comidas…) en el orden en que el público los recorre.
5. **Para qué es**: solo web, embebido en una app, video, impresión. Cambia lo que se prioriza.

Con eso: `python pipeline/nuevo_proyecto.py <id> "Nombre"` y copia el material a `proyectos/<id>/entrada/`.

Antes de construir, deja escrito en una línea qué significa **terminado** (ej.: "link público que abre en celular con
los 6 pabellones, los 120 stands buscables y 12 pines").

## Fase 2 · Plano a metros → skill `mapa-plano-a-metros`

Inspeccionar el PDF, calibrar escala, definir regiones, extraer stands/sillas/zonas, validar contra rótulos.
Sale `proyectos/<id>/salida/plano_m.json` y una vista previa PNG que debes mostrarle a la persona.

## Fase 3 · Modelo 3D → skill `mapa-modelo-blender`

Escribir `recinto.json` (edificios, niveles, zonas, objetos, pines), validar, construir, mirar renders de vista previa,
corregir. Itera aquí con la persona: es donde más correcciones salen (niveles, orientación de tarimas, alturas).

## Fase 4 · Visor web → skill `mapa-visor-web`

Exportar, abrir local, probar en tamaño celular, y publicar (Vercel / Netlify / GitHub Pages) **con permiso**.

## Fase 5 (opcional)

- Integrar en una app React/Next con stands de una base de datos y GPS → skill `mapa-integrar-app`.
- Renders para presentar o imprimir y video de recorrido → skill `mapa-renders-video`.

## Cómo comunicarte

- Muestra imágenes en cada vuelta (renders `--preview` o captura del visor). Pide correcciones sobre la imagen:
  "márcame en rojo lo que está mal".
- Una pregunta a la vez cuando la respuesta cambia el modelo; agrupa las menores.
- Cuando algo es aproximado, dilo y déjalo en `evento.nota` (el visor lo muestra).
- Al final entrega: el link (o la carpeta `salida/web/`), los renders, y qué quedó aproximado o pendiente.
