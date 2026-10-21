/**
 * Georreferenciación del mapa 3D (Fase mapa-3d · GPS).
 *
 * El modelo está en metros locales del plano técnico (X este, Y norte, origen
 * del PDF). Para pintar la ubicación GPS del visitante hace falta convertir
 * latitud/longitud a esas coordenadas.
 *
 * Calibración: transformación de semejanza (escala + giro + traslación)
 * ajustada por mínimos cuadrados con 9 esquinas medidas en sitio por el
 * equipo (Caja de Madera, Pabellón Blanco, Amarillo y Azul). Residuos entre
 * 2 y 6 m, por debajo de la precisión típica del GPS en el recinto.
 *
 *   E = a·x − b·y      N = b·x + a·y      (E, N en metros desde el origen)
 *   lat = lat0 + N / M_LAT   lon = lon0 + E / M_LON
 */

/** Latitud/longitud del origen (0, 0) del plano. */
export const ORIGEN_PLANO = { lat: 6.241281, lon: -75.57653 };

/** a = s·cos θ, b = s·sin θ (escala 1,0162; el eje +Y del plano apunta a 3,1° al este del norte). */
const A = 1.0147;
const B = -0.055386;
const S2 = A * A + B * B;

/** Metros por grado en la latitud de Medellín. */
const M_LAT = 110574;
const M_LON = 111320 * Math.cos((ORIGEN_PLANO.lat * Math.PI) / 180);

/** Caja que envuelve el recinto en coordenadas del plano (m), con margen de calle. */
export const RECINTO = { x0: -130, x1: 140, y0: -130, y1: 310 };

export type PuntoPlano = { x: number; y: number };

/** GPS → coordenadas del plano (metros). */
export function gpsAPlano(lat: number, lon: number): PuntoPlano {
  const dE = (lon - ORIGEN_PLANO.lon) * M_LON;
  const dN = (lat - ORIGEN_PLANO.lat) * M_LAT;
  return {
    x: (A * dE + B * dN) / S2,
    y: (-B * dE + A * dN) / S2,
  };
}

/** Coordenadas del plano → GPS (inversa exacta de gpsAPlano). */
export function planoAGps(p: PuntoPlano): { lat: number; lon: number } {
  const dE = A * p.x - B * p.y;
  const dN = B * p.x + A * p.y;
  return {
    lat: ORIGEN_PLANO.lat + dN / M_LAT,
    lon: ORIGEN_PLANO.lon + dE / M_LON,
  };
}

/** true si el punto cae dentro del recinto (con margen de calle). */
export function dentroDelRecinto(p: PuntoPlano): boolean {
  return (
    p.x >= RECINTO.x0 &&
    p.x <= RECINTO.x1 &&
    p.y >= RECINTO.y0 &&
    p.y <= RECINTO.y1
  );
}

/** Distancia (m) desde el punto hasta el borde del recinto; 0 si está dentro. */
export function distanciaAlRecinto(p: PuntoPlano): number {
  const dx = Math.max(RECINTO.x0 - p.x, 0, p.x - RECINTO.x1);
  const dy = Math.max(RECINTO.y0 - p.y, 0, p.y - RECINTO.y1);
  return Math.hypot(dx, dy);
}

/** Texto corto para el aviso de "fuera del recinto". */
export function textoDistancia(m: number): string {
  if (m < 950) return `${Math.round(m / 10) * 10} m`;
  return `${(m / 1000).toFixed(m < 10000 ? 1 : 0)} km`;
}
