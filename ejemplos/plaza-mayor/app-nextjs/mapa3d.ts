/**
 * Mapa 3D del recinto (Fase mapa-3d).
 *
 * El modelo (public/mapa3d/mapa.glb) y sus datos (public/mapa3d/datos.json)
 * se generan fuera de la app, desde el plano técnico de la feria
 * (proyecto "Mapa Plaza mayor", scripts exportar_web.py y
 * exportar_stands_app.py). Aquí solo vive la lógica de negocio: cruzar los
 * stands del plano con `stands_publico` para que cada pin muestre la empresa,
 * su logo y su ficha del directorio.
 */

/** Pin de lugar (auditorios, ingresos, zonas) ya numerado desde el plano. */
export type MapaPin = {
  n: number;
  nombre: string;
  detalle: string;
  /** Color lineal 0..1 del material del pin. */
  color: [number, number, number];
  nivel: string;
  /** Posición en metros: X este, Y norte, Z alto (sistema del plano). */
  pos: [number, number, number];
  /** Grupo de nivel al que pertenece (base, sup, inf, gs, multi, caja). */
  grupo: string;
};

/** Stand tal como viene del plano técnico (posición 3D). */
export type MapaStandPlano = {
  codigo: string;
  key: string;
  pabellon: string;
  grupo: string;
  pos: [number, number, number];
  alto: number;
};

export type MapaDatos = {
  lift: Record<string, number>;
  raices: Record<string, string>;
  pines: MapaPin[];
  stands: MapaStandPlano[];
};

/** Fila de `stands_publico` que necesita el mapa (vista pública, RLS). */
export type StandPublico = {
  id: string;
  codigo: string | null;
  nombre: string | null;
  pabellon: string | null;
  tipo_stand: string | null;
  logo_url: string | null;
  directorio_descripcion: string | null;
};

/** Stand listo para el visor: posición del plano + datos del directorio. */
export type MapaStand = MapaStandPlano & {
  id: string | null;
  nombre: string | null;
  tipo: string | null;
  logo: string | null;
  descripcion: string | null;
};

/**
 * Normaliza un código de stand para cruzar el plano con la base de datos.
 * El plano escribe "A05", "B02A", "R-13", "T01"; la base, "A 05", "BL 02 A",
 * "R 06", "T1". Se dejan solo letras y números, se quitan los ceros a la
 * izquierda y el prefijo B (plano) pasa a BL (base). Ej.: ambos → "BL2A".
 */
export function normalizeStandCode(code: string | null | undefined): string {
  const c = (code ?? "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  const m = /^([A-Z]+)0*(\d+)([A-Z]*)$/.exec(c);
  if (!m) return c;
  const [, preRaw, num, suf] = m;
  const pre = preRaw === "B" ? "BL" : preRaw;
  return `${pre}${parseInt(num, 10)}${suf}`;
}

/** Cruza los stands del plano con la base por código normalizado. */
export function mergeStands(
  plano: MapaStandPlano[],
  db: StandPublico[],
): MapaStand[] {
  const byKey = new Map<string, StandPublico>();
  for (const s of db) {
    const k = normalizeStandCode(s.codigo);
    if (k && !byKey.has(k)) byKey.set(k, s);
  }
  return plano.map((p) => {
    const s = byKey.get(p.key);
    return {
      ...p,
      id: s?.id ?? null,
      nombre: s?.nombre ?? null,
      tipo: s?.tipo_stand ?? null,
      logo: s?.logo_url ?? null,
      descripcion: s?.directorio_descripcion ?? null,
    };
  });
}

/** Filtro del buscador: por código o por nombre de empresa, sin tildes. */
export function filterStands(stands: MapaStand[], query: string): MapaStand[] {
  const q = fold(query);
  if (!q) return stands;
  const qk = normalizeStandCode(query);
  return stands.filter(
    (s) =>
      (qk && s.key.startsWith(qk)) ||
      fold(s.codigo).includes(q) ||
      (s.nombre !== null && fold(s.nombre).includes(q)),
  );
}

function fold(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
}

export const PABELLON_LABEL: Record<string, string> = {
  azul: "Pabellón Azul",
  blanco: "Pabellón Blanco",
  amarillo: "Pabellón Amarillo",
  rojo: "Pabellón Rojo",
  verde: "Pabellón Verde",
  comidas: "Zona de Comidas",
  plazoleta: "Plazoleta Interamericana",
  gran_salon: "Gran Salón",
};

/**
 * Busca en el mapa el stand de un código dado (p. ej. el `?stand=` de la
 * ficha del directorio). Cruza por código normalizado, así "A 05", "a05" y
 * "A5" dan el mismo stand. undefined si el código no está en el plano.
 */
export function findStandByCode(
  stands: MapaStand[],
  code: string | null | undefined,
): MapaStand | undefined {
  const k = normalizeStandCode(code);
  if (!k) return undefined;
  return stands.find((s) => s.key === k);
}

/** Link al mapa enfocado en un stand; null si no hay código. */
export function mapaStandHref(code: string | null | undefined): string | null {
  const c = (code ?? "").trim();
  return c ? `/mapa?stand=${encodeURIComponent(c)}` : null;
}

/** Id de etiqueta de un lugar (pin numerado del plano). */
export const pinLabelId = (n: number) => `pin-${n}`;
/** Id de etiqueta de un stand (clave normalizada del plano). */
export const standLabelId = (key: string) => `st-${key}`;

/**
 * Etiquetas visibles dado el elegido: si hay una etiqueta seleccionada que
 * existe entre las candidatas, es la ÚNICA visible (las demás estorban); si no
 * hay selección (o no está entre las candidatas), se ven todas.
 */
export function visibleLabelIds(
  ids: string[],
  selectedId: string | null | undefined,
): string[] {
  if (selectedId && ids.includes(selectedId)) return [selectedId];
  return ids;
}

/* ------------------------------------------------------------------ recorrido guiado */

/** Clave de `app_config` con el orden del recorrido (nombres de pines separados por coma). */
export const MAPA_RECORRIDO_KEY = "mapa_recorrido";

/**
 * Orden por defecto: ingreso → taquillas → multipropósito → gran salón → lobby.
 * Son nombres (o el inicio del nombre) de pines de datos.json, sin tildes.
 * Un "*" suma al final los pines restantes por número.
 */
export const MAPA_RECORRIDO_DEFAULT = [
  "ingreso principal",
  "taquillas",
  "multiproposito",
  "gran salon",
  "lobby",
] as const;

/** Convierte el valor de app_config (texto con comas o lista) en nombres; vacío → default. */
export function parseRecorrido(value: unknown): string[] {
  const raw = Array.isArray(value)
    ? value.map(String)
    : typeof value === "string"
      ? value.split(",")
      : [];
  const out = raw.map((s) => s.trim()).filter(Boolean);
  return out.length ? out : [...MAPA_RECORRIDO_DEFAULT];
}

export type RecorridoResuelto = {
  /** Pines en el orden del recorrido, sin repetir. */
  pasos: MapaPin[];
  /** Entradas de la lista que no coinciden con ningún pin (para avisar al admin). */
  noEncontrados: string[];
};

/**
 * Resuelve la lista de nombres contra los pines. Cada entrada puede ser el
 * número del pin ("4") o un texto: gana el pin cuyo nombre (sin tildes, en
 * minúsculas) empieza por el texto, luego el que lo contiene; empata el de
 * menor número. Un pin no se repite. "*" agrega los pines que falten.
 */
export function ordenRecorrido(
  pines: MapaPin[],
  orden: readonly string[],
): RecorridoResuelto {
  const porN = [...pines].sort((a, b) => a.n - b.n);
  const usados = new Set<number>();
  const pasos: MapaPin[] = [];
  const noEncontrados: string[] = [];
  for (const entrada of orden) {
    if (entrada.trim() === "*") {
      for (const p of porN) {
        if (!usados.has(p.n)) {
          usados.add(p.n);
          pasos.push(p);
        }
      }
      continue;
    }
    const t = fold(entrada);
    if (!t) continue;
    const libres = porN.filter((p) => !usados.has(p.n));
    const hit = /^\d+$/.test(t)
      ? libres.find((p) => p.n === Number(t))
      : (libres.find((p) => fold(p.nombre).startsWith(t)) ??
        libres.find((p) => fold(p.nombre).includes(t)));
    if (hit) {
      usados.add(hit.n);
      pasos.push(hit);
    } else if (
      !porN.some((p) => usados.has(p.n) && fold(p.nombre).includes(t))
    ) {
      noEncontrados.push(entrada);
    }
  }
  return { pasos, noEncontrados };
}

/** Texto corto del paso: "1/5 · Ingreso principal" (nombre hasta el primer " · "). */
export function textoPasoRecorrido(
  i: number,
  total: number,
  nombre: string,
): string {
  return `${i + 1}/${total} · ${nombre.split(" · ")[0]}`;
}

/** Siguiente índice del recorrido; null = se pasó del extremo (fin o inicio). */
export function pasoVecino(
  i: number,
  total: number,
  delta: 1 | -1,
): number | null {
  const j = i + delta;
  return j < 0 || j >= total ? null : j;
}

/** Pin que se destaca al quitar el techo (modo niveles): la Zona IA. */
export function esPinZonaIA(p: Pick<MapaPin, "nombre">): boolean {
  return /^zona ia\b/.test(fold(p.nombre));
}
