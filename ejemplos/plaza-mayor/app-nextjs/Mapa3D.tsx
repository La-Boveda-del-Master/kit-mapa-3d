"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  ChevronLeft,
  ChevronRight,
  Grid2x2,
  Home,
  Layers,
  LocateFixed,
  MapPin,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  Route,
  RotateCw,
  Search,
  Store,
  X,
} from "lucide-react";
import type * as THREE from "three";
import type { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { cn } from "@/lib/cn";
import {
  esPinZonaIA,
  filterStands,
  findStandByCode,
  ordenRecorrido,
  pasoVecino,
  textoPasoRecorrido,
  pinLabelId,
  standLabelId,
  visibleLabelIds,
  mergeStands,
  MAPA_RECORRIDO_DEFAULT,
  PABELLON_LABEL,
  type MapaDatos,
  type MapaPin,
  type MapaStand,
  type StandPublico,
} from "@/lib/mapa3d";
import {
  dentroDelRecinto,
  distanciaAlRecinto,
  gpsAPlano,
  textoDistancia,
} from "@/lib/geo";
import {
  type ErrorUbicacion,
  type Ubicacion,
  vigilarUbicacion,
} from "@/lib/platform/geolocation";
import { snapToGrid } from "@/lib/analytics";
import { track } from "@/lib/platform/analytics";

/**
 * Mapa 3D navegable del recinto (modelo a escala del plano técnico).
 *
 * El visor va embebido y arranca al abrir la pestaña Mapa: ocupa el alto
 * visible entre el header y el BottomNav y se redimensiona con su contenedor.
 * El botón de pantalla completa lo expande a todo el dispositivo (Esc o el
 * mismo botón para volver); el ResizeObserver del marco reajusta el render.
 * Arrastrar gira, pellizco o rueda acerca. Dos modos: Exterior (todo en su sitio) y Por niveles (las
 *   cubiertas se quitan y los pisos superpuestos flotan para ver los de
 *   abajo). Dos capas de pines: Lugares (auditorios, ingresos, zonas) y
 *   Stands (cada stand del plano cruzado con stands_publico: nombre y logo).
 *
 * three.js se carga con import() dinámico dentro del efecto: no entra al
 * bundle inicial de la app y nunca corre en el servidor.
 */

// ?v= : súbelo cuando se reemplace mapa.glb/datos.json en la misma ruta.
const VER = "9";
const BASE = "/mapa3d";
const HORIZONTE = 0xd3dfeb;
const RAIZ_DE: Record<string, string> = {
  sup: "sup",
  multi: "multi",
  caja: "caja",
  shell: "shell",
};
const OCULTOS: Record<string, string[]> = {
  exterior: ["guias", "huella"],
  niveles: ["ext_base", "ext_sup", "losa"],
};
const PAB_COLOR: Record<string, string> = {
  azul: "#2f6fd9",
  blanco: "#8c8f96",
  amarillo: "#e2b414",
  rojo: "#d7352b",
  verde: "#5aa832",
  comidas: "#ef8a2a",
  plazoleta: "#9b6bb5",
  gran_salon: "#9a7a5a",
};

type Modo = "exterior" | "niveles";
type Capa = "lugares" | "stands";
type Sel = { tipo: "pin"; n: number } | { tipo: "stand"; key: string } | null;

type Escena = {
  three: typeof THREE;
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camara: THREE.PerspectiveCamera;
  controles: OrbitControls;
  raices: Record<string, THREE.Object3D | undefined>;
  porGrupo: Record<string, THREE.Object3D[]>;
  lift: Record<string, number>;
  centro: THREE.Vector3;
  anim: { paso: (t: number) => boolean } | null;
  sucio: boolean;
  libre: number;
  datos: MapaDatos | null;
  /** Varilla de cada marcador (anclan el pin al sitio exacto): "pin-N" lugares, "st-KEY" stands. */
  varillas: Record<string, THREE.Object3D>;
  /** Marcador "Mi ubicación": punto azul + anillo de precisión a nivel del suelo. */
  ubic: { grupo: THREE.Group; anillo: THREE.Mesh } | null;
};

/** Piso de cada grupo de nivel (m): de ahí arranca la varilla de cada pin. */
const PISO_GRUPO: Record<string, number> = {
  base: 0,
  inf: 0,
  sup: 11,
  multi: 0,
  gs: -4.5,
  caja: 4.5,
};

function srgb(c: [number, number, number]): string {
  return (
    "#" +
    c
      .map((v) =>
        Math.round(Math.pow(v, 1 / 2.2) * 255)
          .toString(16)
          .padStart(2, "0"),
      )
      .join("")
  );
}

/** prefers-reduced-motion: la cámara salta sin vuelo y el recorrido no avanza solo. */
const movimientoReducido = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;
/** Tiempo en cada parada del recorrido guiado (ms). */
const PARADA_MS = 6500;

const suave = (k: number) =>
  k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;

export default function Mapa3D({
  standsDb,
  venueName,
  initialStand = null,
  recorridoCfg = [],
}: {
  standsDb: StandPublico[];
  venueName: string;
  /** Código de stand (`?stand=`) a resaltar al abrir el mapa. */
  initialStand?: string | null;
  /** Orden del recorrido guiado (app_config `mapa_recorrido`, ya parseado). */
  recorridoCfg?: string[];
}) {
  /** Marco del visor: ocupa el alto visible entre el header y el BottomNav de la app. */
  const marco = useRef<HTMLDivElement>(null);
  /** Área de la escena (canvas + pines + controles): la hoja inferior va debajo, sin tapar el mapa. */
  const escena = useRef<HTMLDivElement>(null);
  const [cargando, setCargando] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<MapaDatos | null>(null);
  const [modo, setModo] = useState<Modo>("exterior");
  const [capa, setCapa] = useState<Capa>("lugares");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<Sel>(null);
  const [girando, setGirando] = useState(false);
  /** Recorrido guiado: índice del paso y si está en pausa. null = apagado. */
  const [tour, setTour] = useState<{ i: number; pausa: boolean } | null>(null);
  const [listaAbierta, setListaAbierta] = useState(false);
  /** "Mi ubicación": seguimiento GPS activo, último fix y aviso para el usuario. */
  const [siguiendo, setSiguiendo] = useState(false);
  const [avisoUbic, setAvisoUbic] = useState<string | null>(null);
  /** Aviso si el stand pedido por `?stand=` no está en el plano. */
  const [avisoStand, setAvisoStand] = useState<string | null>(null);
  const standInicialHecho = useRef(false);
  const pararUbic = useRef<(() => void) | null>(null);
  const primerFix = useRef(true);
  /** Muestreo anónimo de posición (apagado salvo `analytics_location_sampling`). */
  const muestreo = useRef({ activo: false, ultimo: 0 });
  useEffect(() => () => pararUbic.current?.(), []);

  /** Pantalla completa: el marco pasa a cubrir el dispositivo (tapa header y BottomNav). */
  const [completa, setCompleta] = useState(false);
  useEffect(() => {
    if (!completa) return;
    track("map_fullscreen", {});
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") setCompleta(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [completa]);

  const lienzo = useRef<HTMLCanvasElement>(null);
  const capaPines = useRef<HTMLDivElement>(null);
  const esc = useRef<Escena | null>(null);
  const modoRef = useRef<Modo>("exterior");
  const pinEls = useRef(new Map<string, HTMLButtonElement>());

  const stands = useMemo(
    () => (datos ? mergeStands(datos.stands, standsDb) : []),
    [datos, standsDb],
  );
  const standsFiltrados = useMemo(() => filterStands(stands, q), [stands, q]);
  const standSel =
    sel?.tipo === "stand" ? stands.find((s) => s.key === sel.key) : undefined;
  const pinSel =
    sel?.tipo === "pin" ? datos?.pines.find((p) => p.n === sel.n) : undefined;

  /* ------------------------------------------------------------ escena */
  useEffect(() => {
    if (!lienzo.current || !escena.current) return;
    let vivo = true;
    let raf = 0;
    const canvas = lienzo.current;
    const cont = escena.current;
    let ro: ResizeObserver | undefined;

    (async () => {
      try {
        const [
          three,
          { OrbitControls },
          { GLTFLoader },
          { DRACOLoader },
          { RoomEnvironment },
        ] = await Promise.all([
          import("three"),
          import("three/examples/jsm/controls/OrbitControls.js"),
          import("three/examples/jsm/loaders/GLTFLoader.js"),
          import("three/examples/jsm/loaders/DRACOLoader.js"),
          import("three/examples/jsm/environments/RoomEnvironment.js"),
        ]);
        if (!vivo) return;
        const tactil = window.matchMedia("(pointer: coarse)").matches;
        const renderer = new three.WebGLRenderer({
          canvas,
          antialias: true,
          powerPreference: "high-performance",
        });
        renderer.setPixelRatio(
          Math.min(window.devicePixelRatio, tactil ? 1.5 : 2),
        );
        renderer.toneMapping = three.ACESFilmicToneMapping;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = three.PCFSoftShadowMap;
        renderer.shadowMap.autoUpdate = false;

        const scene = new three.Scene();
        scene.fog = new three.Fog(HORIZONTE, 1100, 4200);
        scene.environment = new three.PMREMGenerator(renderer).fromScene(
          new RoomEnvironment(),
          0.04,
        ).texture;
        scene.environmentIntensity = 0.35;
        scene.add(
          new three.Mesh(
            new three.SphereGeometry(4000, 32, 16),
            new three.ShaderMaterial({
              side: three.BackSide,
              depthWrite: false,
              fog: false,
              uniforms: {
                h: { value: new three.Color(HORIZONTE) },
                c: { value: new three.Color(0x3f7fd6) },
              },
              vertexShader:
                "varying float y; void main(){ y = normalize(position).y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
              fragmentShader:
                "uniform vec3 h; uniform vec3 c; varying float y; void main(){ gl_FragColor = vec4(mix(h, c, smoothstep(0.0, 0.55, y)), 1.0); }",
            }),
          ),
        );
        const lejos = new three.Mesh(
          new three.PlaneGeometry(9000, 9000),
          new three.MeshLambertMaterial({ color: 0xa9aaa6 }),
        );
        lejos.rotation.x = -Math.PI / 2;
        lejos.position.y = -9.8;
        scene.add(lejos);
        scene.add(new three.HemisphereLight(0xdfeaff, 0x8a8372, 1.15));
        const centro = new three.Vector3(-10, 0, -75);
        const sol = new three.DirectionalLight(0xfff1dc, 2.6);
        sol.position.copy(centro).add(new three.Vector3(230, 330, 170));
        sol.target.position.copy(centro);
        sol.castShadow = true;
        sol.shadow.mapSize.setScalar(tactil ? 2048 : 4096);
        Object.assign(sol.shadow.camera, {
          left: -330,
          right: 330,
          top: 330,
          bottom: -330,
          near: 50,
          far: 1100,
        });
        sol.shadow.bias = -0.0004;
        sol.shadow.normalBias = 0.6;
        scene.add(sol, sol.target);

        const camara = new three.PerspectiveCamera(36, 1, 2, 6000);
        const controles = new OrbitControls(camara, canvas);
        Object.assign(controles, {
          enableDamping: true,
          dampingFactor: 0.08,
          minDistance: 22,
          maxDistance: 1700,
          maxPolarAngle: 1.47,
          zoomToCursor: true,
          autoRotateSpeed: 0.7,
          screenSpacePanning: false,
        });

        const e: Escena = {
          three,
          renderer,
          scene,
          camara,
          controles,
          raices: {},
          porGrupo: {},
          lift: {},
          centro,
          anim: null,
          sucio: true,
          libre: 1,
          datos: null,
          varillas: {},
          ubic: null,
        };
        esc.current = e;

        const ajustar = () => {
          const w = cont.clientWidth;
          const h = cont.clientHeight;
          if (w < 50 || h < 50) return;
          renderer.setSize(w, h, false);
          camara.aspect = w / h;
          camara.updateProjectionMatrix();
          e.libre = w / h;
          e.sucio = true;
        };
        ajustar();
        ro = new ResizeObserver(ajustar);
        ro.observe(cont);
        const ini = vistaInicial(e);
        camara.position.copy(ini.pos);
        controles.target.copy(ini.obj);
        controles.update();
        controles.addEventListener("change", () => {
          e.sucio = true;
        });

        const d = (await (
          await fetch(`${BASE}/datos.json?v=${VER}`)
        ).json()) as MapaDatos;
        if (!vivo) return;
        e.lift = Object.fromEntries(Object.keys(d.lift).map((k) => [k, 0]));
        const draco = new DRACOLoader().setDecoderPath(`${BASE}/draco/`);
        const gltf = await new GLTFLoader()
          .setDRACOLoader(draco)
          .loadAsync(`${BASE}/mapa.glb?v=${VER}`, (ev) => {
            setCargando(Math.min(96, (ev.loaded / (ev.total || 6.7e6)) * 100));
          });
        if (!vivo) return;
        const anis = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        gltf.scene.traverse((o) => {
          const g = (o.userData as { grupo?: string }).grupo;
          if (g) (e.porGrupo[g] ||= []).push(o);
          if (!(o as THREE.Mesh).isMesh) return;
          const m = (o as THREE.Mesh).material as THREE.MeshStandardMaterial;
          o.castShadow = !m.transparent;
          o.receiveShadow = true;
          if (m.transparent) m.depthWrite = false;
          for (const t of [m.map, m.normalMap]) if (t) t.anisotropy = anis;
        });
        for (const [k, nombre] of Object.entries(d.raices))
          e.raices[k] = gltf.scene.getObjectByName(nombre);
        scene.add(gltf.scene);
        renderer.shadowMap.needsUpdate = true;
        guardarDatos(e, d);
        crearVarillas(e, d);
        setDatos(d);
        aplicarVisibilidad(e, modoRef.current);
        setCargando(100);
        track("map_open", { stands: d.stands.length, lugares: d.pines.length });

        const bucle = (ahora: number) => {
          if (!vivo) return;
          raf = requestAnimationFrame(bucle);
          if (e.anim) {
            if (!e.anim.paso(ahora)) e.anim = null;
            e.sucio = true;
          }
          if (controles.update()) e.sucio = true;
          if (!e.sucio) return;
          e.sucio = false;
          renderer.render(scene, camara);
          ubicarPines(e, pinEls.current, capaPines.current);
        };
        raf = requestAnimationFrame(bucle);
      } catch (err) {
        console.error(err);
        if (vivo)
          setError(
            "No se pudo cargar el mapa 3D. Revisa tu conexión e inténtalo de nuevo.",
          );
      }
    })();

    return () => {
      vivo = false;
      cancelAnimationFrame(raf);
      ro?.disconnect();
      const e = esc.current;
      if (e) {
        e.controles.dispose();
        e.renderer.dispose();
        esc.current = null;
      }
      setDatos(null);
      setCargando(0);
      setSel(null);
      setQ("");
      setCapa("lugares");
      setModo("exterior");
      modoRef.current = "exterior";
    };
  }, []);

  /* ------------------------------------------------------------ acciones */
  const ponerModo = useCallback((nuevo: Modo) => {
    const e = esc.current;
    if (!e || nuevo === modoRef.current) return;
    modoRef.current = nuevo;
    setModo(nuevo);
    track("map_mode", { mode: nuevo });
    if (nuevo === "niveles") aplicarVisibilidad(e, nuevo);
    else ocultarGuias(e);
    sombrasNivelesFlotantes(e, nuevo === "exterior");
    const ini = { ...e.lift };
    const fin: Record<string, number> = {};
    const d = e.datos;
    for (const k of Object.keys(e.lift))
      fin[k] = nuevo === "niveles" ? (d?.lift[k] ?? 0) : 0;
    animar(
      e,
      movimientoReducido() ? 1 : 1200,
      (k) => {
        for (const key of Object.keys(e.lift)) {
          e.lift[key] = ini[key] + (fin[key] - ini[key]) * k;
          const r = e.raices[key];
          if (r) r.position.y = e.lift[key];
        }
        e.renderer.shadowMap.needsUpdate = true;
      },
      () => {
        aplicarVisibilidad(e, nuevo);
        e.renderer.shadowMap.needsUpdate = true;
      },
    );
  }, []);

  const volarA = useCallback(
    (
      pos: [number, number, number],
      grupo: string,
      dist: number,
      dur?: number,
    ) => {
      const e = esc.current;
      const d = e?.datos;
      if (!e || !d) return;
      const bajo = ["inf", "gs", "multi", "caja"].includes(grupo);
      if (bajo && modoRef.current !== "niveles") ponerModo("niveles");
      const lift =
        modoRef.current === "niveles" || bajo
          ? (d.lift[RAIZ_DE[grupo] ?? ""] ?? 0)
          : 0;
      const obj = new e.three.Vector3(pos[0], pos[2] + lift - 4, -pos[1]);
      const dir = e.camara.position.clone().sub(e.controles.target).normalize();
      if (dir.y < 0.45) {
        dir.y = 0.45;
        dir.normalize();
      }
      volar(e, obj.clone().add(dir.multiplyScalar(dist)), obj, dur);
      e.controles.autoRotate = false;
      setGirando(false);
    },
    [ponerModo],
  );

  const elegirPin = useCallback(
    (p: MapaPin, via: "pin" | "lista" | "recorrido" = "pin") => {
      if (via !== "recorrido") setTour(null);
      setSel({ tipo: "pin", n: p.n });
      setListaAbierta(false);
      volarA(p.pos, p.grupo, 170, movimientoReducido() ? 1 : undefined);
      track("map_place_select", {
        n: String(p.n),
        nombre: p.nombre,
        nivel: p.nivel,
        via,
      });
    },
    [volarA],
  );

  /** Recorrido ordenado de los lugares: ±1 desde el pin elegido (circular); sin selección arranca en el 1. */
  const pinesOrden = useMemo(
    () => [...(datos?.pines ?? [])].sort((a, b) => a.n - b.n),
    [datos],
  );
  const irPin = useCallback(
    (delta: 1 | -1) => {
      if (!pinesOrden.length) return;
      const i = pinesOrden.findIndex(
        (p) => sel?.tipo === "pin" && p.n === sel.n,
      );
      const j =
        i < 0
          ? delta > 0
            ? 0
            : pinesOrden.length - 1
          : (i + delta + pinesOrden.length) % pinesOrden.length;
      elegirPin(pinesOrden[j], "recorrido");
    },
    [pinesOrden, sel, elegirPin],
  );

  /* Recorrido guiado: orden desde app_config (con default en lib/mapa3d). */
  const recorrido = useMemo(
    () =>
      ordenRecorrido(
        datos?.pines ?? [],
        recorridoCfg.length ? recorridoCfg : MAPA_RECORRIDO_DEFAULT,
      ).pasos,
    [datos, recorridoCfg],
  );
  const irPaso = useCallback(
    (i: number) => {
      const p = recorrido[i];
      if (!p) return;
      setCapa("lugares");
      setTour((t) => ({ i, pausa: t ? t.pausa : movimientoReducido() }));
      elegirPin(p, "recorrido");
    },
    [recorrido, elegirPin],
  );
  const vecinoPaso = (delta: 1 | -1) => {
    if (!tour) return;
    const j = pasoVecino(tour.i, recorrido.length, delta);
    if (j !== null) irPaso(j);
  };
  // Avance automático (con prefers-reduced-motion arranca en pausa). Al llegar
  // a la última parada se detiene ahí.
  useEffect(() => {
    if (!tour || tour.pausa) return;
    const id = setTimeout(() => {
      const j = pasoVecino(tour.i, recorrido.length, 1);
      if (j === null) setTour({ i: tour.i, pausa: true });
      else irPaso(j);
    }, PARADA_MS);
    return () => clearTimeout(id);
  }, [tour, recorrido, irPaso]);

  const elegirStand = useCallback(
    (s: MapaStand, via: "pin" | "lista" = "pin") => {
      setTour(null);
      setSel({ tipo: "stand", key: s.key });
      setListaAbierta(false);
      volarA([s.pos[0], s.pos[1], s.pos[2] + s.alto], s.grupo, 60);
      track("map_stand_select", {
        codigo: s.codigo,
        nombre: s.nombre,
        pabellon: s.pabellon,
        vendido: s.nombre !== null,
        via,
      });
    },
    [volarA],
  );

  // Deep link `?stand=CODIGO`: al cargar el plano se activa la capa de stands,
  // se selecciona el stand y la cámara vuela hasta él. Una sola vez.
  useEffect(() => {
    if (!initialStand || !datos || standInicialHecho.current) return;
    const t = setTimeout(() => {
      standInicialHecho.current = true;
      const s = findStandByCode(stands, initialStand);
      if (!s) {
        setAvisoStand(
          `El stand ${initialStand} no aparece en el mapa todavía.`,
        );
        return;
      }
      setCapa("stands");
      elegirStand(s, "lista");
    }, 0);
    return () => clearTimeout(t);
  }, [initialStand, datos, stands, elegirStand]);

  useEffect(() => {
    if (!avisoStand) return;
    const t = setTimeout(() => setAvisoStand(null), 6000);
    return () => clearTimeout(t);
  }, [avisoStand]);

  // Búsquedas de stand: se registra el texto final (tras 1,2 s sin teclear),
  // con cuántos resultados dio — las búsquedas sin resultado son oro para
  // saber qué marca esperaba encontrar la gente.
  const nResultados = standsFiltrados.length;
  useEffect(() => {
    const texto = q.trim();
    if (texto.length < 2) return;
    const id = setTimeout(
      () => track("map_stand_search", { q: texto, results: nResultados }),
      1200,
    );
    return () => clearTimeout(id);
  }, [q, nResultados]);

  const vistaCasa = () => {
    const e = esc.current;
    if (!e) return;
    const i = vistaInicial(e);
    volar(e, i.pos, i.obj);
  };
  const vistaPlanta = () => {
    const e = esc.current;
    if (!e) return;
    const o = e.controles.target.clone().setY(0);
    volar(
      e,
      o.clone().add(new e.three.Vector3(0.01, e.libre < 1 ? 950 : 650, 0)),
      o,
    );
  };
  const toggleGiro = () => {
    const e = esc.current;
    if (!e) return;
    e.controles.autoRotate = !e.controles.autoRotate;
    setGirando(e.controles.autoRotate);
  };

  const recibirUbicacion = useCallback(
    (u: Ubicacion) => {
      const e = esc.current;
      if (!e) return;
      const p = gpsAPlano(u.lat, u.lon);
      if (!dentroDelRecinto(p)) {
        ponerUbicacion(e, null);
        setAvisoUbic(
          `Estás a ${textoDistancia(distanciaAlRecinto(p))} de Plaza Mayor. El punto se mostrará cuando llegues al recinto.`,
        );
        if (primerFix.current) {
          primerFix.current = false;
          track("map_gps", { state: "fuera" });
        }
        return;
      }
      ponerUbicacion(e, { x: p.x, y: p.y, precision: u.precision });
      setAvisoUbic(
        u.precision > 25
          ? `Señal GPS débil (±${Math.round(u.precision)} m): dentro de los pabellones la posición es aproximada.`
          : null,
      );
      if (primerFix.current) {
        primerFix.current = false;
        volarA([p.x, p.y, 0], "base", 110);
        track("map_gps", {
          state: "dentro",
          precision: Math.round(u.precision),
        });
      }
      // Mapa de calor: celda de 5 m, como mucho una muestra cada 30 s, y solo
      // si el admin lo activó (exige política de privacidad actualizada).
      const m = muestreo.current;
      if (m.activo && u.precision <= 40 && u.ts - m.ultimo >= 30_000) {
        m.ultimo = u.ts;
        track("map_position", snapToGrid(p.x, p.y));
      }
    },
    [volarA],
  );
  const toggleUbicacion = () => {
    if (pararUbic.current) {
      pararUbic.current();
      pararUbic.current = null;
      setSiguiendo(false);
      setAvisoUbic(null);
      if (esc.current) ponerUbicacion(esc.current, null);
      return;
    }
    primerFix.current = true;
    setSiguiendo(true);
    setAvisoUbic("Buscando tu ubicación…");
    track("map_gps", { state: "solicitado" });
    void fetch("/api/app/tags")
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: { tags?: { locationSampling?: boolean } } | null) => {
        muestreo.current.activo = !!cfg?.tags?.locationSampling;
      })
      .catch(() => {});
    pararUbic.current = vigilarUbicacion(recibirUbicacion, (err) => {
      setAvisoUbic(TEXTO_ERROR_UBIC[err]);
      track("map_gps", { state: err });
      if (err !== "tiempo") {
        pararUbic.current?.();
        pararUbic.current = null;
        setSiguiendo(false);
      }
    });
  };

  const pinRef = (id: string) => (el: HTMLButtonElement | null) => {
    if (el) pinEls.current.set(id, el);
    else pinEls.current.delete(id);
  };

  /* ------------------------------------------------------------ render */
  const pinesCandidatos = datos
    ? capa === "lugares"
      ? datos.pines.filter(
          (p) =>
            modo === "niveles" ||
            ["base", "sup"].includes(p.grupo) ||
            p.n === 1,
        )
      : []
    : [];
  const standsCandidatos = capa === "stands" ? standsFiltrados : [];
  // Con una etiqueta elegida (toque, recorrido o ?stand=) solo se ve esa: las
  // demás estorban. Solo cambia visibilidad, no se recrea nada de three.js.
  const selId =
    sel?.tipo === "pin"
      ? pinLabelId(sel.n)
      : sel?.tipo === "stand"
        ? standLabelId(sel.key)
        : null;
  const visibles = new Set(
    visibleLabelIds(
      [
        ...pinesCandidatos.map((p) => pinLabelId(p.n)),
        ...standsCandidatos.map((s) => standLabelId(s.key)),
      ],
      selId,
    ),
  );
  // Sin techo (modo niveles) la Zona IA se destaca: siempre visible y con halo,
  // salvo durante el recorrido guiado (ahí solo se ve la parada actual).
  const iaDestacada = modo === "niveles" && !tour;
  const pinesVisibles = pinesCandidatos.filter(
    (p) => visibles.has(pinLabelId(p.n)) || (iaDestacada && esPinZonaIA(p)),
  );
  const standsVisibles = standsCandidatos.filter((s) =>
    visibles.has(standLabelId(s.key)),
  );
  const idsVisibles = [
    ...new Set([...visibles, ...pinesVisibles.map((p) => pinLabelId(p.n))]),
  ].join(" ");
  useEffect(() => {
    const e = esc.current;
    if (!e) return;
    mostrarVarillas(e, new Set(idsVisibles ? idsVisibles.split(" ") : []));
  }, [idsVisibles, datos]);

  return (
    <>
      <div
        ref={marco}
        data-no-track
        className={
          completa
            ? "fixed inset-0 z-50 flex flex-col overflow-hidden bg-[#cfdcea] text-[#101114]"
            : "relative flex h-[calc(100dvh-12.5rem-env(safe-area-inset-bottom))] min-h-[460px] w-full flex-col overflow-hidden rounded-[18px] border border-white/[0.12] bg-[#cfdcea] text-[#101114]"
        }
      >
        <div ref={escena} className="relative min-h-0 flex-1">
          <canvas
            ref={lienzo}
            className="absolute inset-0 h-full w-full touch-none outline-none"
            aria-label="Mapa 3D de la feria"
          />
          <div
            ref={capaPines}
            className="pointer-events-none absolute inset-0 overflow-hidden"
            aria-hidden
          >
            {pinesVisibles.map((p) => {
              const halo = iaDestacada && esPinZonaIA(p);
              return (
                <button
                  key={`pin-${p.n}`}
                  ref={pinRef(`pin-${p.n}`)}
                  type="button"
                  onClick={() => elegirPin(p)}
                  title={p.nombre}
                  data-pos={`${p.pos[0]},${p.pos[1]},${p.pos[2]},0`}
                  data-grupo={p.grupo}
                  className={cn(
                    "pointer-events-auto absolute left-0 top-0 -ml-4 -mt-[46px] h-[46px] w-8 opacity-0 drop-shadow-[0_3px_4px_rgba(0,0,0,.35)]",
                    sel?.tipo === "pin" && sel.n === p.n && "z-[5]",
                    halo && "z-[4]",
                  )}
                >
                  {halo && (
                    <>
                      <span className="absolute left-0 top-0 h-8 w-8 rounded-full bg-emerald-400/60 motion-safe:animate-ping" />
                      <span className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-extrabold text-white shadow">
                        Zona IA
                      </span>
                    </>
                  )}
                  {/* la posición se fija sin transición (si no, el pin se despega de su varilla al girar); solo escala el marcador elegido */}
                  <span
                    className={cn(
                      "block h-full w-full origin-bottom transition-transform",
                      sel?.tipo === "pin" && sel.n === p.n && "scale-125",
                    )}
                  >
                    <PinSvg color={srgb(p.color)} label={String(p.n)} />
                  </span>
                </button>
              );
            })}
            {standsVisibles.map((s) => {
              const activo = sel?.tipo === "stand" && sel.key === s.key;
              return (
                <button
                  key={`st-${s.key}`}
                  ref={pinRef(`st-${s.key}`)}
                  type="button"
                  onClick={() => elegirStand(s)}
                  title={s.nombre ?? s.codigo}
                  data-pos={`${s.pos[0]},${s.pos[1]},${s.pos[2]},${s.alto + 0.4}`}
                  data-grupo={s.grupo}
                  className={cn(
                    "pointer-events-auto absolute left-0 top-0 -ml-[15px] -mt-[30px] h-[30px] min-w-[30px] opacity-0",
                    activo && "z-[5]",
                  )}
                >
                  {/* el pin se ancla por su borde inferior al extremo de la varilla; solo escala el elegido */}
                  <span
                    className={cn(
                      "flex h-full min-w-full origin-bottom items-center justify-center rounded-full border-2 px-1 text-[9px] font-extrabold text-white shadow-md transition-transform",
                      activo && "scale-125 ring-2 ring-black/40",
                      s.logo ? "bg-white" : "border-white",
                    )}
                    style={{
                      background: s.logo
                        ? "#fff"
                        : (PAB_COLOR[s.pabellon] ?? "#444"),
                      borderColor: s.logo
                        ? (PAB_COLOR[s.pabellon] ?? "#444")
                        : undefined,
                    }}
                  >
                    {s.logo ? <LogoPin src={s.logo} /> : s.codigo}
                  </span>
                </button>
              );
            })}
          </div>

          {/* cabecera */}
          <div
            className={`pointer-events-none absolute left-0 right-0 top-0 z-10 flex items-start justify-between gap-2 p-3 ${
              completa ? "pt-[calc(env(safe-area-inset-top)+12px)]" : ""
            }`}
          >
            {/* Tarjeta del mapa y, debajo (nunca encima), "Ver todas". */}
            <div className="pointer-events-auto flex flex-col items-start gap-2">
              <div className="rounded-2xl border-l-4 border-[#e11d2a] bg-[#101114] px-3 py-2 text-white shadow-lg">
                <div className="text-[13px] font-extrabold tracking-wide">
                  MAPA 3D
                </div>
                <div className="text-[10px] opacity-75">{venueName}</div>
              </div>
              {sel && (
                <button
                  type="button"
                  onClick={() => {
                    setTour(null);
                    setSel(null);
                  }}
                  className="rounded-full bg-white/95 px-3 py-1.5 text-[12px] font-bold text-[#101114] shadow-lg"
                >
                  Ver todas las etiquetas
                </button>
              )}
            </div>
            <div className="pointer-events-auto flex flex-col items-end gap-2">
              <button
                type="button"
                onClick={() => setCompleta((v) => !v)}
                aria-label={
                  completa ? "Salir de pantalla completa" : "Pantalla completa"
                }
                aria-pressed={completa}
                className="grid h-11 w-11 place-items-center rounded-full bg-[#101114] text-white shadow-lg active:scale-95"
              >
                {completa ? (
                  <Minimize2 className="h-5 w-5" />
                ) : (
                  <Maximize2 className="h-5 w-5" />
                )}
              </button>
              {/* modo: exterior / por niveles */}
              <div
                role="tablist"
                aria-label="Modo de vista"
                className="flex rounded-full bg-white/95 p-1 shadow-lg"
              >
                <SegIcono
                  on={modo === "exterior"}
                  label="Exterior"
                  onClick={() => ponerModo("exterior")}
                >
                  <Box className="h-[18px] w-[18px]" />
                </SegIcono>
                <SegIcono
                  on={modo === "niveles"}
                  label="Por niveles"
                  onClick={() => ponerModo("niveles")}
                >
                  <Layers className="h-[18px] w-[18px]" />
                </SegIcono>
              </div>
              {/* capa: lugares / stands */}
              <div
                role="tablist"
                aria-label="Capa de pines"
                className="flex rounded-full bg-white/95 p-1 shadow-lg"
              >
                <SegIcono
                  on={capa === "lugares"}
                  label="Lugares"
                  onClick={() => {
                    setCapa("lugares");
                    setTour(null);
                    setSel(null);
                    track("map_layer", { layer: "lugares" });
                  }}
                >
                  <MapPin className="h-[18px] w-[18px]" />
                </SegIcono>
                <SegIcono
                  on={capa === "stands"}
                  label="Stands"
                  onClick={() => {
                    setCapa("stands");
                    setTour(null);
                    setSel(null);
                    setListaAbierta(true);
                    track("map_layer", { layer: "stands" });
                  }}
                >
                  <Store className="h-[18px] w-[18px]" />
                </SegIcono>
              </div>
            </div>
          </div>

          {/* controles izquierda */}
          <div className="absolute bottom-3 left-3 z-10 flex flex-col gap-2">
            <Ctl onClick={vistaCasa} label="Vista inicial">
              <Home className="h-5 w-5" />
            </Ctl>
            <Ctl
              onClick={toggleGiro}
              label="Recorrido automático"
              activo={girando}
            >
              <RotateCw className="h-5 w-5" />
            </Ctl>
            {recorrido.length > 0 && (
              <Ctl
                onClick={() => (tour ? setTour(null) : irPaso(0))}
                label={tour ? "Salir del recorrido guiado" : "Recorrido guiado"}
                activo={!!tour}
              >
                <Route className="h-5 w-5" />
              </Ctl>
            )}
            <Ctl onClick={vistaPlanta} label="Vista desde arriba">
              <Grid2x2 className="h-5 w-5" />
            </Ctl>
            <Ctl
              onClick={toggleUbicacion}
              label={
                siguiendo ? "Dejar de seguir mi ubicación" : "Mi ubicación"
              }
              activo={siguiendo}
            >
              <LocateFixed className="h-5 w-5" />
            </Ctl>
          </div>


          {avisoStand && (
            <div
              role="status"
              className="pointer-events-none absolute left-3 right-3 top-14 z-10 rounded-2xl bg-[#101114]/90 px-3 py-2 text-[12px] leading-snug text-white shadow-lg"
            >
              {avisoStand}
            </div>
          )}

          {/* aviso de ubicación (GPS) */}
          {avisoUbic && (
            <div
              role="status"
              className="pointer-events-none absolute bottom-3 left-[68px] right-3 z-10 rounded-2xl bg-[#101114]/90 px-3 py-2 text-[12px] leading-snug text-white shadow-lg"
            >
              {avisoUbic}
            </div>
          )}
        </div>

        {/* hoja inferior: buscador + ficha + lista (debajo de la escena, no encima) */}
        <div
          className={`relative z-10 flex max-h-[62%] shrink-0 flex-col rounded-t-[18px] bg-white shadow-[0_-6px_24px_rgba(10,12,20,.18)] ${
            completa ? "pb-[env(safe-area-inset-bottom)]" : ""
          }`}
        >
          <button
            type="button"
            onClick={() => setListaAbierta((v) => !v)}
            className="flex flex-col items-center gap-1.5 px-4 pb-2 pt-2 text-[13.5px] font-bold"
            aria-expanded={listaAbierta}
          >
            <span className="h-1 w-9 rounded-full bg-black/20" />
            {capa === "stands" ? "Buscar stand" : "Lugares de la feria"}
          </button>

          {capa === "stands" && (
            <div className="flex items-center gap-2 px-4 pb-2">
              <Search className="h-4 w-4 shrink-0 text-[#62646b]" />
              <input
                value={q}
                onChange={(ev) => {
                  setQ(ev.target.value);
                  setListaAbierta(true);
                }}
                placeholder="Código o nombre de la empresa…"
                className="w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[13px] outline-none focus:border-black/30"
                inputMode="search"
                autoComplete="off"
              />
            </div>
          )}

          {!listaAbierta && standSel && <StandFicha s={standSel} />}
          {!listaAbierta && capa === "lugares" && tour && recorrido[tour.i] && (
            <div className="flex items-center gap-2 px-3 pb-3">
              <button
                type="button"
                onClick={() => vecinoPaso(-1)}
                disabled={tour.i === 0}
                aria-label="Parada anterior"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#101114] text-white shadow active:scale-95 disabled:opacity-30"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={() => setTour({ ...tour, pausa: !tour.pausa })}
                aria-label={
                  tour.pausa ? "Reanudar recorrido" : "Pausar recorrido"
                }
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#e11d2a] text-white shadow active:scale-95"
              >
                {tour.pausa ? (
                  <Play className="h-5 w-5" />
                ) : (
                  <Pause className="h-5 w-5" />
                )}
              </button>
              <div role="status" aria-live="polite" className="min-w-0 flex-1">
                <b className="block truncate text-[13px]">
                  {textoPasoRecorrido(
                    tour.i,
                    recorrido.length,
                    recorrido[tour.i].nombre,
                  )}
                </b>
                <small className="block truncate text-[11.5px] text-[#62646b]">
                  {recorrido[tour.i].detalle}
                </small>
              </div>
              <button
                type="button"
                onClick={() => vecinoPaso(1)}
                disabled={tour.i >= recorrido.length - 1}
                aria-label="Parada siguiente"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#101114] text-white shadow active:scale-95 disabled:opacity-30"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={() => setTour(null)}
                aria-label="Salir del recorrido"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-black/[.08] active:scale-95"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
          {!listaAbierta && capa === "lugares" && !tour && (
            <div className="flex items-center gap-2 px-3 pb-3">
              <button
                type="button"
                onClick={() => irPin(-1)}
                aria-label="Punto anterior"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#101114] text-white shadow active:scale-95"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              {pinSel ? (
                <div className="grid min-w-0 flex-1 grid-cols-[30px_1fr] items-center gap-x-2.5">
                  <span
                    className="row-span-2 grid h-[30px] w-[30px] place-items-center rounded-full text-[13px] font-extrabold text-white"
                    style={{ background: srgb(pinSel.color) }}
                  >
                    {pinSel.n}
                  </span>
                  <b className="truncate text-[13px]">{pinSel.nombre}</b>
                  <small className="truncate text-[11.5px] text-[#62646b]">
                    {pinSel.detalle} ·{" "}
                    <span
                      className="font-bold uppercase"
                      style={{ color: srgb(pinSel.color) }}
                    >
                      {pinSel.nivel}
                    </span>
                  </small>
                </div>
              ) : (
                <div className="min-w-0 flex-1 text-center text-[12.5px] text-[#62646b]">
                  {recorrido.length > 0 ? (
                    <button
                      type="button"
                      onClick={() => irPaso(0)}
                      className="rounded-full bg-[#e11d2a] px-3 py-1.5 text-[12.5px] font-bold text-white active:scale-95"
                    >
                      Iniciar recorrido guiado ({recorrido.length} paradas)
                    </button>
                  ) : (
                    <>Recorre los {pinesOrden.length} puntos en orden</>
                  )}
                </div>
              )}
              <button
                type="button"
                onClick={() => irPin(1)}
                aria-label="Punto siguiente"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#101114] text-white shadow active:scale-95"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          )}

          {listaAbierta && (
            <ol className="overflow-y-auto overscroll-contain px-2 pb-2">
              {capa === "lugares" &&
                datos?.pines.map((p) => (
                  <li key={p.n}>
                    <button
                      type="button"
                      onClick={() => elegirPin(p, "lista")}
                      className={cn(
                        "grid w-full grid-cols-[34px_1fr] items-center gap-x-2.5 rounded-xl px-2.5 py-2 text-left",
                        sel?.tipo === "pin" &&
                          sel.n === p.n &&
                          "bg-black/[.08]",
                      )}
                    >
                      <span
                        className="row-span-2 grid h-[30px] w-[30px] place-items-center rounded-full text-[13px] font-extrabold text-white"
                        style={{ background: srgb(p.color) }}
                      >
                        {p.n}
                      </span>
                      <b className="text-[13px]">{p.nombre}</b>
                      <small className="text-[11.5px] text-[#62646b]">
                        {p.detalle}
                      </small>
                    </button>
                  </li>
                ))}
              {capa === "stands" &&
                (standsFiltrados.length === 0 ? (
                  <li className="px-3 py-4 text-center text-[12px] text-[#62646b]">
                    Ningún stand coincide con «{q}».
                  </li>
                ) : (
                  standsFiltrados.map((s) => (
                    <li key={s.key}>
                      <button
                        type="button"
                        onClick={() => elegirStand(s, "lista")}
                        className={cn(
                          "grid w-full grid-cols-[44px_1fr] items-center gap-x-2.5 rounded-xl px-2.5 py-1.5 text-left",
                          sel?.tipo === "stand" &&
                            sel.key === s.key &&
                            "bg-black/[.08]",
                        )}
                      >
                        <Logo s={s} size={36} />
                        <b className="truncate text-[12.5px]">
                          {s.nombre ?? "Stand disponible"}
                        </b>
                        <small className="text-[11px] text-[#62646b]">
                          <span
                            className="font-bold"
                            style={{ color: PAB_COLOR[s.pabellon] }}
                          >
                            {s.codigo}
                          </span>{" "}
                          · {PABELLON_LABEL[s.pabellon] ?? s.pabellon}
                        </small>
                      </button>
                    </li>
                  ))
                ))}
            </ol>
          )}
          <p className="px-4 pb-2 pt-1 text-[10px] text-[#62646b]">
            Escala según plano técnico · alturas aproximadas.
          </p>
        </div>

        {cargando < 100 && !error && (
          <div className="absolute inset-0 z-20 grid place-content-center gap-2 bg-[#101114] text-center text-white">
            {/* Logo oficial (nunca se recrea con tipografía). */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/brand/logo-cromado-v2.png"
              alt="Feria Effix 2026"
              className="mx-auto h-32 w-64 animate-pulse object-contain"
            />
            <span className="opacity-70">Cargando mapa 3D…</span>
            <div className="mx-auto mt-2 h-1 w-56 overflow-hidden rounded bg-white/20">
              <i
                className="block h-full bg-[#e11d2a] transition-[width]"
                style={{ width: `${cargando}%` }}
              />
            </div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 z-20 grid place-content-center gap-3 bg-[#101114] p-6 text-center text-white">
            <span>{error}</span>
          </div>
        )}
      </div>
    </>
  );
}

/* ---------------------------------------------------------------- piezas */

function Ctl({
  children,
  onClick,
  label,
  activo,
}: {
  children: React.ReactNode;
  onClick: () => void;
  label: string;
  activo?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      aria-pressed={activo}
      className={cn(
        "grid h-11 w-11 place-items-center rounded-xl shadow-lg backdrop-blur",
        activo ? "bg-[#e11d2a] text-white" : "bg-white/95 text-[#101114]",
      )}
    >
      {children}
    </button>
  );
}

function SegIcono({
  children,
  on,
  label,
  onClick,
}: {
  children: React.ReactNode;
  on: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      role="tab"
      aria-selected={on}
      aria-label={label}
      title={label}
      className={cn(
        "grid h-9 w-9 place-items-center rounded-full transition-colors",
        on ? "bg-[#101114] text-white" : "text-[#62646b]",
      )}
    >
      {children}
    </button>
  );
}

/* eslint-disable @next/next/no-img-element -- logos externos del directorio (storage), tamaño fijo */
function Logo({ s, size }: { s: MapaStand; size: number }) {
  if (s.logo) {
    return (
      <img
        src={s.logo}
        alt=""
        width={size}
        height={size}
        className="row-span-2 rounded-lg bg-white object-contain p-0.5 shadow-sm"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <span
      className="row-span-2 grid place-items-center rounded-lg text-[10px] font-extrabold text-white"
      style={{
        width: size,
        height: size,
        background: PAB_COLOR[s.pabellon] ?? "#444",
      }}
    >
      {s.codigo}
    </span>
  );
}

/** Logo oficial dentro del pin redondo del stand (26 px, sobre fondo blanco). */
function LogoPin({ src }: { src: string }) {
  return (
    <img
      src={src}
      alt=""
      width={26}
      height={26}
      className="h-[26px] w-[26px] rounded-full object-contain p-[2px]"
    />
  );
}
/* eslint-enable @next/next/no-img-element */

function StandFicha({ s }: { s: MapaStand }) {
  return (
    <div className="grid grid-cols-[52px_1fr] items-start gap-x-3 px-4 pb-3">
      <Logo s={s} size={52} />
      <div>
        <b className="block text-[13.5px] leading-tight">
          {s.nombre ?? "Stand disponible"}
        </b>
        <small className="block text-[11.5px] text-[#62646b]">
          <span className="font-bold" style={{ color: PAB_COLOR[s.pabellon] }}>
            {s.codigo}
          </span>{" "}
          · {PABELLON_LABEL[s.pabellon] ?? s.pabellon}
          {s.tipo && <> · {s.tipo.replace("_", " ")}</>}
        </small>
        {s.descripcion && (
          <p className="mt-1 line-clamp-2 text-[11.5px] leading-snug text-[#3a3b40]">
            {s.descripcion}
          </p>
        )}
        {s.nombre && (
          <a
            href={`/stands?stand=${encodeURIComponent(s.codigo)}`}
            data-track="map_directory_click"
            data-track-codigo={s.codigo}
            data-track-nombre={s.nombre}
            className="mt-1.5 inline-block rounded-full bg-[#101114] px-3 py-1 text-[11px] font-bold text-white"
          >
            Ver en el directorio →
          </a>
        )}
      </div>
    </div>
  );
}

function PinSvg({ color, label }: { color: string; label: string }) {
  return (
    <svg
      viewBox="0 0 40 54"
      preserveAspectRatio="xMidYMax meet"
      className="h-full w-full"
    >
      <path
        d="M20 52.5C20 52.5 3.5 33 3.5 20a16.5 16.5 0 1 1 33 0C36.5 33 20 52.5 20 52.5Z"
        fill={color}
        stroke="#fff"
        strokeWidth="2.5"
      />
      <circle cx="20" cy="20" r="11.5" fill="#fff" />
      <text
        x="20"
        y="20.5"
        fill={color}
        fontSize="15"
        fontWeight="700"
        textAnchor="middle"
        dominantBaseline="central"
      >
        {label}
      </text>
    </svg>
  );
}

/* ---------------------------------------------------------------- escena: helpers puros sobre la escena */

function vistaInicial(e: Escena) {
  const d = Math.min(1500, Math.max(470, (430 * 1.8) / e.libre));
  const a = (72 * Math.PI) / 180;
  const el = (34 * Math.PI) / 180;
  return {
    pos: e.centro
      .clone()
      .add(
        new e.three.Vector3(
          Math.sin(a) * Math.cos(el),
          Math.sin(el),
          -Math.cos(a) * Math.cos(el),
        ).multiplyScalar(d),
      ),
    obj: e.centro.clone().setY(8),
  };
}

function animar(
  e: Escena,
  dur: number,
  paso: (k: number) => void,
  fin?: () => void,
) {
  const t0 = performance.now();
  e.anim = {
    paso: (ahora) => {
      const k = Math.min(1, (ahora - t0) / dur);
      paso(suave(k));
      if (k >= 1) fin?.();
      return k < 1;
    },
  };
}

function volar(e: Escena, pos: THREE.Vector3, obj: THREE.Vector3, dur = 1100) {
  const p0 = e.camara.position.clone();
  const o0 = e.controles.target.clone();
  animar(e, dur, (k) => {
    e.camara.position.lerpVectors(p0, pos, k);
    e.controles.target.lerpVectors(o0, obj, k);
  });
}

function guardarDatos(e: Escena, d: MapaDatos) {
  e.datos = d;
}

/**
 * Varillas que anclan cada marcador a su punto exacto del mapa: el marcador
 * HTML flota con la perspectiva, la varilla deja claro a qué sitio pertenece.
 * - Lugares: varilla del color del pin desde el piso del nivel hasta el
 *   marcador, con disco en la base.
 * - Stands: varilla delgada del color del pabellón desde el piso del stand
 *   hasta el marcador (sobre el stand).
 * Cuelgan de la raíz del nivel (si la hay) para subir con él en el modo por niveles.
 */
function crearVarillas(e: Escena, d: MapaDatos) {
  const T = e.three;
  const varilla = (
    x: number,
    y: number,
    z0: number,
    z1: number,
    col: THREE.Color,
    radio: number,
  ) => {
    const alto = Math.max(0.5, z1 - z0);
    const m = new T.Mesh(
      new T.CylinderGeometry(radio, radio, alto, 6),
      new T.MeshBasicMaterial({ color: col }),
    );
    m.position.set(x, z0 + alto / 2, -y);
    return m;
  };
  const padre = (grupo: string) => e.raices[RAIZ_DE[grupo] ?? ""] ?? e.scene;
  for (const p of d.pines) {
    const piso = PISO_GRUPO[p.grupo] ?? 0;
    const col = new T.Color(srgb(p.color));
    const g = new T.Group();
    const base = new T.Mesh(
      new T.RingGeometry(0.5, 1.1, 24),
      new T.MeshBasicMaterial({ color: col, side: T.DoubleSide }),
    );
    base.rotation.x = -Math.PI / 2;
    base.position.set(p.pos[0], piso + 0.06, -p.pos[1]);
    g.add(varilla(p.pos[0], p.pos[1], piso, p.pos[2], col, 0.14), base);
    g.renderOrder = 1;
    g.visible = false;
    padre(p.grupo).add(g);
    e.varillas[`pin-${p.n}`] = g;
  }
  for (const st of d.stands) {
    const col = new T.Color(PAB_COLOR[st.pabellon] ?? "#444");
    const g = varilla(
      st.pos[0],
      st.pos[1],
      st.pos[2],
      st.pos[2] + st.alto + 0.4,
      col,
      0.07,
    );
    g.renderOrder = 1;
    g.visible = false;
    padre(st.grupo).add(g);
    e.varillas[`st-${st.key}`] = g;
  }
}

const TEXTO_ERROR_UBIC: Record<ErrorUbicacion, string> = {
  sin_soporte: "Este dispositivo no permite conocer tu ubicación.",
  denegado:
    "No diste permiso de ubicación. Actívalo en los ajustes del navegador o de la app para verte en el mapa.",
  no_disponible: "No se pudo obtener tu ubicación en este momento.",
  tiempo: "La señal GPS tarda en llegar; sigue intentando…",
};

/**
 * Marcador "Mi ubicación" a nivel del suelo (nivel principal; el GPS no sabe
 * en qué piso estás): punto azul con borde blanco y anillo del radio de
 * precisión. Con `null` se oculta.
 */
function ponerUbicacion(
  e: Escena,
  u: { x: number; y: number; precision: number } | null,
) {
  const T = e.three;
  if (!e.ubic) {
    const grupo = new T.Group();
    const punto = new T.Mesh(
      new T.SphereGeometry(1.6, 20, 14),
      new T.MeshBasicMaterial({ color: 0x1a73e8 }),
    );
    punto.position.y = 1.6;
    const borde = new T.Mesh(
      new T.RingGeometry(1.9, 2.6, 32),
      new T.MeshBasicMaterial({ color: 0xffffff, side: T.DoubleSide }),
    );
    borde.rotation.x = -Math.PI / 2;
    borde.position.y = 0.12;
    const anillo = new T.Mesh(
      new T.CircleGeometry(1, 48),
      new T.MeshBasicMaterial({
        color: 0x1a73e8,
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
      }),
    );
    anillo.rotation.x = -Math.PI / 2;
    anillo.position.y = 0.08;
    grupo.add(anillo, borde, punto);
    grupo.renderOrder = 2;
    e.scene.add(grupo);
    e.ubic = { grupo, anillo };
  }
  const { grupo, anillo } = e.ubic;
  if (!u) {
    grupo.visible = false;
  } else {
    grupo.visible = true;
    grupo.position.set(u.x, 0, -u.y);
    const r = Math.min(Math.max(u.precision, 3), 120);
    anillo.scale.set(r, r, 1);
  }
  e.sucio = true;
}

/** Solo se ven las varillas de los marcadores visibles en la capa/modo/búsqueda actual. */
function mostrarVarillas(e: Escena, visibles: Set<string>) {
  for (const [id, g] of Object.entries(e.varillas))
    g.visible = visibles.has(id);
  e.sucio = true;
}

function ocultarGuias(e: Escena) {
  for (const o of e.porGrupo.guias ?? []) o.visible = false;
}

/** Los niveles que flotan no proyectan sombra sobre lo que dejan ver. */
function sombrasNivelesFlotantes(e: Escena, on: boolean) {
  for (const k of ["sup", "multi", "caja", "shell"])
    for (const o of e.porGrupo[k] ?? []) o.castShadow = on;
}

function aplicarVisibilidad(e: Escena, modo: Modo) {
  for (const [g, objs] of Object.entries(e.porGrupo)) {
    const ver = !OCULTOS[modo].includes(g);
    for (const o of objs) o.visible = ver;
  }
  e.sucio = true;
}

const tmp = { v: null as THREE.Vector3 | null };

/** Proyecta cada pin a la pantalla; los pines llevan data-pos en el id del mapa de refs. */
function ubicarPines(
  e: Escena,
  els: Map<string, HTMLButtonElement>,
  capa: HTMLDivElement | null,
) {
  if (!capa) return;
  const w = capa.clientWidth;
  const h = capa.clientHeight;
  tmp.v ??= new e.three.Vector3();
  const v = tmp.v;
  for (const [id, el] of els) {
    const p = el.dataset.pos?.split(",").map(Number);
    if (!p || p.length < 4) continue;
    const lift = e.lift[RAIZ_DE[el.dataset.grupo ?? ""] ?? ""] ?? 0;
    v.set(p[0], p[2] + lift + p[3], -p[1]).project(e.camara);
    const fuera = v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1;
    el.style.opacity = fuera ? "0" : "1";
    el.style.pointerEvents = fuera ? "none" : "auto";
    if (!fuera)
      el.style.transform = `translate3d(${(((v.x + 1) / 2) * w).toFixed(1)}px, ${(((1 - v.y) / 2) * h).toFixed(1)}px, 0)`;
    void id;
  }
}
