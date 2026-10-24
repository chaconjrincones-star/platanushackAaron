# TOTM

**El tótem de tus agentes.** Un amuleto de seguridad físico (Raspberry Pi 2B en una esfera) que corre un agente local y actúa como capa de seguridad previa a cualquier acceso: vigila lo que hacen los agentes de IA y alerta ante cualquier mal funcionamiento.

Platanus Hack 26 Caracas · track AI Security.

| Carpeta | Contenido |
|---|---|
| [`brand/`](brand/) | Logos de las dos versiones y página comparativa `brand/index.html`. |
| [`app/`](app/) | Prototipo de UI responsive (desktop con sidebar, móvil con tab bar), con selector V1/V2. |
| [`totm-3d/cad/`](totm-3d/cad/) | Modelos 3D paramétricos por código (gratis, medidas exactas): `.glb` y `.stl`. |
| [`viewer/`](viewer/) | Visor 3D en el navegador (three.js) para girar los modelos. |
| [`totm-3d/`](totm-3d/) | Alternativa con IA: generación con la API de Meshy. |

## Dos versiones

| | V1 · Esfera | V2 · Tótem |
|---|---|---|
| Forma | Esfera Ø 140 mm sobre base plana | Columna Ø 76 → 68 mm, 220 mm de alto, 4 segmentos |
| Luz | Una banda: estado global | Tres anillos = tres capas (comandos · red · secretos); la alerta enciende solo la capa afectada |
| Logo | Wordmark TOTM + isotipo esfera | Wordmark TOTM + isotipo columna de segmentos |
| Pi 2B | Puertos visibles por la abertura trasera | Placa parada; cables salen por debajo |

Para comparar todo junto: `python3 -m http.server 8000` en la raíz y abrir
- http://localhost:8000/brand/ — logos y renders de las dos versiones
- http://localhost:8000/viewer/ — modelos 3D (botones V1/V2, protegido/alerta)
- http://localhost:8000/app/ — la app (selector V1/V2 arriba a la derecha)

## Paleta

| Uso | Color |
|---|---|
| Fondo / obsidiana | `#0B0B0C` |
| Cuerpo / hueso | `#F5F3EF` |
| Protegido / jade | `#3FA37C` |
| Alerta / ámbar | `#E8A33D` |

## App (prototipo)

Vistas: **Inicio** (estado del dispositivo; en V2 con el detalle por capa, métricas, actividad, agentes), **Actividad** (feed filtrable, detalle de cada acción), **Agentes** (permisos y carga), **Dispositivo** (specs de la Pi y ajustes). El botón *Simular alerta* cambia la luz y la UI a ámbar. Sigue el modo claro/oscuro del sistema. Los datos son de ejemplo en `app/app.js`.

