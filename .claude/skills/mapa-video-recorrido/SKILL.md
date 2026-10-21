---
name: mapa-video-recorrido
description: Arma el video MP4 de recorrido del modelo 3D con Blender, por tramos de cámara con cortes entre ellos, con fotogramas reanudables y prueba previa de encuadre. Úsalo cuando la persona quiera un video para redes, una presentación o una pantalla del lugar.
---

# Video de recorrido

Script: `pipeline/renders.py` en modo video. Usa el mismo estilo de los renders (`--estilo=`), así que el video y las
láminas combinan.

## 1. Guion de cámara en mapa.json

```json
"recorrido": [
  { "nombre": "llegada",   "segundos": 5, "puntos": [[[120, -80, 60], [15, 10, 0]], [[60, -40, 25], [15, 10, 3]]] },
  { "nombre": "recepcion", "segundos": 6, "puntos": [[[5, -3, 1.7], [5, 6, 1.2]], [[8, 5, 1.7], [20, 6, 1]]] }
]
```

- Cada punto es `[posición de la cámara, punto al que mira]`, en metros del mundo. Para un interior, la z es la del
  piso más 1,7 m (altura de ojos).
- Dentro de un tramo la cámara se mueve suave; entre tramos hay **corte**. Usa un corte para pasar de afuera hacia
  adentro: que la cámara atraviese un muro se ve mal.
- Un orden que funciona: aérea de llegada → ingreso → espacios principales en el orden del recorrido → aérea de salida.
- Si no hay `recorrido`, el video es un giro de 360° alrededor del lugar.

## 2. Probar, renderizar y codificar

```
blender -b .../modelo.blend --python pipeline/renders.py -- .../mapa.json --video --prueba --estilo=realista
blender -b .../modelo.blend --python pipeline/renders.py -- .../mapa.json --video --estilo=realista
blender -b .../modelo.blend --python pipeline/renders.py -- .../mapa.json --codificar
```

1. **Prueba**: saca un fotograma por tramo (`salida/video_prueba_<tramo>.jpg`). Revísalos y muéstraselos a la persona
   antes de las horas de render.
2. **Render**: fotogramas 1920×1080 a 24 fps en `salida/video_frames/`. Es reanudable: si se corta, se vuelve a
   correr y sigue donde iba. Córrelo en segundo plano.
3. **Codificar**: arma `salida/recorrido.mp4` en H.264.

Unos 100 s de video son ~2.400 fotogramas, varias horas en EEVEE.

## Lecciones

- Dentro de espacios con stands o mobiliario, la cámara va a ~4 m y mira un poco hacia abajo; más bajo choca con todo.
- Tramos de 4–7 s: más cortos marean y más largos aburren.
- Música y textos se agregan después en un editor de video; el kit entrega la imagen limpia.
