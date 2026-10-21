---
name: mapa-render-profesional
description: Saca renders 3D de calidad de agencia y láminas listas para imprimir. Tiene cuatro estilos (realista, maqueta blanca de arquitectura, ilustrado tipo infografía, nocturno) y cinco vistas (axonométrica, aérea, planta con escala exacta, por niveles, interiores). Usa EEVEE o Cycles, saca hasta 8K o A1 a 300 ppp, con fondo transparente si hace falta, y compone láminas con título, lugares numerados, leyenda, norte y escala gráfica. Úsalo para presentar, vender, imprimir, señalética o redes, y para revisar avances con la persona.
---

# Render profesional y láminas

Scripts: `pipeline/renders.py` (Blender) y `pipeline/componer_lamina.py` (Python).

```
blender -b proyectos/<id>/salida/modelo.blend --python pipeline/renders.py -- proyectos/<id>/mapa.json \
        --estilo=realista --vistas=axo,planta,niveles --tam=4k
python pipeline/componer_lamina.py proyectos/<id>/salida/renders/axo_realista.png
```

Cada render deja `salida/renders/<vista>_<estilo>.png` y un `.json` con dónde cae cada lugar en la imagen, el norte y la escala.
La lámina sale como `lamina_<vista>_<estilo>.png` y `.pdf`.

## Elegir con la persona (dirección de arte)

| Para qué | Estilo | Vista | Tamaño |
|---|---|---|---|
| Presentación comercial, web, redes | `realista` | `axo` o `aerea` | `4k` |
| Arquitectura, concurso, propuesta sobria | `maqueta` | `axo`, `corte` | `4k` / `a2` |
| Señalética, mapa para el público, folleto | `ilustrado` | `axo` o `niveles` + lámina | `a3` / `a2` |
| Evento de noche, pieza emocional | `noche` | `aerea` | `4k` |
| Mostrar cómo están los pisos | cualquiera | `niveles` | `4k` + lámina |
| Medir, cotizar, comparar con el plano | `ilustrado` o `maqueta` | `planta` + lámina (escala exacta) | `a3` |

## Vistas

- `axo`: axonométrica ortográfica a 35,26°. Es la vista clásica de "mapa 3D", sin deformación de perspectiva.
- `aerea`: perspectiva a tres cuartos, a 30°. Es la más fotográfica.
- `planta`: desde arriba, con el norte arriba. Es la única con escala gráfica exacta.
- `niveles`: axonométrica sin cubiertas y con los pisos separados.
- `corte`: axonométrica sin cubiertas y con todo en su sitio, para ver los interiores.

`--azimut=35` gira la cámara alrededor del lugar (grados desde el sur). Prueba 35, 125, 215 y 305, y quédate con el
que muestre la fachada principal y el ingreso. El encuadre se ajusta solo a lo visible.

## Calidad

- **Motor**:
  - `--motor=eevee` (por defecto): rápido, con trazado de rayos y GI rápida.
  - `--motor=cycles`: sombras y rebotes fieles; usa GPU si hay. Úsalo para la versión final del render principal.
- **Tamaño (`--tam`)**: `preview`, `hd`, `4k`, `8k`, `a3`, `a2`, `a1` (300 ppp). Para revisar, usa siempre `--preview`.
- **Muestras**: `--muestras=N` sube la calidad. Si ves ruido o sombras con grano, auméntalas (EEVEE 128+, Cycles 512).
- **Bordes**: en `realista` y `maqueta` se biselan solos, y eso da la lectura de maqueta física.
  Para ir más rápido, `--sin-bisel`.
- **Fondo**: `--transparente` deja un PNG con alfa, para montar sobre un diseño de marca.
- **Revisión contra el plano**: `--calco` pone la imagen del plano debajo del modelo.

## Lámina (`componer_lamina.py`)

- **Arriba**: título y subtítulo de `marca`, con una barra del color de marca.
- **Sobre el render**:
  - los lugares numerados (pines) con el color de cada uno; los que quedan tapados no se dibujan;
  - la brújula orientada al norte real de la vista;
  - en `planta`, la escala gráfica.
- **Leyenda**: a la derecha (formato horizontal) o abajo (vertical); se fuerza con `--leyenda=abajo`.
  `--sin-pines` deja el render limpio.
- **Al pie**: `marca.nota`.
- **PDF a 300 ppp** para imprenta. Para un pliego, renderiza con `--tam=a2` o `a1` antes de componer.

## Lista de control antes de entregar un render

1. **Composición**: el sujeto ocupa el 70–85 % del cuadro; nada importante cortado; el horizonte o el terreno no
   deja vacíos en las esquinas.
2. **Luz**: las sombras dan volumen y no tapan fachadas clave. Si una fachada importante queda en sombra, cambia `--azimut`.
3. **Color**: el color de marca aparece y no hay más de 4 colores fuertes. En `maqueta` todo es neutro menos el vidrio.
4. **Textos**: se leen a tamaño de entrega; ninguno se sale de su espacio; no hay rótulos encima de otros.
5. **Lugares**: todos los de la leyenda se ven en alguna lámina. Si uno queda tapado, usa la vista `niveles` o `corte`.
6. **Ruido**: con zoom al 100 %, sin grano ni manchas. Si los hay, sube las muestras o usa Cycles.
7. **Coherencia**: el mismo azimut y el mismo estilo en toda una serie.

## Lo que no hace sola (y cómo resolverlo)

- **Fotomontaje sobre una foto real**: renderiza `--transparente` con la cámara que coincida con la foto (una vista
  propia en `VISTAS` con posición y lente) y monta encima.
- **Personas, carros o vegetación detallada**: agrégalos en `detalles.py` (ver `mapa-modelo-blender`). Hay piezas en el caso de origen.
- **Arte real en las pantallas**: reemplaza `texturas/led_*.jpg` y reconstruye el modelo.
