# Modelos 3D por código

```bash
pip install trimesh numpy shapely manifold3d networkx scipy
python totm-3d/cad/build.py
```

Genera en `out/`:

| Archivo | Uso |
|---|---|
| `v1_esfera/v1_esfera-jade.glb`, `-ambar.glb` | Presentación / web (con colores y luz emisiva) |
| `v1_esfera/v1_esfera-cuerpo.stl` | Impresión (cuerpo exterior sólido) |
| `v2_totem/v2_totem-jade.glb`, `-ambar.glb` | Presentación; en ámbar solo se enciende la capa "secretos" |
| `v2_totem/v2_totem-cuerpo.stl` | Impresión (cuerpo exterior sólido) |

Todas las medidas son variables al inicio de `build_sphere()` y `build_totem()`: cambiar un número y volver a correr.

Es la versión base para decidir la forma. Falta, para imprimir el prototipo real: vaciar el interior (pared 2.5 mm), dividir en piezas, canal para la tira LED y soportes para la placa de 85 × 56 mm.
