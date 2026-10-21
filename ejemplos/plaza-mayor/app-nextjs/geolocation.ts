/**
 * Adaptador de geolocalización — capa de plataforma.
 *
 * Web y shell nativo usan la misma API del navegador (`navigator.geolocation`):
 * dentro del WebView de Capacitor funciona cuando el permiso está declarado
 * (Android: ACCESS_FINE_LOCATION en el manifest; iOS:
 * NSLocationWhenInUseUsageDescription en Info.plist) y el sistema pide la
 * autorización al usuario la primera vez.
 */

export type Ubicacion = {
  lat: number;
  lon: number;
  /** Radio de precisión en metros (68 %). */
  precision: number;
  /** Marca de tiempo del fix (ms). */
  ts: number;
};

export type ErrorUbicacion =
  | "sin_soporte"
  | "denegado"
  | "no_disponible"
  | "tiempo";

/** true si el dispositivo puede geolocalizar. */
export function geolocalizacionDisponible(): boolean {
  return typeof navigator !== "undefined" && "geolocation" in navigator;
}

/**
 * Sigue la posición del dispositivo hasta que se llama a la función devuelta.
 * Alta precisión (GPS) y sin caché: en una feria la persona se mueve.
 */
export function vigilarUbicacion(
  onPos: (u: Ubicacion) => void,
  onError: (e: ErrorUbicacion) => void,
): () => void {
  if (!geolocalizacionDisponible()) {
    onError("sin_soporte");
    return () => {};
  }
  const id = navigator.geolocation.watchPosition(
    (p) =>
      onPos({
        lat: p.coords.latitude,
        lon: p.coords.longitude,
        precision: p.coords.accuracy,
        ts: p.timestamp,
      }),
    (err) => {
      if (err.code === err.PERMISSION_DENIED) onError("denegado");
      else if (err.code === err.TIMEOUT) onError("tiempo");
      else onError("no_disponible");
    },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 20000 },
  );
  return () => navigator.geolocation.clearWatch(id);
}
