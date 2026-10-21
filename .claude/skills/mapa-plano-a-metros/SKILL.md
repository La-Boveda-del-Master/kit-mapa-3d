---
name: mapa-plano-a-metros
description: Convierte el plano PDF de un recinto a metros reales. Inspecciona el PDF (colores, textos, cuadrícula), calibra la escala por FFT o por medidas conocidas, define regiones (zonas dibujadas aparte o en otra escala) y extrae stands con su código, sillas y zonas a plano_m.json. Úsalo en la fase 2 del mapa 3D o cuando la escala o la posición de algo no cuadre.
---

# Del plano PDF a metros

Script: `pipeline/extraer_plano.py`. Config: `proyectos/<id>/plano.json` (formato en `docs/FORMATO-RECINTO.md`).

## 1. Inspeccionar

```
python pipeline/extraer_plano.py inspeccionar proyectos/<id>/entrada/plano.pdf [--pagina 0] [--cuadricula 1]
```

Mira los archivos de `salida/inspeccion/`:
- `pagina.png`: la hoja con una regla roja en **puntos PDF** en los bordes. Ábrela con Read para ver el plano y leer
  coordenadas aproximadas de cada zona.
- `colores.json`: cada color de relleno, cuántas veces aparece y su tamaño típico. Los stands suelen ser un color con
  muchas apariciones de 20–200 pt; las sillas, un color con cientos de cuadritos < 15 pt.
- `textos.json`: palabras con posición. Busca los códigos de stand (A01, BL-12…) y rótulos de medida ("6x3").
- `escala.json`: si el PDF trae la cuadrícula de fondo como imagen, aquí sale la escala en pt/m **por eje**
  (pueden diferir: el PDF de Plaza Mayor venía estirado, 9,25 pt/m en X y 9,76 en Y).

Pregúntale a la persona cuánto mide un cuadro de la cuadrícula (en Plaza Mayor: 1 m) y pásalo con `--cuadricula`.

## 2. Calibrar la escala

En orden de preferencia:
1. **Cuadrícula de fondo** (FFT en `escala.json`).
2. **Cotas o medidas conocidas**: un pabellón de 41,6 m, un stand rotulado 18x8, la modulación de columnas (7,2 m).
   Escala = puntos medidos ÷ metros.
3. **Plano oficial del recinto** (web, recorrido 360, ficha técnica): compara 3–4 edificios; error aceptable < 1 %.

Si una zona no tiene cuadrícula, dedúcela de algo repetido que sí conozcas (columnas, escaleras, tarimas).

## 3. Regiones

Los planos de ferias dibujan pisos y salones **aparte**, a otra escala, o "al lado" de donde van. Cada uno es una
región con su propia transformación:

```json
{ "id": "gran_salon", "nivel": "sotano", "bbox_pt": [2819, 864, 3817, 1521],
  "escala_pt_m": [8.57, 8.985], "origen_pt": [3349, 1970], "origen_m": [10.8, 195.8], "rotacion": 0 }
```

- `bbox_pt`: rectángulo de la hoja que pertenece a la región. **Pon las regiones pequeñas primero** (gana la primera
  que contiene el punto) y la principal al final sin `bbox_pt`.
- `origen_pt` ↔ `origen_m`: un punto que reconoces en el PDF y dónde va en el mundo. Para reubicar un piso que va
  **encima** de otro, usa un elemento que aparezca en ambos planos (escaleras eléctricas, vacío central, columnas):
  en Plaza Mayor la Caja de Madera y el Multipropósito se alinearon sobre el Gran Salón con < 1 m de diferencia.
- `rotacion`: grados antihorario si la hoja no tiene el norte arriba (en Plaza Mayor la página iba con el norte a la derecha).
- `mover_m`: desplazamiento extra en metros, para ajustes finos sin recalcular el origen.

## 4. Reglas y extracción

```json
{ "tipo": "stand", "relleno": [0.95, 0.62, 0.64], "tolerancia": 0.03, "area_min_pt": 40, "codigo": "^[A-Z]{1,3}[- ]?[0-9]" }
{ "tipo": "silla", "relleno": [0.69, 0.68, 0.68], "lado_max_pt": 15 }
{ "tipo": "zona",  "relleno": [0.80, 0.90, 0.75], "material": "cesped" }
{ "tipo": "caja",  "relleno": [0.11, 0.11, 0.11], "alto": 1.1, "material": "negro" }
```

En JSON escribe `[0-9]` en vez de `\d` (la barra invertida rompe el JSON).

```
python pipeline/extraer_plano.py extraer proyectos/<id>/plano.json
```

Revisa la salida:
- **Validación**: "X de Y stands rotulados coinciden (+/-12 %)". Menos del 90 % → escala o región mal.
- **"dibujos fuera de toda región"**: elementos que no cayeron en ninguna; amplía un `bbox_pt` o agrega región.
- **"sin código"**: stands cuyo código no está dentro del rectángulo (a veces el texto está al lado): ajústalo a mano
  en `recinto.json` o cambia el patrón `codigo`.
- **`salida/plano_m.png`**: dibujo en metros con cuadrícula de 10 m y norte arriba. **Muéstraselo a la persona** y compáralo
  con el PDF antes de seguir.

## 5. Lo que no sale solo

Los contornos de edificios rara vez son un relleno limpio. Lo práctico: medir en `pagina.png` / `textos.json` sus
esquinas y escribir los polígonos a mano en `recinto.json`, ya en metros (usa la misma transformación de la región:
`x_m = origen_m.x + (x_pt - origen_pt.x)/escala_x`, `y_m = origen_m.y - (y_pt - origen_pt.y)/escala_y`, sin rotación).
Si el PDF no es vectorial (escaneo), calibra con dos puntos de medida conocida y dibuja todo a mano: es más lento pero funciona.

Referencia real con 6 regiones, sillas, tarimas, mesas y catenarias: `ejemplos/plaza-mayor/fuente-original/extraer_plano_v03.py`.
