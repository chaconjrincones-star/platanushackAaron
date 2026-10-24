# TOTM

**El tótem de tus agentes.** Un amuleto de seguridad físico (Raspberry Pi 2B en una esfera) que corre un agente local y actúa como capa de seguridad previa a cualquier acceso: vigila lo que hacen los agentes de IA y alerta ante cualquier mal funcionamiento.

Platanus Hack 26 Caracas · track AI Security.

| Carpeta | Contenido |
|---|---|
| [`brand/`](brand/) | Logo: wordmark (O en anillo jade), isotipo de la esfera, versión vertical, ícono de app. Abrir `brand/index.html`. |
| [`app/`](app/) | Prototipo de UI responsive (desktop con sidebar, móvil con tab bar). Abrir `app/index.html`. |
| [`totm-3d/`](totm-3d/) | Generación del modelo 3D con la API de Meshy. |

## Paleta

| Uso | Color |
|---|---|
| Fondo / obsidiana | `#0B0B0C` |
| Cuerpo / hueso | `#F5F3EF` |
| Protegido / jade | `#3FA37C` |
| Alerta / ámbar | `#E8A33D` |

## App (prototipo)

Vistas: **Inicio** (estado del tótem, métricas, actividad, agentes), **Actividad** (feed filtrable, detalle de cada acción), **Agentes** (permisos y carga), **Dispositivo** (specs de la Pi y ajustes). El botón *Simular alerta* cambia la luz y la UI a ámbar. Sigue el modo claro/oscuro del sistema. Los datos son de ejemplo en `app/app.js`.

```bash
python3 -m http.server -d app 8000   # http://localhost:8000
```
