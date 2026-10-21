---
name: mapa-integrar-app
description: Integra el mapa 3D dentro de una app web o móvil existente (React, Next.js, Capacitor). Cruza los espacios (salas, locales, espacios, oficinas) con una base de datos para traer nombre, logo y ficha, y suma buscador, recorrido guiado, "Mi ubicación" por GPS y analítica. Úsalo cuando el mapa va dentro de un producto y no como página suelta.
---

# Integrar el mapa en una app

Hay dos caminos. Empieza por el primero y pasa al segundo solo si la persona lo necesita.

## Camino A · iframe (una tarde)

Publica `salida/web/` (skill `mapa-visor-web`) y embébelo en la app:

```tsx
<iframe src="https://mapa.midominio.com/?espacio=A12" className="w-full h-[80vh] border-0" allow="fullscreen; geolocation" />
```

- Los enlaces `?lugar=N` y `?espacio=CODIGO` abren el mapa ya enfocado. Desde la ficha de cualquier elemento en la app
  (una sala, un local, un expositor), enlaza al mapa con su código.
- Nombre y detalle de cada espacio: agrégalos en `mapa.json` (`espacios[].nombre`, `espacios[].detalle`), o genera
  `datos.json` desde la base antes de publicar (`datos.espacios[]`).

## Camino B · componente nativo

Código real de referencia (la integración del caso de origen) en `ejemplos/caso-origen-plaza-mayor/app-nextjs/`:

| Archivo | Qué hace |
|---|---|
| `Mapa3D.tsx` | Visor completo en React (~1.700 líneas). Incluye hoja inferior, buscador, capas Lugares/Espacios, recorrido guiado, pantalla completa, GPS, analítica, pin con varilla y logo. |
| `mapa3d.ts` | Lógica pura: `normalizeStandCode` (A 05 ↔ A05, B ↔ BL), `mergeEspacios` (cruce con la base), `filterEspacios`, `ordenRecorrido`. |
| `geo.ts` | GPS → plano con una transformación de semejanza. Incluye `dentroDelRecinto` y `distanciaAlRecinto`. |
| `geolocation.ts` | Adaptador de plataforma para `navigator.geolocation` (luego Capacitor). |
| `mapa-page.tsx` | La página: lee espacios de la vista pública de Supabase y se los pasa al visor. |

Depende de piezas de esa app (`@/lib/cn`, `@/lib/analytics`, `@/lib/platform/*`, `lucide-react`, `three@0.170`).
Adáptalo así:

1. `npm i three@0.170.0` y `npm i -D @types/three`. Copia `mapa.glb`, `datos.json` y `draco/` a `public/mapa3d/`.
   En el componente: `DRACOLoader().setDecoderPath('/mapa3d/draco/')`.
2. Carga three con `import()` dinámico dentro de un `useEffect`. El GLB pesa varios MB: que solo baje cuando se abre el mapa.
3. Reemplaza los imports propios: `cn` por `clsx`, `track` por la analítica de la app o una función vacía, y el
   adaptador de geolocalización por `navigator.geolocation` directo si la app no es nativa.
4. Si los códigos de la base y del plano difieren, ajusta `normalizeStandCode` en un solo lugar. Ejemplos de
   diferencias: "BL 02 A" frente a "B02A", o ceros a la izquierda.
5. Guarda el estado de three (escena, cámara, controles) en un `useRef`, no en el estado de React: el lint de hooks
   se queja de las mutaciones y además re-renderiza de más.
6. Mide el contenedor con `ResizeObserver` e ignora tamaños menores de 50 px. Hubo un bug real: el visor quedaba en
   0×0 en algunos celulares.

## GPS "Mi ubicación" (opcional)

1. Pide a la persona que mida en sitio **6–10 esquinas** del lugar con el celular (lat/lon) y ubícalas en el plano
   (x, y en metros).
2. Ajusta una semejanza (escala, rotación, traslación) por mínimos cuadrados. En el caso de origen se usaron 9 esquinas,
   con residuos de 2–6 m.
3. Pon los coeficientes en `geo.ts`.
4. El GPS no distingue pisos: pinta el punto a nivel del suelo y dilo en la interfaz.
5. Permisos:
   - web: cabecera `Permissions-Policy: geolocation=(self)` (con `geolocation=()` falla en silencio);
   - Android: `ACCESS_FINE_LOCATION` y `ACCESS_COARSE_LOCATION`;
   - iOS: `NSLocationWhenInUseUsageDescription`.
6. Privacidad: la posición no se guarda. Si se quiere analítica de posición, redondéala a una cuadrícula y pide consentimiento.

## Recorrido guiado y analítica

- **Recorrido**: una lista ordenada de pines, que puede venir de la configuración de la app. Avanza solo cada ~6,5 s,
  muestra una etiqueta a la vez y tiene pausa y salida. Ver `ordenRecorrido` en `mapa3d.ts`.
- **Analítica útil**: abrir mapa, cambiar modo, elegir lugar, elegir espacio, búsqueda (texto y número de
  resultados) y estado del GPS.

## Antes de dar por terminado

Corre el typecheck, el lint y los tests de la app. Prueba en un celular real (no solo en el emulador del navegador)
y confirma en la pestaña Network que el GLB llega comprimido y cacheado.
