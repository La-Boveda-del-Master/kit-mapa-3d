---
name: mapa-modelo-blender
description: Construye el modelo 3D en Blender (sin interfaz) a partir de mapa.json. Incluye edificios con fachada, ventanas y cubierta; pisos apilados que flotan en "Por niveles"; muros interiores con puertas; espacios rotulados (salas, locales, stands); escaleras, mobiliario, tarimas con pantalla, sillas, carpas, árboles y zonas. Después lo itera con la persona a partir de renders de vista previa. Úsalo en la fase 3 o para corregir el modelo.
---

# Modelo 3D en Blender

Scripts: `pipeline/validar_mapa.py` y `pipeline/construir_modelo.py`. El formato completo está en `docs/FORMATO-MAPA.md`.
Hay dos ejemplos probados para copiar: `ejemplos/campus-demo/mapa.json` (exteriores) y `ejemplos/oficina-demo/mapa.json` (pisos).

## 1. Escribir mapa.json

- **marca**: `titulo`, `subtitulo`, `nota` (lo aproximado), `color` (hex, el acento del visor y de las láminas), `logo`
  (archivo en `entrada/`) y las etiquetas `etiqueta_lugares` y `etiqueta_espacios` ("Salas", "Locales", "Stands", "Oficinas", "Lotes").
- **niveles**: uno por piso que se quiera ver por separado.
  - `z`: altura del piso; los sótanos van en negativo.
  - `separacion`: los metros que sube el nivel en "Por niveles".
  - `bajo_techo: true`: para los pisos que otro tapa.
  - En un edificio de N pisos todos los de abajo llevan `bajo_techo` y desde el segundo todos llevan `separacion`
    creciente (11, 22, 33… para pisos de 3,6 m).
- **edificios**: el contorno de cada edificio, una vez por piso si hay varios.
  - `poligono` y `altura` (del piso al techo de ese nivel).
  - `color` (tiñe fachada y cubierta) y `fachada` (`vidrio`, `ladrillo`, `madera`, `arenisca_muro`…).
  - `piso`: el material del suelo.
  - `puertas`: `lado` es el índice del lado (desde 0); `centro` y `ancho` van en metros.
  - `cubierta`: `false` en los pisos que tienen otro encima.
  - `muro_bajo`: lo que se sigue viendo en "Por niveles". Usa 1,1 m para pisos con interiores y 3,2 m para pabellones.
  - `rotulo_piso: false`: cuando los espacios ya rotulan el interior.
- **muros**: tabiques interiores o cerramientos. `puntos` (polilínea), `alto`, `grosor`, `cerrado`, `puertas` (por `tramo`).
- **espacios**: lo que se busca en el visor.
  - Campos: `codigo`, `nombre`, `detalle`, `categoria` y `poligono`.
  - `altura`: 2,4 m para un stand o bloque; 0,04 m para una sala o área pintada en el piso.
  - `color` y `rotulo`.
  - Los planos se apoyan solos sobre la losa.
- **zonas**: plazas, jardines, agua, parqueaderos, tapetes, áreas VIP, con `material` o color y `rotulo`.
- **objetos**: `escalera` (`desde`, `hasta`, `sube`, `ancho`), `mesas`, `sillas`, `tarima` (con `pantalla`), `pantalla`,
  `carpa`, `arbol` y `caja` (mostradores, equipos, bloques).
- **pines** (lugares): numerados en el orden en que se recorre el sitio. Llevan `color` por zona o piso y
  `pos` = [x, y, altura sobre el piso del nivel].
- **calco** (opcional): la imagen del plano bajo el modelo, para revisar.

## 2. Validar, construir y mirar

```
python pipeline/validar_mapa.py proyectos/<id>/mapa.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- proyectos/<id>/mapa.json
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/mapa.json --preview --vistas=axo,planta,niveles
```

Lee los PNG y revisa con ojo de director de arte antes de mostrarlos:
- **planta**: coincide con el plano original. Agrega `--calco` si hay imagen para superponer.
- **niveles**: cada piso flota exactamente sobre el de abajo; se leen los nombres de los espacios; no hay muros que
  atraviesen salas ni puertas tapadas.
- **axo**: alturas creíbles, fachadas con ventanas y cubiertas cerradas; pantallas y tarimas orientadas hacia el público.
- **Textos**: ninguno se sale de su espacio ni queda debajo de una losa. Para ajustar, usa `tam_rotulo` y `rot_rotulo`,
  o un `rotulo` más corto.

## 3. Calidad del modelo (lo que lo hace ver profesional)

- **Escala humana**: puertas de ~0,9–1,2 m, mesas, sillas, árboles y escaleras. Sin ellos, el modelo parece una maqueta de cartón.
- **Jerarquía de color**:
  - un color por edificio o zona, en tonos medios;
  - neutros en pisos y muros;
  - acentos saturados solo en lo importante.
- **Entorno sobrio**: vías, andenes, jardín y un margen de terreno (`terreno.margen`) que no compita con el edificio.
- **Nada flotando ni enterrado**: cada objeto lleva el `nivel` correcto, y su `z` es relativa al piso de ese nivel.
- **Peso**: si el modelo va a la web, evita miles de sillas que nadie va a ver. Mide los triángulos con la salida del exportador.

## 4. Lo que el constructor genérico no hace

Gradas, rampas, escaleras eléctricas, puentes, celosías, cubiertas curvas, fachadas especiales. Para eso escribe
`proyectos/<id>/detalles.py` y córrelo después de construir:
`blender -b proyectos/<id>/salida/modelo.blend --python proyectos/<id>/detalles.py`.

El script agrega mallas y guarda con `bpy.ops.wm.save_mainfile()`. Tres reglas:
- `ob['grupo'] = '<nivel>'`, o `'techo_<nivel>'` si debe ocultarse en "Por niveles";
- si el nivel tiene `separacion`, `ob.parent = bpy.data.objects['RAIZ_<nivel>']`;
- acumula geometría en pocas mallas (clase `MB` de `construir_modelo.py`).

Hay un catálogo de piezas resueltas en `ejemplos/caso-origen-plaza-mayor/fuente-original/construir_mapa_v04.py`:
gradas, rampas, `escalera_electrica`, truss, torres de luces, pórtico LED, vehículos, personas.

## 5. Materiales y texturas

Son procedurales (`generar_texturas.py`) y no tienen derechos de terceros. El catálogo disponible está en `CATALOGO`
dentro de `construir_modelo.py`; también sirve un color `[r, g, b]`. Para el arte real en las pantallas, reemplaza
`texturas/led_*.jpg` por imágenes de la misma proporción y reconstruye el modelo.
