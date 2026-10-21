# Mapa Feria Effix 2026 – Plaza Mayor · v03 (por niveles)

Reemplaza la v02. La planta sale del **PDF técnico** (cuadrícula = 1 m). Los recintos que el PDF dibuja "al lado" quedan ubicados donde van.

## Archivos
- `extraer_plano_v03.py` → `plano_v03.json` y `validacion_medidas_v03.json`
- `construir_mapa_v03.py` → `Plaza_Mayor_mapa_v03.blend` y `leyenda_v03.json`
- `render_mapa_v03.py` → `renders_v03/*.png`
- `componer_leyenda.py` → `renders_v03/*_leyenda.png` (panel con los pines numerados)

```
python extraer_plano_v03.py
blender -b --factory-startup --python construir_mapa_v03.py
blender -b Plaza_Mayor_mapa_v03.blend --python render_mapa_v03.py -- mapa_iso maqueta_iso mapa_planta mapa_planta_inferior
python componer_leyenda.py
```

## Vistas
| Archivo | Qué muestra |
|---|---|
| `mapa_iso` | Mapa general con los niveles flotando, visto desde el oriente (Metroplús). Norte a la derecha, como el PDF. |
| `mapa_niveles_caja` | Acercamiento a Gran Salón → Multipropósito → Caja piso 3 → Caja completa. |
| `mapa_niveles_azul_verde` | Acercamiento al Azul sobre el Rojo y al Verde sobre el Auditorio Comunidades. |
| `maqueta_iso` | Volumetría exterior con cubiertas, todo en su sitio. |
| `maqueta_ingreso` | Frente norte de la Caja: pórtico de ingreso y letrero Yo ♥ Medellín. |
| `maqueta_ugc` | Carpa del Auditorio UGC y estructuras flotantes de la plazoleta. |
| `maqueta_gradas` | Gradas de la plazoleta hacia el Gran Salón, con la Caja encima. |
| `mapa_planta` | Planta del nivel principal, el superior y la Caja piso 3. |
| `mapa_planta_inferior` | Planta de Rojo, Auditorio Comunidades y Gran Salón (piso 1). |
| `mapa_planta_intermedia` | Planta del Salón Multipropósito (piso 2). |
| `detalle_registro` | Interior de la Caja: taquilla, counters, acreditación, filas, escaleras. |

## Niveles
| Nivel | Recintos | Altura usada |
|---|---|---|
| Superior | Pabellón Azul, Zona VIP, Pabellón Verde | +7,5 m |
| Principal | Amarillo, Blanco, Hall, Zona de Comidas, Plazoleta Interamericana, plaza de la Caja | 0 |
| Inferior | Pabellón Rojo (bajo el Azul), Auditorio Comunidades (bajo el Verde) | 0, debajo del superior |
| Caja piso 3 | Pórtico de ingreso 10×6, registro, taquillas, acreditación (todo adentro) | 0 |
| Multipropósito piso 2 | Zona VIP 400 px, oficina Grupo Effi (más pequeño que los otros) | −4,5 m |
| Gran Salón piso 1 | Auditorio E-commerce 2.900 px, lobby, Zona Black | −9 m |

En modo mapa los niveles de arriba flotan sobre los de abajo, en la misma posición en planta, con guías punteadas.

## Cómo se ubicó lo que el PDF dibuja aparte
- **Caja, Multipropósito y Gran Salón:** se alinearon por el vacío central y las escaleras eléctricas, que aparecen en los tres planos. Coinciden con menos de 1 m de diferencia. Resultado: la Caja (41,7 × 45,8 m) queda sobre el lobby del Gran Salón, junto a las gradas de la plazoleta, no centrada sobre el auditorio.
- **Gradas Plazoleta ↔ Gran Salón:** franja rayada del PDF, de 65,5 m de ancho por 10,7 m de fondo, en dos tramos con descanso.
- **Auditorio Comunidades:** se desplazó 257 pt (unos 27 m) hacia adentro del Verde, perpendicular a su borde norte, conservando su giro.
- **Pabellón Rojo:** bajo el Azul (ambos miden 41,8 m de ancho).

## Validación de medidas (rótulo NxM contra dibujo)
- Zona principal: 211 de 215 stands coinciden (±12 %).
- Rojo: 19 de 19.
- Tarima 3×3 de la Caja: 3,0 × 3,0 m. Tarima 5×3 del Multipropósito: 5,0 × 3,3 m.
- Gran Salón: los PL19 a PL24 están rotulados 4×4 pero dibujados de 3,5 × 2,7 m. Se respetó el dibujo.
- El detalle de los que difieren está en `validacion_medidas_v03.json`.

## Pines
Los espacios se identifican con pines numerados por color, del 1 (ingreso por la Caja) al 21. La lista está en `leyenda_v03.json` y se edita en la sección "PINES" de `construir_mapa_v03.py`.

## Supuestos por confirmar
1. **Nivel del Verde:** se puso al nivel del Azul (+7,5 m) porque el PDF los une con la Zona VIP y el "Ingreso público general". Blanco, Hall y Amarillo quedaron en 0.
2. **Alturas:** todas son estimadas (pisos, cubiertas, −9 m del Gran Salón). El PDF no trae cortes.
3. **Escala del Multipropósito:** ese plano no tiene cuadrícula. Se dedujo de la modulación de columnas del Gran Salón (7,2 m) y se comprobó con la tarima 5×3.
4. **Escaleras eléctricas:** se asumió que el tramo oriental conecta piso 3 con piso 2 y el occidental piso 2 con piso 1.
5. **Posición exacta del Auditorio Comunidades** bajo el Verde: el PDF no la acota.
6. **Entorno:** Teatro, vías, río, Metroplús y ciudad son referenciales, tomados de la foto aérea.
7. **Estructuras flotantes de la plazoleta:** trazado aproximado según el plano y las fotos.
8. **Stands BR-xx** exteriores al Rojo: no se ubicaron.
