# Caso real: Plaza Mayor Medellín · Feria Effix 2026

Cómo se hizo el primer mapa, del 1 al 7 de octubre de 2026. Lo hicieron Claude Code y Alexander Cast. Es el
origen de este kit. Los archivos originales están en `ejemplos/plaza-mayor/`.

## El recinto

Centro de convenciones con varios pabellones y salones en niveles distintos:
- **Pabellones**: Amarillo, Blanco, Azul, Rojo y Verde, más el Hall.
- **Convenciones**: Gran Salón (piso 1, −9 m), Salón Multipropósito (piso 2) y Caja de Madera (piso 3, el registro).
- **Exterior**: la plazoleta con el auditorio UGC en carpa y las gradas.

Lo difícil fueron los apilamientos:
- el Azul va sobre el Rojo;
- el Verde va sobre el Auditorio Comunidades;
- la Caja va sobre el Multipropósito, y este sobre el Gran Salón.

## Fases, en el orden real

1. **Maqueta v01**: extracción rápida del PDF a una escala supuesta (10,085 pt/m), sin validar. Sirvió para entender el
   problema y para descubrir que la escala estaba mal.
2. **Del PDF a metros (v02 → v03)**: `extraer_plano_v03.py` con PyMuPDF.
   - Stands por color de relleno, con código y rótulo de medida; sillas en 3 colores; tarimas, mesas, VIP, carros y motos.
   - Seis regiones, cada una con su escala y su anclaje. El plano dibujaba "al lado" pisos que van encima: el Rojo
     junto al Azul, y la Caja y el Multipropósito en recuadros aparte.
3. **Modelo en Blender (v02 → v04)**: `construir_mapa_v04.py`, unas 2.100 líneas, sin interfaz.
   - Helpers propios: acumulador de mallas, pabellones con vanos, gradas, rampas, escaleras eléctricas, truss,
     pantallas LED y torres de luces.
   - Los niveles flotantes cuelgan de los vacíos `RAIZ_*` con `LIFT = {sup: 34, multi: 16.5, caja: 30, shell: 52}`.
   - Texturas 100 % procedurales.
4. **Validación con fuentes externas**:
   - el recorrido 360 oficial del recinto (27 escenas), solo como referencia visual; traía un plano oficial con medidas;
   - el fotomontaje aprobado del evento;
   - las fichas técnicas del proveedor de producción (tarimas, pantallas, pórtico LED).
5. **Exportación web**: GLB con Draco (8,3 MB) más `datos.json`, y un visor three.js independiente.
6. **Integración en la app** (Next.js 16 + Supabase + Capacitor):
   - 238 stands cruzados por código con la base para mostrar empresa, logo y ficha;
   - buscador, recorrido guiado, "Mi ubicación" por GPS y analítica.
7. **Extras**: renders para revisión, video de recorrido completo (17–20 tramos, unas 3 horas de render) y una
   portada con el mapa girando al hacer scroll.

## Calibración

- **Escala por FFT** de la cuadrícula de fondo (1 m), una por eje:
  - principal: 9,25 pt/m en X y 9,76 en Y;
  - Gran Salón: 8,57 / 8,985;
  - Caja: 8,76 / 9,135;
  - Multipropósito, que no tiene cuadrícula: 13,3 / 13,6, deducida de las columnas cada 7,2 m y comprobada con la
    tarima de 5×3 y las escaleras eléctricas.
- **Validación**:
  - el stand R-13, rotulado 18×8, midió 18,0 × 8,0 m;
  - 211 de 215 stands coinciden con su rótulo (±12 %);
  - contra el plano oficial: Azul 41,6 × 59,8 m (modelo 41,7 × 59,6); Gran Salón 36,1 × 62,1 m (modelo 36,3 × 61,7).
- **Georreferencia**: semejanza por mínimos cuadrados con 9 esquinas medidas en sitio, con residuos de 2–6 m.

## Qué se le preguntó a la persona (y conviene preguntar siempre)

- La escala de la cuadrícula y cuál PDF manda (técnico frente a comercial).
- **Qué piso va encima de cuál.** Fue lo que más correcciones generó; hay que preguntarlo explícitamente.
- Cuántos metros baja el sótano y por dónde se baja (gradas de la plazoleta).
- Medidas en conflicto: el PDF da 96 m al Pabellón Blanco y el plano oficial 87,4 m. Se le preguntó cuál mantener y
  eligió 96 m.
- Dónde están en realidad las cosas que el PDF dibuja aparte (taquillas y registro dentro de la Caja, zonas exclusivas).
- Presentación: niveles flotando encima (no al lado), y pines numerados desde la entrada y coloreados por pabellón
  en vez de rótulos encima.
- Orientación de tarimas y pantallas y tipo de cubierta (trimalla o carpa a dos aguas).
- Permiso antes de publicar o fusionar a producción.

La persona corregía con capturas marcadas en colores. Cada cambio se revisaba en el visor local antes de publicar.

## Decisiones del visor y por qué

- **Exterior / Por niveles**: se separa sin mover nada en planta, para que se entienda que un piso está **sobre** otro.
- **Al tocar un lugar tapado**, el visor pasa solo a "Por niveles": la persona no tiene que saber en qué piso está.
- **Pines numerados desde el ingreso**: se pueden leer como un recorrido, y la lista sirve de leyenda.
- **Embebido sin portada**: al abrir la pestaña del mapa ya está el 3D, sin un botón extra.
- **Hoja inferior debajo del mapa** en celular, no encima: así no tapa los pines.
- **Rendimiento en celular**: render solo cuando algo cambia, sombras estáticas, `pixelRatio` ≤ 1,5 y el GLB solo se
  descarga al abrir el mapa.

## Pendientes que quedaron (para quien siga)

- Volver a renderizar el video con los niveles nuevos.
- Cambiar las texturas LED genéricas por el arte real del evento.
- Confirmar en sitio algunos accesos y bordes de zonas exteriores.

## Herramientas

- Blender 5.2 sin interfaz, render con EEVEE.
- Python con PyMuPDF, numpy y Pillow.
- three.js 0.170 (OrbitControls, GLTFLoader, DRACOLoader, RoomEnvironment).
- Navegador integrado de Claude Code para revisar el visor y el recorrido 360.
- Vercel para el despliegue de la app.

En el proyecto original no se usaron skills: este kit es el que los empaqueta.
