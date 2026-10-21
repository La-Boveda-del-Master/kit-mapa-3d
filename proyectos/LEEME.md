# proyectos/

Cada lugar nuevo va en su propia carpeta. Créala con `python pipeline/nuevo_proyecto.py <id> "Nombre"`.

```
proyectos/<id>/
  entrada/        lo que entrega la persona: plano (PDF, DXF o imagen), fotos, logo, lista de espacios
  plano.json      cómo leer el plano: regiones y reglas (ver docs/FORMATO-MAPA.md)
  mapa.json       el lugar: marca, niveles, edificios, muros, espacios, zonas, objetos, lugares
  detalles.py     (opcional) geometría propia que el constructor genérico no hace
  salida/         lo generado: plano_m.json, modelo.blend, renders/, láminas, web/, video
```

Git ignora estas carpetas para que el material de cada persona no se suba sin querer al kit. Para versionar un
proyecto, crea un repo propio o quita la regla `proyectos/*/` del `.gitignore` en tu copia.
