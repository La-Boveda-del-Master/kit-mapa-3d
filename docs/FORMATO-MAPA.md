# Formato de mapa.json y plano.json

Todo en **metros**. Mundo: **+X Este, +Y Norte, Z arriba**. Colores `[r, g, b]` lineales de 0 a 1, o hex en `marca.color`.
Ejemplos completos y probados: `ejemplos/campus-demo/` y `ejemplos/oficina-demo/`.

## mapa.json

```jsonc
{
  "id": "mi-lugar",
  "nombre": "Nombre del lugar",
  "marca": {
    "titulo": "MI LUGAR",                 // cabecera del visor y de las láminas
    "subtitulo": "Ciudad · cliente · fecha",
    "nota": "Escala según plano. Alturas aproximadas.",   // pie del visor y de las láminas
    "color": "#2563eb",                   // acento del visor y de las láminas
    "logo": "entrada/logo.png",           // opcional
    "etiqueta_lugares": "Lugares",
    "etiqueta_espacios": "Salas"          // Salas, Locales, Stands, Oficinas, Habitaciones, Lotes…
  },
  "importar": "salida/plano_m.json",      // opcional: suma lo extraído del plano (espacios, muros, edificios, zonas, objetos)
  "calco": { "imagen": "entrada/plano.jpg", "px_por_m": 12.5, "origen_px": [0, 900], "origen_m": [0, 0] },   // opcional
  "terreno": { "margen": 40, "material": "concreto", "vias": [[[x0, y0], [x1, y1], ancho]] },   // "ninguno" = sin terreno
  "niveles": [ ... ], "edificios": [ ... ], "muros": [ ... ], "espacios": [ ... ],
  "zonas": [ ... ], "objetos": [ ... ], "pines": [ ... ],
  "recorrido": [ ... ]                    // opcional: tramos del video
}
```

### niveles

| campo | qué es |
|---|---|
| `id` | nombre corto (`base`, `p1`, `p2`, `sotano`) |
| `nombre` | lo que se lee en el visor y la leyenda ("Piso 2") |
| `z` | altura del piso en m (sótanos negativos) |
| `separacion` | m que sube en "Por niveles". Va en todo nivel que tape a otro; crece piso a piso (11, 22, 33…) |
| `bajo_techo` | `true` si otro nivel lo tapa: sus lugares se esconden en "Exterior" |

### edificios (uno por edificio y por piso)

| campo | qué es |
|---|---|
| `id`, `nombre`, `nivel` | `nombre` se rotula en la cubierta (y en el piso, salvo `rotulo_piso: false`) |
| `poligono` | `[[x, y], ...]` |
| `altura` | m del piso de ese nivel hasta su techo |
| `color` | tiñe fachada de panel y cubierta |
| `fachada` | material del muro en vez del panel teñido (`vidrio`, `ladrillo`, `madera`, `arenisca_muro`, `blanco`…) |
| `piso` | material del piso (por defecto `concreto_pulido`) |
| `cubierta` | `false` en pisos con otro encima |
| `muro_bajo` | lo que queda visible en "Por niveles" (3,2; usa 1,1 en pisos con interiores) |
| `muros_altos` | `false` para no poner muro por encima de `muro_bajo` (plazas cubiertas, pérgolas) |
| `ventanas` | franja de vidrio continua en el muro alto (por defecto sí) |
| `losa` | `false` si no lleva losa propia |
| `puertas` | `[{ "lado": 0, "centro": 20, "ancho": 6 }]`: lado = índice desde 0 en el polígono **en sentido antihorario** |
| `grosor_muro`, `tam_rotulo`, `rot_rotulo`, `z` | ajustes finos |

### muros (tabiques y cerramientos)

`{ "nivel", "puntos": [[x, y], ...], "alto": 2.6, "grosor": 0.15, "cerrado": false, "material": "muro_interior", "puertas": [{ "tramo": 0, "centro": 2, "ancho": 0.9 }] }`

### espacios (lo que se busca: salas, locales, stands, oficinas, lotes)

`{ "codigo": "P2-03", "nombre": "Gerencia", "detalle", "categoria", "nivel", "poligono", "altura": 0.04, "color", "rotulo", "rot_rotulo", "z" }`

- `altura` 0,04 → área pintada en el piso (salas, lotes); 2,4 → bloque (stands, módulos). Los planos se apoyan solos sobre la losa.
- `rotulo` reemplaza el texto del piso (por defecto el código). El tamaño del texto se ajusta solo al espacio.
- El buscador encuentra "p2-3", "P2 03" y "P2-03" por igual, y también por nombre.

### zonas

`{ "id", "nivel", "poligono", "material" | [r,g,b], "alto": 0.06, "z": 0, "rotulo", "tam_rotulo", "rot_rotulo" }`

Materiales: `concreto`, `concreto_pulido`, `piedra_pulida`, `alfombra`, `madera`, `madera_clara`, `pav_plaza`,
`pav_arenisca`, `pav_oscuro`, `cesped`, `asfalto`, `agua`, `arenisca_muro`, `ladrillo`, `vidrio`, `blanco`,
`muro_interior`, `negro`.

### objetos

| tipo | campos |
|---|---|
| `escalera` | `desde [x,y]` (abajo), `hasta [x,y]` (arriba), `sube` (m), `ancho` |
| `mesas` | `puntos [[x, y, rot], ...]`, `tam [ancho, fondo]`, `material` |
| `sillas` | `area [[x0,y0],[x1,y1]]`, `paso [0.6, 1.0]`, `rot` |
| `sillas_puntos` | `puntos [[x, y, rot], ...]` (las genera extraer_plano) |
| `tarima` | `centro`, `ancho`, `fondo`, `alto`, `rot`, `pantalla: { ancho, alto, base }` (mira hacia `rot + 90°`) |
| `pantalla` | `centro`, `ancho`, `alto`, `base`, `rot` |
| `carpa` | `centro`, `ancho`, `fondo`, `alto`, `rot` |
| `arbol` | `puntos [[x, y], ...]`, `escala` |
| `caja` | `centro`, `tam [ancho, fondo, alto]`, `material` o `color`, `rot` (mostradores, equipos, bloques) |

Todos aceptan `nivel`, `z` (relativo al piso del nivel) y `rotulo`.

### pines (lugares)

`{ "n": 1, "nombre", "detalle", "nivel", "pos": [x, y, alto_sobre_el_piso], "color": [r,g,b] }`

### recorrido (video)

`[{ "nombre", "segundos", "puntos": [[[cam_x, cam_y, cam_z], [mira_x, mira_y, mira_z]], ...] }]`, en coordenadas de mundo.

## plano.json (para extraer_plano.py)

### PDF

```jsonc
{
  "pdf": "entrada/plano.pdf", "pagina": 0,
  "regiones": [                               // la primera que contenga el punto gana: pequeñas primero
    { "id": "piso2", "nivel": "p2", "bbox_pt": [x0, y0, x1, y1], "escala_pt_m": [sx, sy],
      "origen_pt": [x, y], "origen_m": [X, Y], "rotacion": 0, "mover_m": [0, 0] },
    { "id": "principal", "nivel": "p1", "escala_pt_m": [10, 10], "origen_pt": [100, 900], "origen_m": [0, 0] }
  ],
  "reglas": [
    { "tipo": "espacio", "relleno": [0.95, 0.62, 0.64], "tolerancia": 0.03, "area_min_pt": 40, "codigo": "^[A-Z]{1,3}[- ]?[0-9]", "color": [r,g,b] },
    { "tipo": "silla",   "relleno": [0.69, 0.68, 0.68], "lado_max_pt": 15 },
    { "tipo": "zona",    "relleno": [r, g, b], "material": "cesped" },
    { "tipo": "caja",    "relleno": [r, g, b], "alto": 1.1, "material": "negro" }
  ]
}
```

Transformación: `dx = (x_pt − origen_pt.x)/sx`, `dy = −(y_pt − origen_pt.y)/sy`, rotada `rotacion`° antihoraria,
más `origen_m + mover_m`.

### DXF (CAD)

```jsonc
{
  "dxf": "entrada/plano.dxf",
  "unidad_m": 0.001,                          // opcional si el DXF trae $INSUNITS
  "regiones": [
    { "id": "piso1", "nivel": "p1", "bbox": [x0, y0, x1, y1], "origen_dibujo": [0, 0], "origen_m": [0, 0], "rotacion": 0,
      "edificio": { "cubierta": false } }    // ajustes a los edificios de esta región
  ],
  "reglas": [                                 // por capa (acepta comodines *)
    { "capa": "A-EDIFICIO",   "tipo": "edificio", "altura": 3.6, "muro_bajo": 1.1, "color": [r,g,b], "fachada": "vidrio", "rotulo_piso": false },
    { "capa": "A-MUROS*",     "tipo": "muro", "alto": 2.7, "grosor": 0.12 },
    { "capa": "A-ESPACIOS",   "tipo": "espacio", "altura": 0.04, "capa_textos": "A-TEXTOS", "codigo": "^P[0-9]", "rotulo": "nombre", "color": [r,g,b] },
    { "capa": "A-JARDIN",     "tipo": "zona", "material": "cesped" },
    { "capa": "A-MOBILIARIO", "tipo": "caja", "alto": 0.75, "material": "madera_clara" },
    { "capa": "A-TEXTOS",     "tipo": "texto" }
  ]
}
```

Lee LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, HATCH, TEXT y MTEXT. Los bloques (INSERT) no se explotan: si el
mobiliario viene en bloques, explótalo en CAD antes de exportar, o ignóralo.

Salida `salida/plano_m.json`: `{ espacios, muros, edificios, zonas, objetos }`, en el mismo formato de mapa.json y
listo para `importar`.
