# proyectos/

Cada recinto nuevo vive en su carpeta: `python pipeline/nuevo_proyecto.py <id> "Nombre"`.

```
proyectos/<id>/
  entrada/        lo que entrega la persona: plano.pdf, fotos, fichas técnicas
  plano.json      regiones y reglas para extraer el PDF
  recinto.json    el recinto: niveles, edificios, zonas, stands, objetos, pines
  detalles.py     (opcional) geometría propia que el constructor genérico no hace
  salida/         lo generado: plano_m.json, modelo.blend, web/, renders/
```

Git ignora estas carpetas para que el material de cada persona no se suba sin querer al kit.
Para versionar tu proyecto, crea un repo propio, o quita la regla `proyectos/*/` del `.gitignore` en tu copia.
