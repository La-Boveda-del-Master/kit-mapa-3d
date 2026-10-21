---
name: mapa-renders-video
description: Saca renders fijos del modelo 3D (isométrico exterior, planta norte arriba, niveles separados) para revisar, presentar o imprimir, y arma el video de recorrido por tramos con Blender. Úsalo para mostrar avances a la persona, para piezas de comunicación del evento o para un video de recorrido.
---

# Renders y video de recorrido

Script: `pipeline/renders.py` (EEVEE, sin interfaz).

## Renders fijos

```
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/recinto.json --preview
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/recinto.json --vistas=iso,planta,niveles
```

- `--preview`: mitad de resolución y 16 muestras, en segundos. Úsalo en cada vuelta de corrección.
- Sin `--preview`: 2400×1600 y 64 muestras, para entregar.
- Salen en `salida/renders/<vista>.png`. Léelos con Read antes de mostrarlos y envíalos con SendUserFile.

Para impresión grande (pliego 100×70 cm), sube la resolución en `render()` (por ejemplo 7000×4900) y usa la vista
`planta` u `iso`. La leyenda de pines numerados se compone aparte con PIL: ver
`ejemplos/plaza-mayor/fuente-original/componer_leyenda.py`.

Si quieres cámaras con encuadre propio (una fachada, un auditorio por dentro), agrega una vista en `renders.py` con
`camara('Cam_X', posición, mira, lente)`. Las coordenadas están en metros del mundo; los interiores de un nivel van a
z del nivel + 1,7 m (altura de ojos).

## Video de recorrido

1. Define los tramos en `recinto.json`. Si no hay tramos, el video es un giro de 360°:

```json
"recorrido": [
  { "nombre": "panoramica", "segundos": 5, "puntos": [[[330, 150, 190], [0, 95, 0]], [[190, 290, 110], [10, 200, 5]]] },
  { "nombre": "registro",   "segundos": 6, "puntos": [[[12, 216, 1.7], [12, 190, 1]], [[13, 196, 1.7], [8, 180, 0]]] }
]
```

   Cada punto es `[posición de cámara, punto al que mira]`. Dentro de un tramo la cámara se mueve suave; entre tramos
   hay corte.

2. Prueba un fotograma por tramo (640×360) y revisa el encuadre:

```
blender -b .../modelo.blend --python pipeline/renders.py -- .../recinto.json --video --prueba
```

3. Render completo (reanudable: si se corta, vuelve a correrlo y sigue donde iba):

```
blender -b .../modelo.blend --python pipeline/renders.py -- .../recinto.json --video
blender -b .../modelo.blend --python pipeline/renders.py -- .../recinto.json --codificar
```

   Sale `salida/recorrido.mp4` (1280×720, 24 fps, H.264). Un recorrido de ~100 s son ~2.400 fotogramas, unas 3 horas.
   Córrelo en segundo plano.

## Lecciones

- Dentro de pabellones con stands, la cámara va a ~4 m: por encima de los stands (~3 m) y mirando un poco hacia abajo.
  Más abajo choca con ellos.
- Para pasar de afuera hacia adentro, usa un corte entre tramos. Que la cámara atraviese un muro se ve mal.
- Blender no sobrescribe un PNG que esté abierto en un visor de imágenes de Windows: cierra el visor o cambia el nombre.
