---
name: mapa-visor-web
description: Exporta el modelo 3D a una página web (three.js + GLB con Draco + datos.json), la prueba en local y en tamaño celular, y la publica en Vercel, Netlify o GitHub Pages, o la embebe en otra web con un iframe. Úsalo en la fase 4 del mapa 3D o cuando el visor cargue mal, pese mucho o muestre una versión vieja.
---

# Visor web del mapa

## 1. Exportar

```
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/exportar_web.py -- proyectos/<id>/recinto.json
```

Sale `proyectos/<id>/salida/web/`, una carpeta **estática y autocontenida**:
- `index.html`, `app.js`, `estilos.css`: copiados de `visor/`, con título y versión sellados;
- `mapa.glb`: el modelo con Draco;
- `datos.json`: títulos, niveles, pines y stands;
- `draco/`: el decodificador local, que no depende de un CDN.

El script imprime triángulos y MB. **Meta: menos de 10 MB.** Si pasa de 12, avisa (ver `docs/PROBLEMAS.md` → peso).

## 2. Probar en local

```
python -m http.server 8765 --directory proyectos/<id>/salida/web
```

Abre http://localhost:8765 con el navegador integrado (`preview_start` con la url) y revisa:
1. Carga sin errores de consola.
2. **Exterior**: se ven cubiertas y rótulos; los pines de niveles `bajo_techo` no aparecen.
3. **Por niveles**: los niveles con `separacion` suben, las cubiertas desaparecen y se ve el interior.
4. Tocar un pin de la lista: la cámara vuela al lugar, y cambia sola a "Por niveles" si el lugar está tapado.
5. **Stands**: la pestaña aparece si hay stands con código. Prueba el buscador ("a5" debe encontrar A05) y que la
   cámara vuele al stand.
6. **Celular**: `resize_window` en `mobile`. El panel pasa a hoja inferior y los botones no tapan el mapa.
7. **Enlaces directos**: `?lugar=3` y `?stand=A12` abren el mapa ya enfocado (sirven para QR en el recinto).

Luego vuelve el navegador a escritorio. Muéstrale a la persona una captura o el link local.

## 3. Publicar (pide permiso antes: es publicar en internet)

Cualquier hosting de archivos estáticos sirve. La carpeta es `proyectos/<id>/salida/web/`.

- **Vercel**: `npx vercel deploy proyectos/<id>/salida/web --prod`. La primera vez pide iniciar sesión, y eso lo hace la persona.
- **Netlify**: `npx netlify deploy --dir proyectos/<id>/salida/web --prod`, o arrastrar la carpeta a app.netlify.com/drop.
- **GitHub Pages**: subir el contenido de `web/` a un repo y activar Pages en la rama.
- **Embeber en otra web**:
  `<iframe src="https://.../" style="width:100%;height:80vh;border:0" allow="fullscreen"></iframe>`

Después de publicar, abre el link real y repite la prueba 1–5.

## 4. Personalizar el visor

Todo el visor está en `visor/`; las copias en `salida/web/` se sobrescriben en cada exportación.
- **Colores de marca**: variables `--tinta` y `--rojo` en `visor/estilos.css`.
- **Logo** en la pantalla de carga: agrégalo en `index.html` dentro de `#carga` y copia el archivo a `salida/web/`.
- **Textos**: `evento.titulo`, `evento.subtitulo`, `evento.nota` y `evento.titulo_lista` en recinto.json.
- **Vista inicial y distancias**: `vistaInicial()` en `app.js` (ángulos 72° / 34°, escala con el radio del recinto).

## 5. Si algo falla

- **Pantalla "No se pudo cargar"**: abre la consola. Casi siempre es abrir `index.html` con doble clic (file://),
  que no deja usar fetch. Hay que servirla con http.server o publicarla.
- **Se ve el modelo viejo**: caché. Exporta de nuevo (cambia `?v=`) o recarga con Ctrl+F5.
- **Pines desfasados al girar**: no les pongas `transition` CSS a la posición. El visor los recoloca en el mismo
  cuadro del render.
- **Lento en celular**: baja `setPixelRatio` (ya limitado a 1,5 en pantallas táctiles) y el tamaño del mapa de sombras,
  y reduce mallas o sillas.
