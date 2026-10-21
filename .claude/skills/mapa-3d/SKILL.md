---
name: mapa-3d
description: Orquestador del Kit Mapa 3D. Convierte cualquier plano (PDF, CAD/DXF o imagen) de cualquier lugar —edificio, oficina, casa, campus, centro comercial, hotel, hospital, parque, recinto de eventos— en un modelo 3D con renders profesionales y un mapa web navegable. Úsalo al empezar, cuando alguien diga "quiero mi plano en 3D" o "un mapa 3D de mi lugar", o cuando no sepas en qué fase vas. Entrevista, pide el plano y encadena los demás skills mapa-*.
---

# Kit Mapa 3D, de punta a punta

La persona trae un plano y quiere verlo en 3D con calidad de agencia. Hay tres entregables posibles; pregunta cuáles quiere:

1. **Renders y láminas**: imágenes de alta resolución en cuatro estilos (realista, maqueta blanca, ilustrado, noche),
   con título, lugares numerados, leyenda, norte y escala. PNG y PDF para imprimir.
2. **Mapa web 3D**: el lugar navegable en el celular y el computador. Tiene modo "Por niveles", lugares con pin,
   buscador de espacios (salas, locales, stands, oficinas) y links directos para QR.
3. **Video de recorrido**: un MP4 que recorre el lugar.

Referencias de calidad: `ejemplos/campus-demo/` (exteriores, varios edificios), `ejemplos/oficina-demo/` (un edificio de
tres pisos importado de CAD) y `docs/CASO-ORIGEN.md` (el primer mapa real, un centro de convenciones).

## Fase 0 · Entorno (una vez)

| Necesita | Verificar |
|---|---|
| Python 3.10+ | `python --version` |
| Librerías | `pip install -r requirements.txt` (PyMuPDF, ezdxf, numpy, Pillow) |
| Blender 4.2+ (probado en 5.2) | `blender --version`. En Windows: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"` |
| Texturas | `python pipeline/generar_texturas.py` (procedurales, sin derechos de terceros) |

Si falta algo, explica cómo instalarlo y no lo instales sin permiso. Construye un demo para probar el entorno y
muéstraselo a la persona: así ve el nivel de calidad antes de empezar.

## Fase 1 · Entrevista → `docs/ENTREVISTA.md`

Pide lo que bloquea y deja el resto para cuando haya algo que mostrar:
- **El plano y su formato**: PDF vectorial, DXF/DWG de CAD, imagen o croquis.
- **Una medida conocida**, si no es CAD.
- **Pisos**: cuántos son y qué queda encima de qué.
- **Alturas.**
- **Qué marcar**: lugares con pin y espacios buscables.
- **Marca**: título, color y logo.
- **Entregables**: cuáles de los tres quiere.

Crea el proyecto con `python pipeline/nuevo_proyecto.py <id> "Nombre"` y copia el material a `proyectos/<id>/entrada/`.

Antes de construir, escribe en una línea qué significa **terminado**. Ejemplo: "lámina A3 en estilo ilustrado de los
3 pisos, más el mapa web publicado con las 24 salas buscables".

## Fase 2 · Plano a metros → skill `mapa-plano-a-metros`

PDF (vectores, escala por FFT o cotas), DXF (capas y unidades) o imagen (dos puntos de calibración y cuadrícula en metros).
Sale `salida/plano_m.json` con espacios, muros, edificios, zonas y mobiliario, y una vista previa en PNG.

## Fase 3 · Modelo → skill `mapa-modelo-blender`

Escribe `mapa.json` con niveles, edificios, zonas, objetos, lugares y la marca, y valídalo. Después construye y
revisa renders `--preview`. **Itera con la persona aquí**: es donde salen las correcciones de niveles, orientación y alturas.

## Fase 4 · Entregables

- Renders y láminas → skill `mapa-render-profesional`.
- Mapa web → skill `mapa-visor-web`. Para meterlo dentro de una app existente, skill `mapa-integrar-app`.
- Video → skill `mapa-video-recorrido`.

## Fase 5 · Control de calidad → skill `mapa-control-calidad`

Antes de entregar, pasa la lista completa: escala, niveles, textos, peso web, celular y láminas. No entregues sin pasarla.

## Cómo comunicarte

- **Muestra imágenes en cada vuelta.** Lee los PNG con Read antes de mostrarlos y envíalos con SendUserFile. Pide que
  marquen sobre la imagen lo que está mal.
- **Una pregunta a la vez** cuando la respuesta cambia el modelo; agrupa las menores.
- **Nunca inventes medidas ni pisos.** Lo aproximado se dice y queda en `marca.nota`.
- **No publiques en internet sin permiso explícito.**
- **Al final entrega** los archivos (láminas, carpeta web o link, video) y una lista corta de lo que quedó aproximado.
