#!/usr/bin/env python3
"""Modelos 3D paramétricos de TOTM, sin IA: medidas exactas y gratis.

  python cad/build.py            # genera las dos versiones en cad/out/

V1 · Esfera: esfera de 140 mm con ranura de luz y abertura trasera para los puertos.
V2 · Tótem:  columna de 4 segmentos; cada anillo de luz es una capa de seguridad.

Unidades en mm. Se modela con Z hacia arriba y el frente hacia -Y; al exportar
a glTF se rota a Y arriba. Requiere: trimesh, numpy, shapely, manifold3d.
"""

from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box
from trimesh.visual.material import PBRMaterial

OUT = Path(__file__).resolve().parent / "out"
SECTIONS = 160

BONE = (245, 243, 239)
JADE = (63, 163, 124)
AMBER = (232, 163, 61)
PCB = (22, 74, 46)
METAL = (190, 192, 196)


# ---------- utilidades ----------

def revolve(profile):
    """Sólido de revolución alrededor de Z a partir de puntos (radio, z)."""
    return trimesh.creation.revolve(np.asarray(profile, float), sections=SECTIONS)


def ring(r_in, r_out, z0, z1):
    m = trimesh.creation.annulus(r_min=r_in, r_max=r_out, height=z1 - z0, sections=SECTIONS)
    return m.apply_translation((0, 0, (z0 + z1) / 2))


def rounded_box(w, h, d, r):
    """Caja de w (x) × h (z) × d (y) con esquinas redondeadas en la cara XZ."""
    poly = box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, resolution=12)
    m = trimesh.creation.extrude_polygon(poly, d)  # extruye en Z
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))  # Z→-Y
    return m.apply_translation((0, d / 2, 0))


def material(rgb, emissive=None, rough=0.85, metal=0.0):
    return PBRMaterial(
        baseColorFactor=[*rgb, 255],
        metallicFactor=metal,
        roughnessFactor=rough,
        emissiveFactor=[c / 255 for c in emissive] if emissive else None,
    )


def paint(mesh, mat):
    mesh.visual = trimesh.visual.TextureVisuals(material=mat)
    return mesh


# ---------- letras TOTM (misma geometría que brand/totm-wordmark-*.svg) ----------
# Cada glifo en una caja de 100 × 100 con origen abajo a la izquierda.

def glyph(ch):
    if ch == "T":
        return box(0, 86, 72, 100).union(box(29, 0, 43, 100)), 72
    if ch == "O":
        return Point(50, 50).buffer(50, 64).difference(Point(50, 50).buffer(36, 64)), 100
    if ch == "M":
        pts = [(0, 100), (0, 0), (16, 0), (50, 52), (84, 0), (100, 0), (100, 100), (86, 100),
               (86, 24), (56, 70), (44, 70), (14, 24), (14, 100)]
        return Polygon([(x, 100 - y) for x, y in pts]), 100
    raise ValueError(ch)


def letter_solid(ch, height, depth):
    """Letra extruida en -Y, centrada en X y Z, de `height` mm de alto."""
    poly, width = glyph(ch)
    s = height / 100
    poly = trimesh.path.polygons.transform_polygon(poly, np.array([[s, 0, -width * s / 2], [0, s, -height / 2], [0, 0, 1]]))
    m = trimesh.creation.extrude_polygon(poly, depth)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    return m  # ocupa y ∈ [-depth, 0]


def engrave(body, letters, surface_y, relief=0.8):
    """Graba letras (lista de (char, z, altura)) en el frente (-Y) del cuerpo."""
    inlays = []
    for ch, z, h in letters:
        cutter = letter_solid(ch, h, 20).apply_translation((0, surface_y(z) + 20 - relief, z))
        body = body.difference(cutter)
        if ch == "O":  # la O es un anillo de color, como en el logo
            inlay = letter_solid(ch, h, 20).apply_translation((0, surface_y(z) + 20 - relief * 0.4, z))
            inlays.append(inlay)
    return body, inlays


# ---------- Raspberry Pi 2B (simplificada) ----------

def rpi_ports_edge():
    """Borde de puertos de la Pi 2B: 2 × USB-A dobles + Ethernet. Sin USB-C."""
    parts = []
    usb = (13.1, 17.0, 15.6)  # ancho x, fondo y, alto z de cada bloque doble
    eth = (15.9, 21.0, 13.5)
    for x in (-17.0, 1.0):
        parts.append(trimesh.creation.box(usb).apply_translation((x, 0, usb[2] / 2)))
    parts.append(trimesh.creation.box(eth).apply_translation((19.5, -2, eth[2] / 2)))
    return trimesh.util.concatenate(parts)


# ---------- V1 · Esfera ----------

def build_sphere(light):
    R, groove_h, groove_d = 70.0, 8.0, 3.0
    base_r, base_h = 34.0, 7.0
    cz = base_h + R - 4.0                # la esfera se hunde 4 mm en la base
    g0, g1 = cz + 12.0, cz + 12.0 + groove_h  # ranura un poco sobre el ecuador

    # perfil de la esfera con la ranura de luz
    prof = [(0.0, cz - R)]
    for a in np.linspace(-np.pi / 2, np.pi / 2, 181):
        z = cz + R * np.sin(a)
        r = R * np.cos(a)
        if g0 <= z <= g1:
            r -= groove_d
        prof.append((max(r, 0.0), z))
    # bordes verticales limpios en la ranura
    rr0 = np.sqrt(R ** 2 - (g0 - cz) ** 2)
    rr1 = np.sqrt(R ** 2 - (g1 - cz) ** 2)
    prof = [p for p in prof if not (g0 - 0.6 < p[1] < g1 + 0.6)]
    prof += [(rr0, g0), (rr0 - groove_d, g0), (rr1 - groove_d, g1), (rr1, g1)]
    prof = sorted(prof, key=lambda p: p[1])
    prof[-1] = (0.0, cz + R)
    shell = revolve(prof)

    base = revolve([(0, 0), (base_r - 2, 0), (base_r, 2), (base_r, base_h), (0, base_h)])
    body = shell.union(base)

    # abertura trasera (+Y) en la mitad inferior, con la Pi detrás
    cut_w, cut_h, cut_z = 58.0, 24.0, cz - 30.0
    cutter = rounded_box(cut_w, cut_h, 40, 6).apply_translation((0, R - 22, cut_z))
    pocket = rounded_box(cut_w - 1, cut_h - 1, 30, 5.5).apply_translation((0, R - 40, cut_z))
    body = body.difference(cutter.union(pocket))

    # grabado TOTM vertical en el frente, mitad inferior; la O en color de estado
    def front_y(z):
        return -np.sqrt(max(R ** 2 - (z - cz) ** 2, 1.0))
    letters = [("T", cz - 8, 9), ("O", cz - 20, 9), ("T", cz - 32, 9), ("M", cz - 44, 9)]
    body, inlays = engrave(body, letters, front_y)

    # luz: anillo dentro de la ranura
    band = ring(rr0 - groove_d - 2, rr0 - groove_d + 0.6, g0 + 0.3, g1 - 0.3)

    # placa y puertos visibles por la abertura
    board = trimesh.creation.box((56, 3, cut_h + 4)).apply_translation((0, R - 40, cut_z))
    ports = rpi_ports_edge().apply_translation((0, R - 29, cut_z - 8))

    return {
        "cuerpo": paint(body, material(BONE)),
        "luz": paint(band, material(light, emissive=light, rough=0.4)),
        "logo-o": paint(trimesh.util.concatenate(inlays), material(light, emissive=light)),
        "placa": paint(board, material(PCB, rough=0.6)),
        "puertos": paint(ports, material(METAL, rough=0.35, metal=0.8)),
    }


# ---------- V2 · Tótem ----------

def build_totem(lights):
    """lights: color de cada anillo de abajo arriba (comandos, red, secretos)."""
    H = 220.0
    r_bot, r_top = 38.0, 34.0             # se afina hacia arriba
    plinth_r, plinth_h = 33.0, 5.0        # zócalo retranqueado: la columna "flota"
    ring_h, ring_d = 5.0, 2.5
    # alturas de los anillos (centro); el segmento base aloja la Pi parada
    ring_z = [plinth_h + 95.0, plinth_h + 145.0, plinth_h + 185.0]

    def radius(z):
        t = (z - plinth_h) / (H - plinth_h)
        return r_bot + (r_top - r_bot) * t

    prof = [(0, plinth_h), (radius(plinth_h) - 1.5, plinth_h), (radius(plinth_h), plinth_h + 1.5)]
    for zc in ring_z:
        a, b = zc - ring_h / 2, zc + ring_h / 2
        prof += [(radius(a), a), (radius(a) - ring_d, a), (radius(b) - ring_d, b), (radius(b), b)]
    rt = radius(H)
    prof += [(rt, H - 5), (rt - 0.6, H - 2), (rt - 2, H - 0.5), (rt - 4, H), (0, H)]  # borde superior suave
    column = revolve(prof)
    plinth = revolve([(0, 0), (plinth_r, 0), (plinth_r, plinth_h + 1), (0, plinth_h + 1)])
    body = column.union(plinth)

    # salida de cables por detrás del zócalo (USB/Ethernet miran hacia abajo)
    slot = rounded_box(30, 10, 30, 3).apply_translation((0, plinth_r - 8, 1.5))
    body = body.difference(slot)

    # una letra por segmento, de arriba abajo: T · O · T · M
    seg_mid = [(ring_z[2] + H) / 2, (ring_z[1] + ring_z[2]) / 2, (ring_z[0] + ring_z[1]) / 2, ring_z[0] - 30]
    letters = [("T", seg_mid[0], 13), ("O", seg_mid[1], 13), ("T", seg_mid[2], 13), ("M", seg_mid[3], 13)]
    body, inlays = engrave(body, letters, lambda z: -radius(z))

    parts = {"cuerpo": paint(body, material(BONE))}
    for i, (zc, color) in enumerate(zip(ring_z, lights)):
        r_in = radius(zc + ring_h / 2) - ring_d
        band = ring(r_in - 2, r_in + 0.6, zc - ring_h / 2 + 0.3, zc + ring_h / 2 - 0.3)
        parts[f"luz-{['comandos', 'red', 'secretos'][i]}"] = paint(band, material(color, emissive=color, rough=0.4))
    parts["logo-o"] = paint(trimesh.util.concatenate(inlays), material(JADE, emissive=JADE))
    return parts


# ---------- exportación ----------

Z_UP_TO_Y_UP = trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0))


def export(name, parts):
    folder = OUT / name.split("-")[0]
    folder.mkdir(parents=True, exist_ok=True)
    scene = trimesh.Scene()
    for key, mesh in parts.items():
        # separa normales en aristas vivas para que el grabado no se vea "derretido"
        shaded = trimesh.graph.smooth_shade(mesh, angle=np.radians(25))
        shaded.visual = mesh.visual.copy()
        scene.add_geometry(shaded, node_name=key, geom_name=key)
    scene.apply_transform(Z_UP_TO_Y_UP)
    scene.export(folder / f"{name}.glb")
    body = parts["cuerpo"]
    if "-ambar" not in name:  # la forma es la misma; un solo STL por versión
        body.export(folder / f"{name.split('-')[0]}-cuerpo.stl")
    ext = body.extents
    print(f"{name:<22} {ext[0]:.0f} × {ext[1]:.0f} × {ext[2]:.0f} mm  watertight={body.is_watertight}")


def main():
    export("v1_esfera-jade", build_sphere(JADE))
    export("v1_esfera-ambar", build_sphere(AMBER))
    export("v2_totem-jade", build_totem([JADE, JADE, JADE]))
    export("v2_totem-ambar", build_totem([JADE, JADE, AMBER]))  # alerta solo en la capa "secretos"


if __name__ == "__main__":
    main()
