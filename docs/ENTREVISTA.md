# Entrevista para montar un mapa 3D

Estas son las preguntas que el agente le hace a la persona. Van en orden: primero lo que bloquea, después lo que se
afina viendo el modelo. Haz una pregunta a la vez cuando la respuesta cambia el modelo, y agrupa las menores.

## 1. Arranque (imprescindible)

- **¿Qué lugar es?** Oficina, casa, edificio, campus, centro comercial, hotel, hospital, colegio, parque, recinto de
  eventos… y dónde queda.
- **¿Para qué lo quieres?** Puedes elegir varias:
  - **Renders y láminas** para presentar, vender, imprimir o publicar en redes.
  - **Mapa web 3D** para que el público se ubique desde el celular.
  - **Video de recorrido.**
- **¿En qué formato está el plano?**
  - DWG o DXF de CAD (lo mejor);
  - PDF exportado de CAD o de un programa de diseño;
  - imagen, foto o escaneo;
  - croquis a mano.
  Si lo tiene, pide el archivo original, no una captura.
- **¿Qué medida conoces?** Solo hace falta si no es CAD. Puede ser una cota, el largo de una fachada, el ancho de una
  puerta o de un pasillo, o "cada cuadro del plano es 1 m".
- **¿Qué significa terminado?** Una línea. Ejemplo: "lámina A3 de los 3 pisos en estilo ilustrado y el mapa web con
  las 24 salas buscables".

## 2. Estructura y pisos (lo que más correcciones genera)

- ¿Cuántos edificios hay y cuántos pisos tiene cada uno? ¿Cómo se llaman?
- **¿Algún piso o edificio queda encima de otro?** ¿Cuál sobre cuál? Si el plano dibuja los pisos uno al lado del
  otro, ¿qué elemento se repite en todos (escaleras, ascensor, columnas) para alinearlos?
- ¿Hay sótanos, mezanines o terrazas?
- ¿A qué nivel queda la calle o el ingreso principal?
- ¿Cómo se sube de un piso a otro? Escaleras, ascensores, rampas, escaleras eléctricas.

## 3. Medidas y alturas

- Altura de cada piso, o fotos para estimarla. Valores típicos:
  - vivienda: 2,5–3 m;
  - oficina: 3,5–4 m;
  - pabellones y bodegas: 6–12 m.
- Si dos fuentes no coinciden, **¿cuál manda?**
- ¿Hay un plano oficial, un recorrido 360 o fotos de fachadas? Sirven para validar y para elegir materiales
  (solo como referencia, sin copiar imágenes).

## 4. Qué marcar

- **Lugares con pin**: ingreso, recepción, salas importantes, baños, cafetería, parqueadero, punto de encuentro…
  - Van en el orden en que alguien recorre el lugar (1 = ingreso).
  - Para cada uno, un nombre corto y un detalle de una línea.
- **Espacios buscables**:
  - ¿Cómo se llaman en este lugar? Salas, oficinas, locales, stands, habitaciones, lotes, consultorios.
  - ¿Tienen código (101, A-05, P2-03)?
  - ¿Hay una lista con el nombre de cada código?
- **Mobiliario que importa mostrar**: escritorios, mesas, sillas de un auditorio, tarimas, pantallas.

## 5. Marca y estilo

- Título y subtítulo de las láminas y del mapa web.
- Color principal en hex, o un ejemplo de su marca. Logo en PNG o SVG.
- Estilo de render. Muéstrale los cuatro: realista, maqueta blanca, ilustrado y noche (`docs/img/estilos.jpg`).
- Si va a imprenta, el tamaño: A3, A2 o A1.

## 6. Publicación

- ¿Dónde va el mapa web? En un link propio (Vercel o Netlify), dentro de su página web (iframe) o dentro de una app.
- ¿Quién aprueba antes de publicar?
- Para "Mi ubicación" por GPS: ¿alguien puede ir al lugar a medir 6–10 esquinas con el celular?

## Cómo pedir correcciones

Pídele que marque sobre el render: rojo para lo que sobra o está mal, azul para lo que falta, y una flecha hacia
donde va. Es mucho más rápido que describirlo con palabras.
