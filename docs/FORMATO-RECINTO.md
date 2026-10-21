# Formato de recinto.json y plano.json

Todo en **metros**. Mundo: **+X Este, +Y Norte, Z arriba**. Colores `[r, g, b]` lineales de 0 a 1.
Ejemplo completo y probado: `ejemplos/demo-centro-eventos/`.

## recinto.json

```jsonc
{
  "id": "mi-recinto",                       // sin espacios
  "nombre": "Centro de Convenciones X",
  "evento": {
    "titulo": "FERIA X 2027",               // cabecera y pantalla de carga del visor
    "subtitulo": "Ciudad · 10 al 12 de mayo",
    "nota": "Escala según plano técnico. Alturas aproximadas.",   // pie del panel
    "titulo_lista": "Lugares de la feria"
  },
  "stands_desde": "salida/plano_m.json",    // opcional: suma stands, objetos y zonas extraídos del PDF
  "terreno": { "margen": 80, "material": "concreto",
               "vias": [[[x0, y0], [x1, y1], ancho]] },
  "niveles": [ ... ], "edificios": [ ... ], "zonas": [ ... ],
  "stands": [ ... ], "objetos": [ ... ], "pines": [ ... ],
  "recorrido": [ ... ]                      // opcional: tramos del video
}
```

### niveles

| campo | qué es |
|---|---|
| `id` | nombre corto (`base`, `p2`, `sotano`) |
| `nombre` | lo que se lee en el visor ("Pabellón B · piso 2") |
| `z` | altura del piso en m (sótanos negativos) |
| `separacion` | m que sube en el modo "Por niveles" (solo niveles que tapan a otro). Crea el vacío `RAIZ_<id>` |
| `bajo_techo` | `true` si otro nivel lo tapa: sus pines se esconden en "Exterior" |

### edificios

| campo | qué es |
|---|---|
| `id`, `nombre`, `nivel` | `nombre` se rotula en el piso y en la cubierta |
| `poligono` | `[[x, y], ...]`, 3 o más puntos |
| `altura` | m desde el piso del nivel hasta la cubierta |
| `color` | color del pabellón (tiñe fachada de panel y cubierta) |
| `piso` | material del piso interior (por defecto `concreto_pulido`) |
| `fachada` | material del muro en vez del panel teñido (`madera`, `vidrio`, `ladrillo`, `arenisca_muro`…) |
| `cubierta` | `false` para no poner techo (un piso con otro encima) |
| `muro_bajo` | alto del muro que queda visible en "Por niveles" (3,2) |
| `grosor_muro` | 0,4 |
| `puertas` | `[{ "lado": 0, "centro": 20, "ancho": 6 }]`: lado = índice desde 0 en el orden del polígono **ya en sentido antihorario** (si lo diste horario se invierte); centro en m desde el primer vértice de ese lado |
| `rotulo`, `tam_rotulo`, `rot_rotulo` | rótulo sí/no, tamaño en m, giro en grados |
| `z` | desplazamiento extra sobre el piso del nivel |

### zonas

`{ "id", "nivel", "poligono", "material" | [r,g,b], "alto": 0.06, "z": 0, "rotulo", "tam_rotulo", "rot_rotulo" }`

Materiales: `concreto`, `concreto_pulido`, `piedra_pulida`, `alfombra`, `madera`, `madera_clara`, `pav_plaza`,
`pav_arenisca`, `pav_oscuro`, `cesped`, `asfalto`, `agua`, `arenisca_muro`, `ladrillo`, `vidrio`, `blanco`, `negro`.

### stands

`{ "codigo": "A05", "nivel", "poligono", "altura": 2.4, "color": [r,g,b], "nombre", "detalle", "rot_rotulo", "z" }`

`nombre` y `detalle` aparecen en la lista y la ficha del visor. El buscador encuentra "a5", "A 05" y "A05" por igual.

### objetos

| tipo | campos |
|---|---|
| `tarima` | `centro [x,y]`, `ancho`, `fondo`, `alto` (0,6), `rot`, `pantalla: { ancho, alto, base }`. La pantalla va al fondo y mira hacia `rot + 90°` (rot 0 → norte, 180 → sur) |
| `pantalla` | `centro`, `ancho`, `alto`, `base` (alto del borde inferior), `rot` |
| `sillas` | `area [[x0,y0],[x1,y1]]`, `paso [0.6, 1.0]`, `rot` |
| `sillas_puntos` | `puntos [[x, y, rot_grados], ...]` (las genera extraer_plano) |
| `carpa` | `centro`, `ancho`, `fondo`, `alto`, `rot` |
| `arbol` | `puntos [[x, y], ...]`, `escala` |
| `caja` | `centro`, `tam [ancho, fondo, alto]`, `material` o `color`, `rot` (taquillas, counters, bloques) |

Todos aceptan `nivel`, `z` (relativo al nivel) y `rotulo`.

### pines

`{ "n": 1, "nombre", "detalle", "nivel", "pos": [x, y, alto_sobre_el_piso], "color": [r,g,b] }`

Numera en el orden del recorrido del público. Usa el color del pabellón para que la lista se lea por zonas.

### recorrido (video)

`[{ "nombre", "segundos", "puntos": [[[cam_x, cam_y, cam_z], [mira_x, mira_y, mira_z]], ...] }]`, en coordenadas
absolutas del mundo.

## plano.json (para extraer_plano.py)

```jsonc
{
  "pdf": "entrada/plano.pdf",
  "pagina": 0,
  "regiones": [                               // la primera que contenga el punto gana: pequeñas primero
    { "id": "gran_salon", "nivel": "sotano", "bbox_pt": [x0, y0, x1, y1],
      "escala_pt_m": [sx, sy], "origen_pt": [x, y], "origen_m": [X, Y], "rotacion": 0, "mover_m": [0, 0] },
    { "id": "principal", "nivel": "base", "escala_pt_m": [9.25, 9.76], "origen_pt": [1300, 1150], "origen_m": [0, 0], "rotacion": 90 }
  ],
  "reglas": [
    { "tipo": "stand", "relleno": [0.95, 0.62, 0.64], "tolerancia": 0.03, "area_min_pt": 40,
      "codigo": "^[A-Z]{1,3}[- ]?[0-9]", "color": [0.3, 0.58, 0.95], "nivel": "opcional" },
    { "tipo": "silla", "relleno": [0.69, 0.68, 0.68], "lado_max_pt": 15 },
    { "tipo": "zona",  "relleno": [r, g, b], "material": "cesped", "id": "jardin" },
    { "tipo": "caja",  "relleno": [r, g, b], "alto": 1.1, "material": "negro" }
  ]
}
```

Transformación de una región: `dx = (x_pt − origen_pt.x) / sx`, `dy = −(y_pt − origen_pt.y) / sy`, se rota
`rotacion` grados antihorario y se suma `origen_m + mover_m`.

Salida `salida/plano_m.json`: `{ stands: [...], objetos: [...], zonas: [...], validacion: {...} }`, con el mismo
formato de recinto.json, listo para `stands_desde`.
