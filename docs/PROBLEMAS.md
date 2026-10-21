# Problemas conocidos y cómo se resolvieron

Todo esto pasó de verdad en el mapa de Plaza Mayor (Feria Effix 2026).

## Plano y escala

| Síntoma | Causa | Arreglo |
|---|---|---|
| Edificios con proporciones raras | El PDF viene estirado: escala distinta en X y en Y | `escala_pt_m: [sx, sy]` por eje; medir con FFT de la cuadrícula (`inspeccionar`) |
| Un salón no cuadra con el resto | El plano lo dibuja en un recuadro a otra escala | Región propia con su escala y su punto de anclaje |
| Pisos dibujados uno al lado del otro | Así los pone el plano; en realidad van apilados | Misma planta, distinto nivel, `separacion` en el de arriba |
| Zona sin cuadrícula | El recuadro no la trae | Deducir la escala de algo repetido conocido (columnas cada 7,2 m, una tarima de 5×3) |
| Dos fuentes dan medidas distintas | PDF de montaje frente a plano oficial | Preguntar cuál manda y anotarlo; no promediar |
| Stand sin código | El texto quedó fuera del rectángulo | Patrón `codigo` más flexible o poner el código a mano |

## Modelo (Blender)

| Síntoma | Causa | Arreglo |
|---|---|---|
| `KeyError: 'Principled BSDF'` | Los nombres de nodo cambian con el idioma de Blender | Buscar por tipo: `n.type == 'BSDF_PRINCIPLED'` (ya hecho en el kit) |
| `DeprecationWarning: use_nodes` | Blender 5 avisa que lo quitará en la versión 6 | Inofensivo por ahora; en Blender 6 quitar esas líneas |
| El video no codifica en Blender 5 | `sequence_editor.sequences` pasó a llamarse `strips`, y `strips` vacío es falso | `se.strips if hasattr(se, 'strips') else se.sequences` (ya hecho) |
| Pantalla de espaldas al público | Orientación calculada con sillas de otro nivel | Orientar con `rot` explícito; si se calcula, filtrar por el mismo nivel |
| Cara LED invertida | Orden de vértices al revés | Invertir el orden (a, b) de la cara |
| No sobrescribe un PNG | Windows lo tiene abierto en un visor | Cerrar el visor o renderizar con otro nombre |
| Script de Python roto con "unterminated string" | Se escribió dentro de un heredoc de Bash | Escribir archivos con la herramienta de edición, no con `cat <<EOF` |
| `PIL` no guarda en `/d/...` (Windows) | Ruta estilo Git Bash | Usar `D:/...` |

## Visor web

| Síntoma | Causa | Arreglo |
|---|---|---|
| "No se pudo cargar el mapa" | Se abrió `index.html` con doble clic (file://) | Servir con `python -m http.server` o publicar |
| Se ve el modelo viejo | Caché del navegador o del CDN | `?v=` sellado al exportar; en una app, subir la constante de versión |
| Pines que se quedan atrás al girar | `transition` CSS en la posición del pin | Sin transición en `transform`; recolocar en el mismo cuadro del render |
| Visor en 0×0 en algunos celulares | Se midió antes de tener tamaño | Ignorar tamaños menores de 50 px; `ResizeObserver` con respaldo `resize`/`orientationchange` |
| Lento en celular | Píxeles, sombras y llamadas de dibujo | `pixelRatio ≤ 1,5` en táctil, sombra de 2048 y estática, render solo si algo cambió, mallas unidas |
| Stands repetidos en la búsqueda | El mismo código en varios polígonos | Deduplicar por código y quedarse con el más grande (ya en `extraer_plano`) |

## Peso del modelo

Meta: **≤ 10 MB** de GLB. Plaza Mayor quedó en 8,3 MB con ~930.000 triángulos y Draco nivel 6. Si te pasas:

1. Sillas: son miles de cajas. Bájales detalle o quítalas de los salones que no importan.
2. Textos: el exportador ya une los códigos de stand por nivel; los rótulos sueltos suman.
3. Árboles, vehículos y personas: menos instancias.
4. Texturas: 512 px está bien para el visor; no subas a 2048.
5. Revisa `tris` en la salida del exportador después de cada cambio grande.

## Publicación y app

| Síntoma | Causa | Arreglo |
|---|---|---|
| GPS "permiso denegado" en Chrome | `Permissions-Policy: geolocation=()` | `geolocation=(self)` |
| La app de tienda no pide ubicación | No se declaró el permiso | Android `ACCESS_FINE/COARSE_LOCATION`; iOS `NSLocationWhenInUseUsageDescription`; nueva versión |
| `next dev` reescribe `AGENTS.md` | Next.js 16 regenera el archivo | `git checkout -- AGENTS.md` antes de cada commit |
| Un commit trae cambios de otra sesión | `git add -A` con varias sesiones en el mismo repo | Trabajar en un `git worktree` aparte y agregar archivos por nombre |
