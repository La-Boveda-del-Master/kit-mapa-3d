// Mapa 3D navegable de un recinto. Modelo: mapa.glb (pipeline/exportar_web.py). Titulos, niveles, pines y stands: datos.json.
// Coordenadas: Blender (x este, y norte, z alto) -> three.js (x, z, -y).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const VER = '1';   // exportar_web.py lo cambia en cada exportacion para saltar la cache del navegador
const $ = (id) => document.getElementById(id);
const movil = matchMedia('(max-width: 820px)');
const tactil = matchMedia('(pointer: coarse)').matches;
const HORIZONTE = 0xd3dfeb;
const aThree = (p) => new THREE.Vector3(p[0], p[2], -p[1]);

// ---------------------------------------------------------------- escena
const lienzo = $('lienzo');
const renderer = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, tactil ? 1.5 : 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;           // escena estatica: la sombra solo se recalcula al mover niveles

const scene = new THREE.Scene();
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.35;
scene.add(new THREE.Mesh(
  new THREE.SphereGeometry(4000, 32, 16),
  new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { h: { value: new THREE.Color(HORIZONTE) }, c: { value: new THREE.Color(0x3f7fd6) } },
    vertexShader: 'varying float y; void main(){ y = normalize(position).y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'uniform vec3 h; uniform vec3 c; varying float y; void main(){ gl_FragColor = vec4(mix(h, c, smoothstep(0.0, 0.55, y)), 1.0); }',
  })));
scene.add(new THREE.HemisphereLight(0xdfeaff, 0x8a8372, 1.15));
const sol = new THREE.DirectionalLight(0xfff1dc, 2.6);
scene.add(sol, sol.target);

const camara = new THREE.PerspectiveCamera(36, 1, 1, 8000);
const controles = new OrbitControls(camara, lienzo);
Object.assign(controles, { enableDamping: true, dampingFactor: 0.08, maxPolarAngle: 1.47,
  zoomToCursor: true, autoRotateSpeed: 0.7, screenSpacePanning: false });

// ---------------------------------------------------------------- estado
let datos = null, modo = 'exterior', capa = 'lugares', sucio = true, sel = null, selStand = null, libre = 1.5, R = 200;
const CENTRO = new THREE.Vector3();
const raices = {}, porGrupo = {}, pines = [], puntos = [];
const lift = {};
let animacion = null;
const sRGB = (c) => '#' + c.map((v) => Math.round(Math.pow(v, 1 / 2.2) * 255).toString(16).padStart(2, '0')).join('');
const suave = (k) => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);
const nivelBajoTecho = (g) => (datos.niveles.find((n) => n.id === g) || {}).bajo_techo;

function vistaInicial() {
  const d = THREE.MathUtils.clamp(R * 3.4 / Math.min(libre, 1.8), R * 2.2, R * 6), a = THREE.MathUtils.degToRad(72), e = THREE.MathUtils.degToRad(34);
  return { pos: CENTRO.clone().add(new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), -Math.cos(a) * Math.cos(e)).multiplyScalar(d)),
    obj: CENTRO.clone().setY(4) };
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
    const ver = !(modo === 'niveles' && g.startsWith('techo_'));
    for (const o of objs) o.visible = ver;
  }
  // en exterior no se muestran los pines de niveles tapados por otro (se pasa solo a "Por niveles" al tocarlos)
  for (const p of pines) p.activo = capa === 'lugares' && (modo === 'niveles' || !nivelBajoTecho(p.grupo));
  for (const p of puntos) p.activo = capa === 'stands' && (modo === 'niveles' || !nivelBajoTecho(p.grupo));
  sucio = true;
}

function ponerModo(nuevo) {
  if (nuevo === modo) return;
  modo = nuevo;
  for (const [id, m] of [['modo-exterior', 'exterior'], ['modo-niveles', 'niveles']]) {
    $(id).classList.toggle('activo', modo === m); $(id).setAttribute('aria-selected', modo === m);
  }
  const ini = { ...lift }, fin = {};
  for (const k of Object.keys(lift)) fin[k] = modo === 'niveles' ? datos.lift[k] : 0;
  if (modo === 'niveles') aplicarVisibilidad();            // al separar: primero se quitan las cubiertas
  animar(1200, (k) => {
    for (const key of Object.keys(lift)) { lift[key] = ini[key] + (fin[key] - ini[key]) * k; if (raices[key]) raices[key].position.y = lift[key]; }
    renderer.shadowMap.needsUpdate = true;
  }, () => { aplicarVisibilidad(); renderer.shadowMap.needsUpdate = true; });
}

// ---------------------------------------------------------------- pines (lugares) y puntos (stands)
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
  li.innerHTML = `<span class="num" style="background:${col}">${p.n}</span><b></b><small><span class="det"></span><span class="nivel" style="color:${col}"></span></small>`;
  li.querySelector('b').textContent = p.nombre; li.querySelector('.det').textContent = p.detalle; li.querySelector('.nivel').textContent = p.nivel;
  li.addEventListener('click', () => seleccionar(p.n));
  $('lista').append(li);
  return { ...p, col, el: b, li, activo: true, base: aThree(p.pos), mundo: new THREE.Vector3() };
}

function crearPunto(s) {
  const b = document.createElement('button');
  b.className = 'punto oculto'; b.title = `${s.codigo}${s.nombre ? ' · ' + s.nombre : ''}`; b.setAttribute('aria-label', b.title);
  b.addEventListener('click', (ev) => { ev.stopPropagation(); seleccionarStand(s.key); });
  $('pines').append(b);
  const li = document.createElement('li');
  li.innerHTML = '<span class="cod"></span><b></b><small></small>';
  li.querySelector('.cod').textContent = s.codigo; li.querySelector('b').textContent = s.nombre || `Stand ${s.codigo}`;
  li.querySelector('small').textContent = [s.detalle, s.nivel].filter(Boolean).join(' · ');
  li.addEventListener('click', () => seleccionarStand(s.key));
  $('lista-stands').append(li);
  return { ...s, el: b, li, activo: false, base: aThree(s.pos), mundo: new THREE.Vector3() };
}

const v = new THREE.Vector3();
function ubicar(lista) {
  const w = lienzo.clientWidth, h = lienzo.clientHeight;
  for (const p of lista) {
    p.mundo.copy(p.base); p.mundo.y += lift[p.grupo] || 0;
    v.copy(p.mundo).project(camara);
    const fuera = !p.activo || v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1;
    p.el.classList.toggle('oculto', fuera);
    if (!fuera) p.el.style.transform = `translate3d(${((v.x + 1) / 2 * w).toFixed(1)}px, ${((1 - v.y) / 2 * h).toFixed(1)}px, 0)`;
  }
}

function acercar(base, grupo, cerca) {
  if (nivelBajoTecho(grupo) && modo !== 'niveles') ponerModo('niveles');
  const obj = base.clone(); obj.y += (modo === 'niveles' ? datos.lift[grupo] || 0 : 0) - 2;
  const dir = camara.position.clone().sub(controles.target).normalize();
  if (dir.y < 0.45) { dir.y = 0.45; dir.normalize(); }
  volar(obj.clone().add(dir.multiplyScalar(cerca)), obj);
  controles.autoRotate = false; $('btn-girar').setAttribute('aria-pressed', 'false');
}

function mostrarFicha(html) {
  const f = $('ficha'); f.hidden = false; f.innerHTML = html;
  $('asa-txt').textContent = capa === 'stands' ? 'Ver todos los stands' : 'Ver todos los lugares';
  if (movil.matches) abrirPanel(false);
  medirHoja();
}

function seleccionar(n) {
  const p = pines.find((q) => q.n === n);
  if (!p) return;
  if (capa !== 'lugares') ponerCapa('lugares');
  sel = n;
  for (const q of pines) { q.el.classList.toggle('sel', q.n === n); q.li.classList.toggle('sel', q.n === n); }
  p.li.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  mostrarFicha(`<span class="num" style="background:${p.col}">${p.n}</span><b>${esc(p.nombre)}</b><small>${esc(p.detalle)}</small>`);
  acercar(p.base, p.grupo, movil.matches ? R * .9 : R * .75);
}

function seleccionarStand(key) {
  const s = puntos.find((q) => q.key === key);
  if (!s) return;
  if (capa !== 'stands') ponerCapa('stands');
  selStand = key;
  for (const q of puntos) { q.el.classList.toggle('sel', q.key === key); q.li.classList.toggle('sel', q.key === key); }
  s.li.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  mostrarFicha(`<span class="cod">${esc(s.codigo)}</span><b>${esc(s.nombre || 'Stand ' + s.codigo)}</b><small>${esc([s.detalle, s.nivel].filter(Boolean).join(' · '))}</small>`);
  acercar(s.base, s.grupo, 45);
}

function ponerCapa(nueva) {
  capa = nueva;
  for (const [id, c] of [['capa-lugares', 'lugares'], ['capa-stands', 'stands']]) {
    $(id).classList.toggle('activo', capa === c); $(id).setAttribute('aria-selected', capa === c);
  }
  $('lista').hidden = capa !== 'lugares'; $('lista-stands').hidden = capa !== 'stands'; $('buscar').hidden = capa !== 'stands';
  $('ficha').hidden = true;
  aplicarVisibilidad();
}

function filtrarStands(q) {
  const t = q.trim().toUpperCase().replace(/[^A-Z0-9 ]/g, ''), k = t.replace(/ /g, '').replace(/^([A-Z]+)0*(\d)/, '$1$2');
  for (const s of puntos) {
    const ok = !t || s.key.startsWith(k) || (s.nombre || '').toUpperCase().includes(t);
    s.li.hidden = !ok;
  }
}

const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// ---------------------------------------------------------------- panel (hoja inferior en celular)
function abrirPanel(abrir) {
  $('panel').classList.toggle('abierto', abrir);
  $('panel-asa').setAttribute('aria-expanded', abrir);
  $('asa-txt').textContent = abrir || !(sel || selStand) ? datos.meta.lista : (capa === 'stands' ? 'Ver todos los stands' : 'Ver todos los lugares');
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
$('capa-lugares').addEventListener('click', () => ponerCapa('lugares'));
$('capa-stands').addEventListener('click', () => ponerCapa('stands'));
$('buscar').addEventListener('input', (e) => filtrarStands(e.target.value));
$('btn-inicio').addEventListener('click', () => { const i = vistaInicial(); volar(i.pos, i.obj); });
$('btn-planta').addEventListener('click', () => {
  const o = controles.target.clone().setY(0);
  volar(o.clone().add(new THREE.Vector3(0.01, THREE.MathUtils.clamp(R * 3 / Math.min(libre, 1.5), R * 2.5, R * 6), 0)), o);
});
$('btn-girar').addEventListener('click', (e) => {
  controles.autoRotate = !controles.autoRotate;
  e.currentTarget.setAttribute('aria-pressed', controles.autoRotate);
});
controles.addEventListener('start', () => { $('ayuda').classList.add('fuera'); });
controles.addEventListener('change', () => { sucio = true; });

// ---------------------------------------------------------------- tamano y bucle
function ajustar() {
  const w = innerWidth, h = innerHeight;
  if (w < 50 || h < 50) return;                       // pestana minimizada u oculta: no dejar el visor en 0x0
  renderer.setSize(w, h, false);
  // en escritorio el panel tapa la derecha: el centro de la vista se corre a la izquierda
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
  ubicar(pines); ubicar(puntos);                     // en el mismo cuadro que el render: los pines no se rezagan al girar
}

// ---------------------------------------------------------------- carga
async function iniciar() {
  ajustar();
  datos = await (await fetch('datos.json?v=' + VER)).json();
  R = Math.max(60, datos.radio);
  CENTRO.copy(aThree([datos.centro[0], datos.centro[1], 0]));
  Object.assign(controles, { minDistance: 12, maxDistance: R * 9 });
  scene.fog = new THREE.Fog(HORIZONTE, R * 5, R * 18);
  sol.position.copy(CENTRO).add(new THREE.Vector3(R * .7, R * 1.1, R * .55));
  sol.target.position.copy(CENTRO);
  sol.castShadow = true;
  sol.shadow.mapSize.setScalar(tactil ? 2048 : 4096);
  Object.assign(sol.shadow.camera, { left: -R * 1.2, right: R * 1.2, top: R * 1.2, bottom: -R * 1.2, near: 1, far: R * 5 });
  sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.6;
  const lejos = new THREE.Mesh(new THREE.PlaneGeometry(R * 40, R * 40), new THREE.MeshLambertMaterial({ color: 0xa9aaa6 }));
  lejos.rotation.x = -Math.PI / 2; lejos.position.set(CENTRO.x, datos.z_min - .6, CENTRO.z); scene.add(lejos);
  const i = vistaInicial(); camara.position.copy(i.pos); controles.target.copy(i.obj); controles.update();
  $('nota').textContent = datos.meta.nota; $('asa-txt').textContent = datos.meta.lista;
  for (const k of Object.keys(datos.lift)) lift[k] = 0;
  if (!Object.keys(datos.lift).length) $('modo-niveles').closest('.modos').hidden = true;   // un solo nivel: no hay modos

  const draco = new DRACOLoader().setDecoderPath('draco/');
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync('mapa.glb?v=' + VER, (e) => {
    $('carga-barra').style.width = Math.min(96, (e.loaded / (e.total || 8e6)) * 100) + '%';
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
  for (const s of datos.stands) puntos.push(crearPunto(s));
  if (puntos.length) $('capas').hidden = false;
  aplicarVisibilidad();
  renderer.shadowMap.needsUpdate = true;
  window.__mapa = { scene, camara, controles, pines, puntos, ponerModo, ponerCapa, seleccionar, seleccionarStand, renderer };
  const q = new URLSearchParams(location.search);          // enlaces directos: ?lugar=3  o  ?stand=A12
  if (q.get('stand')) seleccionarStand(q.get('stand').toUpperCase().replace(/[^A-Z0-9]/g, '').replace(/^([A-Z]+)0*(\d)/, '$1$2'));
  else if (q.get('lugar')) seleccionar(Number(q.get('lugar')));
  $('carga').classList.add('lista-ok');
  setTimeout(() => $('ayuda').classList.add('fuera'), 9000);
  medirHoja();
  requestAnimationFrame(bucle);
}
iniciar().catch((err) => {
  console.error(err);
  $('carga').querySelector('span').textContent = 'No se pudo cargar el mapa. Revisa tu conexión y recarga la página.';
});
