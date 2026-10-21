# Entrevista para montar el mapa de un recinto

Preguntas que el agente le hace a la persona. Están en el orden en que conviene hacerlas: primero lo que bloquea,
después lo que se puede afinar viendo el modelo. Salieron de las ~100 rondas de corrección del mapa de Plaza Mayor.

## 1. Arranque (imprescindible)

- **¿Qué recinto y qué evento?** Nombre, ciudad, fechas. Van como título y subtítulo del visor.
- **¿Para qué lo quieres?** Página web suelta, dentro de una app, video, impresión. Puede ser varias cosas.
- **¿Tienes el plano en PDF?** Ideal: el técnico del montaje, vectorial (que al hacer zoom no se pixele). Si hay dos
  (técnico y comercial con los códigos de stand), pide los dos.
- **¿Cuánto mide la cuadrícula del plano, o qué medida conoces?** Por ejemplo "cada cuadro es 1 m", "el pabellón
  mide 41,6 m" o "el stand A1 es de 6x3".
- **¿Qué significa terminado?** Una línea. Ejemplo: "link que abre en el celular con los 6 pabellones, los stands
  buscables y 12 pines".

## 2. Estructura y niveles (lo que más correcciones genera)

- ¿Qué edificios, pabellones o salones hay? ¿Cómo se llama cada uno y de qué color lo identifican?
- **¿Algún pabellón está encima de otro?** ¿Cuál sobre cuál? En el mapa, el de arriba flota sobre el de abajo.
- ¿Hay sótanos o salones por debajo del nivel de la calle? ¿Cuántos metros?
- ¿Hay terrazas o mezanines a media altura?
- ¿A qué nivel queda la calle o el ingreso principal?
- ¿El plano dibuja algún piso "aparte" (en un recuadro, a otra escala)? ¿Dónde va en realidad?
- ¿Cómo se pasa de un nivel a otro? Gradas, rampas, escaleras eléctricas, puentes.

## 3. Medidas y alturas

- Altura aproximada de cada pabellón. Sirven fotos o "como un edificio de 3 pisos".
- Si dos fuentes no coinciden (por ejemplo, el PDF dice 96 m y el plano oficial 87 m), **¿cuál manda?**
- ¿Hay un plano oficial del recinto, un recorrido 360 o una ficha técnica pública? Sirven para validar medidas y
  acabados (solo como referencia; no se copian sus imágenes).

## 4. Qué marcar

- **Lugares con pin**, en el orden en que el público los recorre (1 = ingreso). Ejemplos: ingreso, taquillas o
  registro, auditorios, zonas especiales, baños, comidas, parqueadero, punto de encuentro.
- Para cada pin: nombre corto y detalle de una línea (aforo, qué pasa ahí).
- **Stands**: ¿se buscan por código? ¿Hay una lista o base de datos con el nombre de la empresa y su logo por código?
- Zonas especiales: VIP, prensa, tapetes de color, carpas, tarimas (con medidas de tarima y pantalla si las hay).

## 5. Acabados (después del primer render)

- Fotos de fachadas, pisos y plazas, para elegir materiales del catálogo.
- Orientación de tarimas y pantallas: ¿hacia dónde mira el público?
- Tipo de cubierta de carpas y estructuras.
- Arte para las pantallas LED (opcional; por defecto van con contenido genérico).

## 6. Publicación

- ¿Dónde se publica? ¿Hay un dominio? ¿Vercel, Netlify, la web del evento, una app?
- ¿Quién aprueba antes de publicar?
- Para GPS "Mi ubicación": ¿alguien puede ir al recinto a medir 6–10 esquinas con el celular?

## Cómo pedir correcciones

Pídele a la persona que marque sobre el render o la captura: rojo = sobra o está mal, azul = falta, y una
flecha hacia dónde va. Es mucho más rápido que describirlo con palabras.
