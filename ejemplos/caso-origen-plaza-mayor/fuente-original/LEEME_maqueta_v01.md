# Maqueta Plaza Mayor v01

Base de estudio editable; no es todavia un mapa aprobado para visitantes.

## Archivos
- Plaza_Mayor_maqueta_v01.blend: escena 01 con implantacion provisional; escena 02 con contornos del PDF en sus posiciones originales de pagina.
- medidas_pdf_v01.json: vertices, cajas envolventes y procedencia de las medidas.
- extraer_plano.py y construir_maqueta.py: reproduccion del trabajo.
- maqueta_v01.png: vista de estudio, sin acabado ilustrado.

## Escala
Se usa 1 unidad Blender = 1 metro como referencia de modelado. La impresion se reduce mediante encuadre en un pliego de 100 x 70 cm. No significa impresion a tamano real.
La conversion preliminar es 10.085 puntos del PDF por metro, deducida de modulos vectoriales repetidos y cotejada con stands acotados. El borde de trazo agrega pequenas diferencias. Falta aislar y contar visualmente la cuadricula de fondo indicada por el usuario; no se considera calibracion topografica definitiva.

## Medidas derivadas del dibujo
Son envolventes de zonas dibujadas, no certificados de dimension del edificio.
- Blanco: 95.50 x 35.72 m.
- Azul: envolvente 42.92 x 63.42 m; contorno irregular conservado en escena 02.
- Rojo: envolvente 42.92 x 57.65 m.
- Amarillo: dos zonas contiguas de 49.76 y 69.47 m por aproximadamente 44.32 m.
- Verde: poligono inclinado extraido; su envolvente de pagina NO equivale al largo/ancho del edificio.
- Gran Salon: poligono irregular, envolvente 71.87 x 39.11 m.
- Recuadro de tercer piso / Caja de Madera: 43.01 x 40.18 m.

## Pendientes importantes
- Los recuadros de pisos no son distancias geograficas. La escena 02 es una extraccion de la hoja, no un plano de implantacion.
- La escena 01 contiene alturas, separaciones, vias, estacion, teatro, escaleras y rampas aproximadas basadas en referencias. No se han medido en campo.
- Caja de Madera toma provisionalmente la envolvente del Gran Salon para estudiar su separacion visual; no esta validado y difiere del recuadro del tercer piso.
- Butacas y vehiculos son simbolos de estudio, no aforos ni distribuciones verificadas.
- Azul y Caja de Madera usan separacion vertical expositiva, no altura real.
- Falta reconciliar entrada principal rotulada en tercer piso del PDF con acceso por nivel inferior indicado por el usuario.
- Falta ajustar toda la implantacion con referencias por nivel y comprobar circulaciones antes del acabado y preimpresion.
