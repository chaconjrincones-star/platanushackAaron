# TOTM · modelo 3D con Meshy

Script para generar el modelo 3D del dispositivo TOTM (esfera de ~140 mm con banda de luz, Raspberry Pi 2B dentro) con la API de Meshy.

## Preparación

```bash
cd totm-3d
pip install -r requirements.txt
cp .env.example .env      # y pon tu MESHY_API_KEY (el archivo está en .gitignore)
```

Guarda las referencias en `refs/`:
- `refs/totm-esfera-led.png`: prototipo con la tira LED (construcción).
- `refs/totm-esfera-render.png`: render limpio (**referencia principal de estilo**).

## Comandos

```bash
python generate.py image refs/totm-esfera-render.png --name render-jade
python generate.py preview --prompt forma --name esfera-v1
python generate.py preview --prompt forma-rpi2b --name esfera-v2
python generate.py refine <preview_task_id> --texture jade  --name esfera-v1-jade
python generate.py refine <preview_task_id> --texture ambar --name esfera-v1-ambar
python generate.py status <task_id> [--download --name <variante>]
```

- `--prompt` / `--texture` aceptan un nombre de `prompts.json` o un texto literal (máx. 800 caracteres, se valida antes de enviar).
- Consulta el estado cada 5 s con un máximo de 15 min. Si se corta, recupera con `status <id> --download`.
- `429` → reintenta con backoff exponencial. `402` → se detiene: sin créditos. `401` → token inválido.
- El token nunca se imprime.

Cada variante queda en `models/<fecha>_<nombre>/` con `model.glb`, `model.stl`, `thumbnail.png` y `task.json` (id, endpoint, parámetros, créditos antes/después, estado final). Los `.glb`/`.stl` están ignorados por git por peso; para subir el final: `git add -f models/<carpeta>/model.glb`.

## Flujo para ahorrar créditos

1. 2–3 `preview` (baratas) + 1 `image` con la referencia principal.
2. Revisar los `thumbnail.png` y elegir la mejor forma.
3. `refine` solo de la elegida: primero `jade`, luego `ambar`.

## Notas de diseño

- Meshy no genera bien texto: el grabado **TOTM** (vertical, con la O en anillo jade) y `TOTM v1.1 · PROTOTYPE · MADE WITH RPI` se agregan en Blender (texto → malla → Boolean Difference). Ver `../brand/totm-vertical.svg`.
- Puertos de la Raspberry Pi 2B: 4 × USB-A, Ethernet, micro-USB, HDMI, jack 3.5 mm. **Sin USB-C**: revisar que el modelo elegido no lo muestre.
- Para imprimir: dividir por la ranura, pared ~2.5 mm, canal para la tira LED, soportes para la placa de 85 × 56 mm.
