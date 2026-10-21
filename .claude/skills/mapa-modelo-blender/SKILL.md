---
name: mapa-modelo-blender
description: Construye el modelo 3D del recinto en Blender (sin interfaz) desde recinto.json — pabellones con puertas y cubiertas, niveles que flotan, zonas, stands con código, tarimas con pantalla LED, sillas, carpas, árboles — y lo itera con la persona usando renders de vista previa. Úsalo en la fase 3 del mapa 3D o para corregir el modelo.
---

# Modelo 3D en Blender

Scripts: `pipeline/validar_recinto.py`, `pipeline/construir_modelo.py`. Formato completo: `docs/FORMATO-RECINTO.md`.

## 1. Escribir recinto.json

Parte de la plantilla de `nuevo_proyecto.py` o del demo (`ejemplos/demo-centro-eventos/recinto.json`).

- **niveles**: uno por piso que se quiera ver por separado.
  - `z`: altura del piso en metros (sótanos negativos).
  - `separacion`: cuánto sube ese nivel en el modo "Por niveles" (25–50 m según el tamaño). Solo para niveles que
    tapan a otro.
  - `bajo_techo: true`: para el nivel que queda **debajo** de otro. Sus pines se esconden en "Exterior" y, al tocarlos,
    el visor pasa solo a "Por niveles".
  - Ejemplo: Pabellón B piso 1 (`bajo_techo`) y piso 2 encima (`separacion: 26`).
- **edificios**: polígono en metros (antihorario o no, da igual), `altura`, `color` del pabellón (tiñe fachada y
  cubierta), `piso`, `puertas` (`lado` = índice del lado del polígono contado desde 0, `centro` y `ancho` en metros a lo
  largo de ese lado).
  - `cubierta: false` para un piso que tiene otro encima.
  - `muro_bajo`: alto del muro que se sigue viendo en "Por niveles" (3,2 m por defecto).
- **zonas**: plazas, jardines, agua, tapetes de color, áreas VIP. Polígono plano con `material` o color `[r, g, b]`.
- **stands**: a mano o desde el plano con `"stands_desde": "salida/plano_m.json"`.
- **objetos**: `tarima` (con `pantalla`), `pantalla`, `sillas` (área en cuadrícula), `sillas_puntos` (del plano),
  `carpa`, `arbol`, `caja`. `rot` en grados.
- **pines**: numerados en el orden en que el público recorre (1 = ingreso), con `color` del pabellón y `pos` = [x, y, alto
  sobre el piso del nivel].

## 2. Validar y construir

```
python pipeline/validar_recinto.py proyectos/<id>/recinto.json
blender -b --factory-startup --python pipeline/construir_modelo.py -- proyectos/<id>/recinto.json
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/recinto.json --preview
```

Lee los tres PNG de `salida/renders/` (iso, planta, niveles) y revisa antes de mostrarlos:
- **planta**: ¿coincide con el PDF? Los edificios no deben pisarse salvo donde un nivel va encima de otro.
- **niveles**: ¿lo de arriba flota exactamente sobre lo de abajo? ¿Se ve el interior?
- **iso**: ¿alturas razonables, puertas donde van, tarimas y pantallas mirando al público?

Luego muéstraselos a la persona y pide correcciones concretas.

## 3. Errores típicos (todos pasaron en Plaza Mayor)

- **Un piso dibujado "al lado" en vez de encima.** Va en el mismo polígono, en otro nivel, con `separacion`.
- **Pantalla o tarima de espaldas.** `rot` de la tarima: la pantalla queda al fondo y mira hacia `rot + 90°` (en
  grados, desde +X). Con `rot: 180` mira al sur.
- **Muro o cerramiento que tapa algo importante** (una vidriera, una tarima). Quítalo o usa una zona plana en vez de volumen.
- **Algo flotando o enterrado.** Revisa `z` del nivel y el `z` propio del objeto, que es relativo al nivel.
- **Medidas en conflicto entre fuentes.** No elijas tú: pregunta cuál manda y anótalo en el LEEME del proyecto.

## 4. Detalles que el constructor genérico no hace

Gradas, rampas, escaleras eléctricas, puentes, celosías, fachadas especiales, vehículos, personas. Escribe
`proyectos/<id>/detalles.py`, que se corre después de construir:

```
blender -b proyectos/<id>/salida/modelo.blend --python proyectos/<id>/detalles.py
```

El script abre el modelo, agrega mallas y guarda con `bpy.ops.wm.save_mainfile()`. Reglas para que el visor las entienda:
- cada objeto lleva `ob['grupo'] = '<nivel>'`, o `'techo_<nivel>'` si debe ocultarse en "Por niveles";
- si el nivel tiene `separacion`, el objeto se emparenta: `ob.parent = bpy.data.objects['RAIZ_<nivel>']`;
- se acumula geometría en pocas mallas (clase `MB` de `construir_modelo.py`): cada malla es una llamada de dibujo en el celular.

Catálogo de piezas ya resueltas para copiar (gradas, rampas, `escalera_electrica`, `truss`, `torre_luces`, `pantalla`,
carros, motos, personas, árboles, pórtico LED): `ejemplos/plaza-mayor/fuente-original/construir_mapa_v04.py`.
En ese proyecto la v04 la generaba `generador/make_v04.py` con parches sobre la v03. Funciona, pero para un proyecto
nuevo es más simple editar directo.

## 5. Texturas y materiales

Todo es procedural (`generar_texturas.py`), sin derechos de terceros. Para usar el arte real del evento en las
pantallas, reemplaza `texturas/led_*.jpg` por imágenes con la misma proporción y reconstruye. Los materiales
disponibles están en `CATALOGO` dentro de `construir_modelo.py`; para uno nuevo, agrega la textura en
`generar_texturas.py` y una línea en `CATALOGO`.
