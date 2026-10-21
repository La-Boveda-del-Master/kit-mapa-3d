// Mapa 3D navegable de Feria Effix 2026 · Plaza Mayor Medellín
// Modelo: mapa.glb (exportar_web.py desde Blender). Pines y niveles: datos.json.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const VER = '1791414098';   // cambia en cada exportacion para saltar la cache del navegador
const $ = (id) => document.getElementById(id);
const movil = matchMedia('(max-width: 820px)');
const tactil = matchMedia('(pointer: coarse)').matches;
const HORIZONTE = 0xd3dfeb;

// ---------------------------------------------------------------- escena
const lienzo = $('lienzo');
const renderer = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, tactil ? 1.5 : 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;           // escena estática: la sombra solo se recalcula al mover niveles

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(HORIZONTE, 1100, 4200);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.35;

// cielo en degradado
scene.add(new THREE.Mesh(
  new THREE.SphereGeometry(4000, 32, 16),
  new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { h: { value: new THREE.Color(HORIZONTE) }, c: { value: new THREE.Color(0x3f7fd6) } },
    vertexShader: 'varying float y; void main(){ y = normalize(position).y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'uniform vec3 h; uniform vec3 c; varying float y; void main(){ gl_FragColor = vec4(mix(h, c, smoothstep(0.0, 0.55, y)), 1.0); }',
  })));
// suelo lejano (se funde con el horizonte)
const lejos = new THREE.Mesh(new THREE.PlaneGeometry(9000, 9000), new THREE.MeshLambertMaterial({ color: 0xa9aaa6 }));
lejos.rotation.x = -Math.PI / 2; lejos.position.y = -9.8; scene.add(lejos);   // bajo el sótano del Gran Salón

scene.add(new THREE.HemisphereLight(0xdfeaff, 0x8a8372, 1.15));
const sol = new THREE.DirectionalLight(0xfff1dc, 2.6);
const CENTRO = new THREE.Vector3(-10, 0, -75);            // Blender (x, y, z) -> three (x, z, -y)
sol.position.copy(CENTRO).add(new THREE.Vector3(230, 330, 170));
sol.target.position.copy(CENTRO);
sol.castShadow = true;
sol.shadow.mapSize.setScalar(tactil ? 2048 : 4096);
Object.assign(sol.shadow.camera, { left: -330, right: 330, top: 330, bottom: -330, near: 50, far: 1100 });
sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.6;
scene.add(sol, sol.target);

const camara = new THREE.PerspectiveCamera(36, 1, 2, 6000);
const controles = new OrbitControls(camara, lienzo);
Object.assign(controles, { enableDamping: true, dampingFactor: 0.08, minDistance: 22, maxDistance: 1700, maxPolarAngle: 1.47,
  zoomToCursor: true, autoRotateSpeed: 0.7, screenSpacePanning: false });

// ---------------------------------------------------------------- estado
let datos = null, modo = 'exterior', sucio = true, sel = null, libre = 1.5;
const raices = {}, porGrupo = {}, pines = [];
const lift = { sup: 0, multi: 0, caja: 0, shell: 0 };
let animacion = null;                                    // { t0, dur, paso(k) }
const OCULTOS = { exterior: ['guias', 'huella'], niveles: ['ext_base', 'ext_sup', 'losa'] };
const RAIZ_DE = { sup: 'sup', multi: 'multi', caja: 'caja' };
const sRGB = (c) => '#' + c.map((v) => Math.round(Math.pow(v, 1 / 2.2) * 255).toString(16).padStart(2, '0')).join('');
const suave = (k) => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);

function vistaInicial() {
  const d = THREE.MathUtils.clamp(430 * 1.8 / libre, 470, 1500), a = THREE.MathUtils.degToRad(72), e = THREE.MathUtils.degToRad(34);
  return { pos: CENTRO.clone().add(new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), -Math.cos(a) * Math.cos(e)).multiplyScalar(d)),
    obj: CENTRO.clone().setY(8) };
}

function volar(pos, obj, dur = 1100) {
  const p0 = camara.position.clone(), o0 = controles.target.clone();
  animar(dur, (k) => { camara.position.lerpVectors(p0, pos, k); controles.target.lerpVectors(o0, obj, k); });
}

function animar(dur, paso, fin) {
  const previa = animacion;
  const t0 = performance.now();
  animacion = { paso: (ahora) => {
    const k = Math.min(1, (ahora - t0) / dur);
    paso(suave(k));
    if (previa && previa.viva) previa.viva = previa.paso(ahora);
    if (k >= 1 && fin) fin();
    return k < 1 || (previa && previa.viva);
  }, viva: true };
}

// ---------------------------------------------------------------- modos (exterior / por niveles)
function aplicarVisibilidad() {
  for (const [g, objs] of Object.entries(porGrupo)) {
    const ver = !OCULTOS[modo].includes(g);
    for (const o of objs) o.visible = ver;
  }
  for (const p of pines) p.activo = modo === 'niveles' || ['base', 'sup'].includes(p.grupo) || p.n === 1;
}

function ponerModo(nuevo) {
  if (nuevo === modo) return;
  modo = nuevo;
  $('modo-exterior').classList.toggle('activo', modo === 'exterior'); $('modo-exterior').setAttribute('aria-selected', modo === 'exterior');
  $('modo-niveles').classList.toggle('activo', modo === 'niveles'); $('modo-niveles').setAttribute('aria-selected', modo === 'niveles');
  const ini = { ...lift }, fin = {};
  for (const k of Object.keys(lift)) fin[k] = modo === 'niveles' ? datos.lift[k] : 0;
  if (modo === 'niveles') aplicarVisibilidad();            // al separar: primero se quitan las cubiertas
  else for (const o of porGrupo.guias || []) o.visible = false;
  animar(1200, (k) => {
    for (const key of Object.keys(lift)) { lift[key] = ini[key] + (fin[key] - ini[key]) * k; raices[key].position.y = lift[key]; }
    renderer.shadowMap.needsUpdate = true;
  }, () => { aplicarVisibilidad(); renderer.shadowMap.needsUpdate = true; sucio = true; });
}

// ---------------------------------------------------------------- pines
const NS = 'http://www.w3.org/2000/svg';
function crearPin(p) {
  const col = sRGB(p.color);
  const b = document.createElement('button');
  b.className = 'pin'; b.title = p.nombre; b.setAttribute('aria-label', `${p.n}. ${p.nombre}`);
  b.innerHTML = `<svg viewBox="0 0 40 54" xmlns="${NS}"><path d="M20 52.5C20 52.5 3.5 33 3.5 20a16.5 16.5 0 1 1 33 0C36.5 33 20 52.5 20 52.5Z" fill="${col}" stroke="#fff" stroke-width="2.5"/>` +
    `<circle cx="20" cy="20" r="11.5" fill="#fff"/><text x="20" y="20.5" fill="${col}">${p.n}</text></svg>`;
  b.addEventListener('click', (ev) => { ev.stopPropagation(); seleccionar(p.n); });
  $('pines').append(b);
  const li = document.createElement('li');
  li.innerHTML = `<span class="num" style="background:${col}">${p.n}</span><b>${p.nombre}</b><small>${p.detalle}<span class="nivel" style="color:${col}">${p.nivel}</span></small>`;
  li.addEventListener('click', () => seleccionar(p.n));
  $('lista').append(li);
  return { ...p, col, el: b, li, activo: true, base: new THREE.Vector3(p.pos[0], p.pos[2], -p.pos[1]), mundo: new THREE.Vector3() };
}

const v = new THREE.Vector3();
function ubicarPines() {
  const w = lienzo.clientWidth, h = lienzo.clientHeight;
  for (const p of pines) {
    p.mundo.copy(p.base); p.mundo.y += lift[RAIZ_DE[p.grupo]] || 0;
    v.copy(p.mundo).project(camara);
    const fuera = !p.activo || v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1;
    p.el.classList.toggle('oculto', fuera);
    if (!fuera) p.el.style.transform = `translate3d(${((v.x + 1) / 2 * w).toFixed(1)}px, ${((1 - v.y) / 2 * h).toFixed(1)}px, 0)`;
  }
}

function seleccionar(n) {
  const p = pines.find((q) => q.n === n);
  if (!p) return;
  if (!p.activo) ponerModo('niveles');
  sel = n;
  for (const q of pines) { q.el.classList.toggle('sel', q.n === n); q.li.classList.toggle('sel', q.n === n); }
  p.li.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  const f = $('ficha');
  f.hidden = false;
  f.innerHTML = `<span class="num" style="background:${p.col}">${p.n}</span><b>${p.nombre}</b><small>${p.detalle}</small>`;
  $('asa-txt').textContent = 'Ver todos los lugares';
  if (movil.matches) abrirPanel(false);
  // acercar manteniendo el ángulo actual de la cámara
  const obj = p.base.clone(); obj.y += (modo === 'niveles' || !p.activo ? datos.lift[RAIZ_DE[p.grupo]] || 0 : 0) - 4;
  const dir = camara.position.clone().sub(controles.target).normalize();
  if (dir.y < 0.45) { dir.y = 0.45; dir.normalize(); }
  volar(obj.clone().add(dir.multiplyScalar(movil.matches ? 190 : 150)), obj);
  controles.autoRotate = false; $('btn-girar').setAttribute('aria-pressed', 'false');
  medirHoja();
}

// ---------------------------------------------------------------- panel (hoja inferior en celular)
function abrirPanel(abrir) {
  $('panel').classList.toggle('abierto', abrir);
  $('panel-asa').setAttribute('aria-expanded', abrir);
  if (!abrir) $('asa-txt').textContent = sel ? 'Ver todos los lugares' : 'Lugares de la feria';
  else $('asa-txt').textContent = 'Lugares de la feria';
  medirHoja();
}
function medirHoja() {
  requestAnimationFrame(() => {
    const cerrada = !$('panel').classList.contains('abierto');
    if (movil.matches && cerrada) document.documentElement.style.setProperty('--alto-hoja', $('panel').offsetHeight + 'px');
  });
}
$('panel-asa').addEventListener('click', () => { if (movil.matches) abrirPanel(!$('panel').classList.contains('abierto')); });

// ---------------------------------------------------------------- botones
$('modo-exterior').addEventListener('click', () => ponerModo('exterior'));
$('modo-niveles').addEventListener('click', () => ponerModo('niveles'));
$('btn-inicio').addEventListener('click', () => { const i = vistaInicial(); volar(i.pos, i.obj); });
$('btn-planta').addEventListener('click', () => {
  const o = controles.target.clone().setY(0);
  volar(o.clone().add(new THREE.Vector3(0.01, THREE.MathUtils.clamp(620 * 1.5 / libre, 620, 1000), 0)), o);
});
$('btn-girar').addEventListener('click', (e) => {
  controles.autoRotate = !controles.autoRotate;
  e.currentTarget.setAttribute('aria-pressed', controles.autoRotate);
});
controles.addEventListener('start', () => { $('ayuda').classList.add('fuera'); });
controles.addEventListener('change', () => { sucio = true; });

// ---------------------------------------------------------------- tamaño y bucle
function ajustar() {
  const w = innerWidth, h = innerHeight;
  if (w < 50 || h < 50) return;                       // pestaña minimizada u oculta
  renderer.setSize(w, h, false);
  // en escritorio el panel tapa la derecha: se desplaza el centro de la vista hacia la izquierda
  const panel = movil.matches ? 0 : 354;
  camara.aspect = (w + panel) / h;
  if (panel) camara.setViewOffset(w + panel, h, panel, 0, w, h); else camara.clearViewOffset();
  libre = (w - panel) / h;
  camara.updateProjectionMatrix();
  sucio = true; medirHoja();
}
addEventListener('resize', ajustar);
movil.addEventListener('change', ajustar);

function bucle(ahora) {
  requestAnimationFrame(bucle);
  if (animacion && animacion.viva) { animacion.viva = animacion.paso(ahora); sucio = true; }
  if (controles.update()) sucio = true;
  if (!Number.isFinite(camara.position.x + camara.position.y + camara.position.z)) {   // red de seguridad
    const i = vistaInicial(); camara.position.copy(i.pos); controles.target.copy(i.obj); controles.update(); sucio = true;
  }
  if (!sucio) return;
  sucio = false;
  renderer.render(scene, camara);
  ubicarPines();
}

// ---------------------------------------------------------------- carga
async function iniciar() {
  ajustar();
  const i = vistaInicial(); camara.position.copy(i.pos); controles.target.copy(i.obj); controles.update();
  datos = await (await fetch('datos.json?v=' + VER)).json();
  const draco = new DRACOLoader().setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/');
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync('mapa.glb?v=' + VER, (e) => {
    $('carga-barra').style.width = Math.min(96, (e.loaded / (e.total || 6.5e6)) * 100) + '%';
  });
  const anis = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  gltf.scene.traverse((o) => {
    const g = o.userData.grupo;
    if (g) (porGrupo[g] ||= []).push(o);
    if (!o.isMesh) return;
    const m = o.material;
    o.castShadow = !m.transparent; o.receiveShadow = true;
    if (m.transparent) m.depthWrite = false;
    for (const t of [m.map, m.normalMap]) if (t) t.anisotropy = anis;
  });
  for (const [k, nombre] of Object.entries(datos.raices)) raices[k] = gltf.scene.getObjectByName(nombre);
  scene.add(gltf.scene);
  for (const p of datos.pines) pines.push(crearPin(p));
  aplicarVisibilidad();
  renderer.shadowMap.needsUpdate = true;
  window.__mapa = { scene, camara, controles, pines, ponerModo, seleccionar, renderer };
  $('carga').classList.add('lista-ok');
  setTimeout(() => $('ayuda').classList.add('fuera'), 9000);
  medirHoja();
  requestAnimationFrame(bucle);
}
iniciar().catch((err) => {
  console.error(err);
  $('carga').querySelector('span').textContent = 'No se pudo cargar el mapa. Revisa tu conexión y recarga la página.';
});
