---
name: mapa-plano-a-metros
description: Lleva cualquier plano a metros reales para el Kit Mapa 3D. Sirve para PDF vectorial (escala por cuadrícula FFT o cotas), CAD en DXF (capas y unidades; un DWG se convierte antes) e imagen o escaneo (calibración con dos puntos y cuadrícula en metros). Separa pisos dibujados aparte y extrae espacios con su código, muros, edificios, sillas, zonas y mobiliario a plano_m.json. Úsalo en la fase 2 o cuando la escala o la posición de algo no cuadre.
---

# Del plano a metros

Todo termina en `proyectos/<id>/salida/plano_m.json` (se importa en mapa.json con `"importar": "salida/plano_m.json"`)
o en coordenadas que escribes a mano en `mapa.json`. Mundo: **+X Este, +Y Norte, metros**.

Elige el camino según el plano que trajo la persona (detalle en `docs/ENTRADAS.md`):

| Plano | Camino | Precisión |
|---|---|---|
| DXF o DWG de CAD | B | exacta, porque ya viene en unidades reales |
| PDF exportado de CAD o de diseño (vectorial) | A | muy alta, con calibración |
| Imagen, escaneo, foto, captura | C | buena si la imagen está derecha y hay una medida conocida |
| Croquis a mano o descripción | C con la medida que dé la persona, o dibujo directo en mapa.json | aproximada (dilo) |

## A · PDF vectorial

```
python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.pdf [--pagina 0] [--cuadricula 1]
```

Lee los archivos de `salida/inspeccion/`:

- **`pagina.png`**: la hoja con una regla roja en puntos PDF.
- **`colores.json`**: cada relleno con su cantidad y tamaño típico.
  - Muchos rellenos iguales de 20–200 pt suelen ser los espacios.
  - Cientos de cuadritos de menos de 15 pt suelen ser las sillas.
- **`textos.json`**: códigos ("A05", "101", "P2-03") y rótulos de medida ("6x3").
- **`escala.json`**: pt/m por eje, medidos con FFT sobre la cuadrícula de fondo. Pueden diferir: hay PDF estirados.

**Escala**, en orden de preferencia:
1. Cuadrícula de fondo (FFT).
2. Cotas o medidas conocidas: escala = puntos ÷ metros.
3. Plano oficial del lugar.
4. Algo repetido de tamaño conocido: módulo de columnas, puerta de 0,9 m, puesto de parqueo de 2,5 × 5 m.

**Regiones**: una por cada piso o recuadro dibujado aparte o a otra escala. Pon las pequeñas primero; la principal va al final y sin `bbox_pt`.

```json
{ "id": "piso2", "nivel": "p2", "bbox_pt": [x0, y0, x1, y1], "escala_pt_m": [sx, sy],
  "origen_pt": [x, y], "origen_m": [X, Y], "rotacion": 0, "mover_m": [0, 0] }
```

Para apilar pisos, ancla cada región en un elemento que aparezca en todos: escaleras, ascensores, columnas, el vacío central.

**Reglas** por color de relleno:

```json
{ "tipo": "espacio", "relleno": [0.95, 0.62, 0.64], "tolerancia": 0.03, "area_min_pt": 40, "codigo": "^[A-Z]{1,3}[- ]?[0-9]" }
{ "tipo": "silla", "relleno": [0.69, 0.68, 0.68], "lado_max_pt": 15 }
{ "tipo": "zona", "relleno": [0.80, 0.90, 0.75], "material": "cesped" }
{ "tipo": "caja", "relleno": [0.11, 0.11, 0.11], "alto": 1.1, "material": "negro" }
```

En JSON escribe `[0-9]` en lugar de `\d`.

## B · CAD (DXF)

Si llega un DWG, conviértelo antes a DXF (ver `docs/ENTRADAS.md`).

```
python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.dxf
```

Revisa tres cosas:
- **La unidad** (`$INSUNITS`). Si sale "desconocida", pregunta si el dibujo está en mm, cm o m.
- **Las capas**: cuántas entidades y cuántas cerradas tiene cada una, y ejemplos de sus textos. Con eso se ve cuál es
  de muros, cuál de espacios, cuál de textos y cuál de mobiliario.
- **`dibujo.png`**, que lleva una regla azul en unidades del dibujo para leer el `bbox` de cada piso.

`plano.json` para CAD (ejemplo completo en `ejemplos/oficina-demo/plano.json`):

```json
{ "dxf": "entrada/plano.dxf", "unidad_m": 0.001,
  "regiones": [ { "id": "piso2", "nivel": "p2", "bbox": [39000, -3000, 71000, 21000], "origen_dibujo": [40000, 0],
                  "origen_m": [0, 0], "edificio": { "cubierta": false } } ],
  "reglas": [
    { "capa": "A-EDIFICIO", "tipo": "edificio", "altura": 3.6, "muro_bajo": 1.1, "fachada": "vidrio", "rotulo_piso": false },
    { "capa": "A-MUROS*", "tipo": "muro", "alto": 2.7, "grosor": 0.12 },
    { "capa": "A-ESPACIOS", "tipo": "espacio", "altura": 0.04, "capa_textos": "A-TEXTOS", "codigo": "^P[0-9]", "rotulo": "nombre" },
    { "capa": "A-MOBILIARIO", "tipo": "caja", "alto": 0.75, "material": "madera_clara" } ] }
```

- **Capas**: aceptan comodines (`A-MUROS*`).
- **Espacios**: toman como código el texto que está dentro de cada polilínea cerrada y que cumple el patrón `codigo`;
  el resto de los textos de adentro pasa a ser el nombre. Con `"rotulo": "nombre"`, en el piso se lee el nombre en vez del código.
- **Muros con doble línea** (lo normal en CAD): cada línea sale como un muro delgado. Usa `grosor` 0,05–0,08 para que
  las dos líneas formen la cara del muro. Si el dibujo trae los ejes de muro, usa esa capa con `grosor` real.
- **Pisos dibujados lado a lado**: una región por piso, cada una con su `origen_dibujo` llevado a `[0, 0]` para que queden apilados.
  El bloque `edificio` de la región ajusta solo ese piso; por ejemplo, la cubierta solo en el último.

## C · Imagen o escaneo

```
python pipeline/calibrar_imagen.py proyectos/<id>/entrada/plano.jpg
python pipeline/calibrar_imagen.py proyectos/<id>/entrada/plano.jpg --puntos x1,y1,x2,y2 --distancia 12.5 [--origen x,y]
```

1. La primera llamada genera `imagen_pixeles.png`. Úsala para leer dos puntos de medida conocida.
2. La segunda genera `imagen_metros.png`, con una cuadrícula en metros del mundo. Ábrela con Read y **lee las esquinas
   de edificios, muros y espacios directamente en metros** para escribirlas en `mapa.json`.
3. También imprime el bloque `calco`. Pégalo en `mapa.json` para ver la imagen bajo el modelo en los renders
   (`--calco`) y comprobar que todo coincide.

Si la imagen está torcida o en perspectiva (una foto), enderézala antes. Si no hay ninguna medida, pregunta por una:
el ancho de una puerta, un pasillo o un parqueadero.

## Revisión obligatoria (todos los caminos)

- `salida/plano_m.png` (o `imagen_metros.png`) comparado con el original, al lado. **Muéstraselo a la persona.**
- Validación de escala en PDF: "X de Y espacios rotulados coinciden (+/-12 %)". Si coincide menos del 90 %, la
  escala o la región están mal.
- "Fuera de toda región" debe dar 0, o un número que sepas explicar.
- "Sin código": revisa el patrón `codigo` o ponle el código a mano.
