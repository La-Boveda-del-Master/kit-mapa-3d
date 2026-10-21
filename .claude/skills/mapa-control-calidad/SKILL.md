---
name: mapa-control-calidad
description: Control de calidad antes de entregar un trabajo del Kit Mapa 3D. Revisa escala y geometría contra el plano, niveles, textos, materiales, renders y láminas, y el mapa web (peso, celular, búsqueda, links). Úsalo siempre antes de decir "terminado" o de publicar.
---

# Control de calidad

Pasa cada punto y anota el resultado. Si algo falla, arréglalo o díselo a la persona; nunca lo escondas.

## Geometría y escala

- [ ] `python pipeline/validar_mapa.py proyectos/<id>/mapa.json` termina sin errores.
- [ ] La validación de escala del plano dio más del 90 % (PDF), o la unidad del DXF está confirmada, o la imagen se
      calibró con una medida conocida.
- [ ] Render `planta` (con `--calco` si hay imagen) comparado con el plano original: ningún edificio desplazado más de 1 m.
- [ ] 3 o 4 medidas conocidas comprobadas en el modelo: largo de un edificio, ancho de un espacio, altura de un piso.
- [ ] Los niveles están bien apilados: lo que va encima flota exactamente sobre lo de abajo en "Por niveles".
- [ ] Nada flotando ni enterrado; las escaleras llegan al piso de arriba.

## Contenido

- [ ] Todos los lugares (pines) que pidió la persona, en orden de recorrido, con nombre y detalle.
- [ ] Todos los espacios con código y, si hay, nombre. No hay códigos repetidos (el validador avisa).
- [ ] Textos legibles, sin salirse de su espacio, sin tildes rotas.
- [ ] `marca.nota` dice lo que es aproximado.

## Renders y láminas (ver la lista de `mapa-render-profesional`)

- [ ] Composición, luz, color, textos y ruido revisados con zoom al 100 %.
- [ ] La lámina tiene título, leyenda completa, norte y, en planta, escala.
- [ ] El PDF abre bien y pesa lo razonable (menos de 30 MB en A3).

## Mapa web

- [ ] El exportador dice que el GLB pesa menos de 10 MB.
- [ ] Abre sin errores en la consola, tanto en escritorio como en tamaño celular.
- [ ] "Por niveles" separa y muestra los interiores; tocar un lugar tapado cambia solo de modo.
- [ ] El buscador encuentra por código con y sin ceros ("a5" = "A05") y por nombre.
- [ ] Los links `?lugar=N` y `?espacio=CODIGO` abren enfocados.
- [ ] La brújula apunta al norte y al tocarla vuelve con el norte arriba.
- [ ] El color de marca, el título y el logo son los correctos.
- [ ] Publicado (si se pidió y con permiso): el link real abre en un celular de verdad.

## Entrega

- [ ] Se entregan los archivos (láminas PNG/PDF, carpeta `web/` o link, video) y no solo rutas internas.
- [ ] Va una lista corta de lo que quedó aproximado o pendiente.
