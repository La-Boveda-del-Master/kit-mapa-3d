# Qué plano sirve y cómo prepararlo

| Formato | Qué tan bueno | Qué hacer |
|---|---|---|
| **DXF** | El mejor. Viene en unidades reales, con capas y textos | `extraer_plano.py inspeccionar plano.dxf` |
| **DWG** (AutoCAD) | El mismo dibujo, en formato cerrado | Convertir a DXF (abajo) |
| **PDF vectorial** (exportado de CAD, Illustrator o Revit) | Muy bueno. Trae líneas, rellenos y textos; hay que calibrar la escala | `extraer_plano.py inspeccionar plano.pdf` |
| **PDF escaneado** (al hacer zoom se pixela) | Es una imagen dentro de un PDF | Tratarlo como imagen |
| **Imagen** (JPG, PNG, captura, foto derecha) | Buena si está derecha y hay una medida conocida | `calibrar_imagen.py` |
| **Foto en perspectiva o croquis a mano** | Aproximada | Enderezar la foto, o dibujar en `mapa.json` con las medidas que dé la persona |
| **SketchUp, Revit, IFC** | Ya está en 3D | Exportar las plantas a DXF o PDF por piso y seguir el camino normal |

## De DWG a DXF (gratis)

- **ODA File Converter** (Windows, macOS, Linux), de opendesign.com: se elige la carpeta de entrada y la de salida,
  versión DXF 2018, y se convierte.
- **LibreCAD** o **QCAD**: abrir el DWG y guardar como DXF.
- **AutoCAD**, si la persona lo tiene: `GUARDARCOMO` → DXF.

## Antes de exportar desde CAD (para quien tenga el archivo)

- **Explotar los bloques** de mobiliario que se quieran ver. El kit no lee bloques (INSERT).
- Dejar **una capa por tipo de cosa**: contorno del edificio, muros, espacios (polilíneas cerradas), textos,
  mobiliario y zonas (jardín, parqueo).
- Que los espacios sean **polilíneas cerradas** con su código o nombre escrito **adentro**.
- Si hay varios pisos en el mismo archivo, que estén separados y con un elemento común (ascensor o escalera) para alinearlos.

## Imagen: cómo sacarle el máximo

- Que esté **derecha** (vista de planta, no en perspectiva) y lo más grande posible.
- Con una **medida conocida**: una cota del plano, una puerta (≈ 0,9 m), un puesto de parqueo (2,5 × 5 m) o la
  fachada medida en Google Maps.
- `calibrar_imagen.py` genera una cuadrícula en metros encima. Con ella se leen las esquinas en metros, y el `calco`
  pone la imagen bajo el modelo para comprobar.

## Material de apoyo que mejora el resultado

- **Fotos de fachadas e interiores**: para materiales, alturas y colores.
- **Plano oficial o ficha del lugar**: para validar medidas.
- **Logo y colores de marca.**
- **Lista de espacios con su código**, en Excel o CSV: nombre, categoría y detalle de cada uno.
