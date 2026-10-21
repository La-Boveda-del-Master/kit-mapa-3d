# Caso de origen: Plaza Mayor Medellín (fuente original)

Es el primer mapa, un centro de convenciones, y de él nació el kit. Aquí está **el código tal como se usó**, como referencia y cantera de piezas.
No es un proyecto listo para correr. La historia completa está en `docs/CASO-ORIGEN.md`.

## Contenido

| Carpeta | Qué hay |
|---|---|
| `fuente-original/` | Scripts del proyecto Blender: `extraer_plano_v03.py` (6 regiones, sillas, tarimas, catenarias), `construir_mapa_v04.py` (~2.100 líneas: gradas, rampas, escaleras eléctricas, truss, pórtico LED, vehículos, personas), `generador/make_v04.py` (la v04 se generaba parchando la v03), exportadores, renders, video y los LEEME de cada versión |
| `fuente-original/web/` | El primer visor web independiente |
| `app-nextjs/` | Integración en una app Next.js 16 + Supabase: `Mapa3D.tsx`, `mapa3d.ts`, `geo.ts` (GPS), `geolocation.ts` y la página |
| `renders/` | Vistas previas del resultado |

## Lo que no está y por qué

- **El PDF técnico del montaje, los espacios extraídos (`plano_v03.json`), los tapetes, los pines y el modelo
  `mapa.glb`**: son material del cliente y de terceros.
- **Las fichas técnicas del proveedor de producción y las capturas del recorrido 360 oficial**: son de terceros.

Por eso los scripts tienen rutas absolutas (`D:/Usuario/...`) y no corren tal cual: léelos y copia las piezas al
pipeline genérico (`pipeline/`) o a un `detalles.py` de tu proyecto.
