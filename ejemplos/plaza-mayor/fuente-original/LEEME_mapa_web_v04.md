# Mapa web 3D y video · Feria Effix 2026 (v04)

## Qué hay
- `web/`: mapa 3D navegable (HTML + three.js). Archivos: `index.html`, `estilos.css`, `app.js`, `mapa.glb` (modelo, 6,5 MB) y `datos.json` (pines y niveles).
- `renders_v04/`: renders con acabados nuevos y, cuando termine, `recorrido_effix_2026.mp4`.
- `texturas/`: texturas generadas por `generar_texturas.py` (no son fotos de terceros).

## Regenerar
```
python generar_texturas.py
blender -b --factory-startup --python construir_mapa_v04.py
blender -b Plaza_Mayor_mapa_v04.blend --python exportar_web.py
blender -b Plaza_Mayor_mapa_v04.blend --python video_recorrido.py                  # fotogramas (reanudable)
blender -b Plaza_Mayor_mapa_v04.blend --python video_recorrido.py -- --codificar   # MP4
```
`construir_mapa_v04.py` se genera desde la v03 con un script de parches; para cambios de fondo conviene editar la v04 directamente.

## Ver el mapa web en este computador
```
python -m http.server 5173 --directory web
```
y abrir http://localhost:5173

## Cómo funciona el mapa web
- Arrastrar gira, rueda o pellizco acerca, dos dedos o clic derecho desplaza.
- **Exterior**: todo en su sitio, con cubiertas. **Por niveles**: quita cubiertas y separa los niveles (Azul y Verde sobre Rojo y Comunidades; Caja sobre Multipropósito sobre Gran Salón).
- Los pines numerados y la lista llevan la cámara a cada lugar. Si el lugar está bajo otro nivel, cambia solo a "Por niveles".
- Botones: vista inicial, recorrido automático (giro) y vista desde arriba.
- three.js se carga desde el CDN jsdelivr (necesita internet).

## Acabados tomados del recorrido 360 oficial (solo como referencia visual)
Fuente: recorrido de Real Vision 360 para Plaza Mayor. No se copiaron sus imágenes.
- Plazas en losas de piedra gris cálida con franjas de adoquín oscuro.
- Celosía de la Caja en tono bronce oscuro.
- Fachadas de pabellones en vidrio y panel gris; el color de cada pabellón queda en cubierta, cornisa y zócalo.
- Jardín de bambú al oriente de la Caja y edificio de servicios con paneles solares sobre la Av. Ferrocarril.

## Recorrido 360 oficial: las 27 escenas revisadas
Plano oficial de Plaza Mayor (incluido en el recorrido) con medidas que confirman la extracción del PDF técnico:
Azul 41,6 × 59,8 m (h 4,7) · Rojo 41,6 × 52,7 m (h 4,5) · Amarillo 41 × 117,2 m (h 10,7) · Blanco 33,73 × 87,41 m (h 10,05) ·
Verde 40,95 × 70 m (h 13,3) · Gran Salón 36,1 × 62,1 m (h 6,9) · Caja de Madera 31,25 × 36,46 m (h 11) · Plazoleta Descubierta 51 × 49 m.
Alturas aplicadas en la v04. El Blanco del modelo mide 96 m: los últimos 8,6 m del PDF técnico probablemente son servicios/enfermería, no pabellón.

Materiales interiores vistos y aplicados: concreto pulido en los pabellones (cerchas blancas en Blanco y Verde, negras en Amarillo;
zócalos amarillos en el Amarillo; techo bajo con ductos en el Rojo), piedra pulida gris verdosa en lobbies, Hall y Caja (interior con
cielo de madera, celosía visible y un volumen amarillo de circulaciones), alfombra gris azulada y muros de madera clara en el Gran Salón
(cielo negro con paneles acústicos de colores), alfombra y muros blancos/piedra en Comisiones y salas.

Zona Black (uso exclusivo según el usuario): Comisiones 5+6, 7 y 11, Sala de Negocios, Sala de Prensa y Sala VIP, en el edificio de
Convenciones, piso 1. Pin 22. Su posición exacta dentro del edificio no está acotada; se ubicó en el costado oriental del lobby, donde el
PDF técnico rotula "Zona Black".

## Fotomontaje de Effix (fotomontaje-feria-effix.netlify.app), revisado
- `tapetes.html`: los 22 tapetes del archivo "Tapete Feria EFFIX a cotizar" con coordenadas en el plano técnico. Guardados en `tapetes_effix.json`
  y pintados en el modelo con su color real (Convermate gris, YouTube rojo, Vitalcom verde billar, Unmerco verde, Zona Black negro,
  VIP rojo, Effix azul, Marketing morado, UGC césped sintético). Los académicos quedan dentro de los stands y no se dibujan.
- `visor` y `maqueta`: montaje de la Plazoleta Interamericana. Aplicado: pabellón UGC en trimalla 18 × 25 m con 6 patas y ecopesos,
  lado largo norte-sur (pedido del usuario), cerramiento perimetral en malla de 2 m, 3 torres de luces, 25 mesas de coctel y tótem del
  punto de encuentro. Pendiente: Pancake Plaza (letras y rompetráficos), 9 motos, y revisar que las sillas del plano (bloque de 21 m
  de ancho E-O) caben bajo el pabellón de 18 m; el tapete de césped del archivo mide 25 m en sentido E-O y 20 m N-S.
- El Pabellón Blanco se deja en 96 m (decisión del usuario).

## Correcciones del 2 de octubre (tarde)
- Cerramiento de la plazoleta: ya no cruza las graderías; termina en su borde oriental (X 36) y occidental (X -30).
- Dos ingresos con escarapela sobre el cerramiento, donde el PDF técnico marca "Ingreso techo truss 8×4": occidente (-30, 125) y oriente (84, 120). Pines 20 y 21.
- Fachada del Gran Salón hacia las graderías (fotos 360): zócalo de piedra con franja de vidrio (piso 2), vidriera con puertas al lobby (piso 1), pilares cada 7,2 m, avisos.
- Placa del Multipropósito recortada a la línea de fachada (Y ≥ 168,4).
- Exhibición: los 10 íconos de 28×14 pt del PDF son las MOTOS (línea diagonal, X 39–60); los carros son 11 íconos rojos vectoriales en dos filas,
  parqueados de lado con 2,8 m entre ejes, eje largo a -63° (fila) y -40° (Autoshow). Se modelaron como deportivos de lujo con rines cromados y motos con tanque, motor y manubrio.
- Cámaras nuevas de revisión: `maqueta_fachada_gs`, `maqueta_carros`.

## Fachada de Convenciones hacia las graderías (fotos 360 del usuario, 2 oct noche)
- Gran Salón sigue a −9 m (confirmado por el usuario: se bajan varias escaleras).
- Las gradas terminan en Y 162,8; de ahí a la vidriera va la explanada del acceso con los stands PL17–PL24 (como en el plano).
- Piso 1: porche con pilares redondos cada 7,2 m, vidriera retranqueada 2,6 m con tres puertas, piso de piedra.
- Piso 2 (Multipropósito): balcón corrido con antepecho y baranda, ventanales altos, pantalla LED, volumen de persianas de madera al occidente, letrero.
- Muros laterales de piedra de las gradas, pasamanos de acero, tótem negro de señalización.
- El muro bajo del Gran Salón ya no se dibuja en el frente (tapaba la vidriera).
- Vistas de revisión: `maqueta_fachada_gs` (desde el descanso de las gradas) y `detalle_gran_salon` (planta del lobby, mismo encuadre que el plano).
- PL17 y PL18 (al pie de las gradas, frente al acceso) van como marcación a piso, no como volumen: tapaban la fachada.
- Estructuras flotantes de la plazoleta: dos bandas curvas que nacen en el ingreso occidental, se abren al sur y al norte y se juntan en el oriental (digitalizadas del plano técnico).

## Fichas técnicas Livesound (Render aprobado, 13/04/2026) aplicadas
- **Tarimas:** principal 60 cm de alto con faldón negro; secundarias 90–100 cm. Pantalla LED central centrada al fondo: 15 × 4 m
  (Verde, Gran Salón, Amarillo), 10 × 3 m (UGC y tarimas de 11–18 m), 6 × 2,5 m en las chicas. Torres de truss con 4 cabezas móviles
  en las esquinas del fondo; pantallas laterales 16:9 colgadas a media sala en Verde y Gran Salón.
- **UGC (plazoleta):** tarima de la ficha, 12,2 × 3,7 m, 1,0 m de alto, pantalla 10 × 3 mirando al oriente. La cubierta se dejó en
  trimalla por decisión del usuario (el render Livesound muestra carpa a dos aguas).
- **Ingreso principal (Caja de Madera):** pórtico LED de 10,2 × 5,1 m, vano de 6 m, patas 1,5 × 2,1 forradas en LED, banda superior
  10 × 2 por ambas caras. Frente hacia la plaza norte.
- **Contenido de las pantallas:** texturas procedurales `led_*.jpg` (anillos violeta/magenta con figura central, estilo del render).
  Para usar el arte real de Effix basta reemplazar esos archivos en `texturas/` y regenerar.
- Vistas de revisión: `maqueta_portico`, `mapa_verde_tarima`.

## Integración en la app (app.feriaeffix.com)
- Rama `feat/mapa-3d` del repo de la app: `src/components/mapa/Mapa3D.tsx`, `src/lib/mapa3d.ts`, `public/mapa3d/` (modelo, datos, Draco).
- `exportar_stands_app.py` genera `public/mapa3d/datos.json` con los pines y los 238 stands del plano (posición 3D + código normalizado).
- La página `/mapa` cruza esos stands con `stands_publico` por código (A 05 ↔ A05, BL 02 A ↔ B02A) para mostrar empresa y logo.
- Gran Salón: el muro de madera del fondo de la sala se extiende hasta Y 269,5 para que la tarima (Y 261–268,5 en el PDF) quede adentro.
- UGC: tarima Livesound 12,2 × 3,7 en el extremo norte de la carpa (Y 145,9–149,6, centrada en X −1,7), pantalla 10 × 3 hacia el sur, como en el fotomontaje aprobado.
