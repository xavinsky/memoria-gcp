"""Schéma d'infrastructure décrit en YAML (front matter `schema:`) → SVG inline + légende.

Description :
  size: [largeur, hauteur]                      (viewBox, 760 x 300 par défaut)
  zones:                                        cadres pointillés (projet GCP, VPC, on-premise...)
    - {label: Projet GCP, x: 170, y: 16, w: 574, h: 268}
  nodes:                                        composants, référencés par leur clé
    bq: {label: BigQuery, sub: entrepôt, icon: produits/bigquery, focus: true,
         x: 400, y: 110, w: 150, h: 60}
  flows:                                        flux de données, numérotés dans l'ordre de la liste
    - {from: gcs, to: bq, text: "Chargement des fichiers", from_side: right, to_side: left}

Les côtés de départ et d'arrivée sont déduits des positions relatives ; `from_side` / `to_side`
(left, right, top, bottom) les imposent, `offset` décale le point d'accroche le long du côté.
Le tracé est orthogonal (coudes à angle droit), le numéro de l'étape est posé sur le segment
central. Le style (couleurs, polices) vient des classes CSS arch-* de www/style.css.
"""

import html

NODE_W, NODE_H, ICON = 140, 56, 26
# Largeur moyenne d'un caractère : libellé (serif gras 13 px), sous-titre (mono 10 px)
LABEL_CHAR, SUB_CHAR = 7.4, 6.1
NODE_KEYS = {"label", "sub", "icon", "x", "y", "w", "h", "focus", "external"}


def esc(text):
    return html.escape(str(text), quote=True)


def anchor(node, side, offset=0):
    x, y, w, h = node["x"], node["y"], node.get("w", NODE_W), node.get("h", NODE_H)
    return {
        "left": (x, y + h / 2 + offset),
        "right": (x + w, y + h / 2 + offset),
        "top": (x + w / 2 + offset, y),
        "bottom": (x + w / 2 + offset, y + h),
    }[side]


def auto_sides(a, b):
    ax, ay = a["x"] + a.get("w", NODE_W) / 2, a["y"] + a.get("h", NODE_H) / 2
    bx, by = b["x"] + b.get("w", NODE_W) / 2, b["y"] + b.get("h", NODE_H) / 2
    gap_x = abs(bx - ax) - (a.get("w", NODE_W) + b.get("w", NODE_W)) / 2
    gap_y = abs(by - ay) - (a.get("h", NODE_H) + b.get("h", NODE_H)) / 2
    if gap_x >= gap_y:
        return ("right", "left") if bx > ax else ("left", "right")
    return ("bottom", "top") if by > ay else ("top", "bottom")


def route(p1, side1, p2, side2):
    """Points d'un tracé orthogonal entre deux points d'accroche."""
    (x1, y1), (x2, y2) = p1, p2
    horizontal1 = side1 in ("left", "right")
    horizontal2 = side2 in ("left", "right")
    if horizontal1 and horizontal2:
        if abs(y1 - y2) < 0.5:
            return [p1, p2]
        mx = (x1 + x2) / 2
        return [p1, (mx, y1), (mx, y2), p2]
    if not horizontal1 and not horizontal2:
        if abs(x1 - x2) < 0.5:
            return [p1, p2]
        my = (y1 + y2) / 2
        return [p1, (x1, my), (x2, my), p2]
    if horizontal1:
        return [p1, (x2, y1), p2]
    return [p1, (x1, y2), p2]


def midpoint(points):
    """Milieu du plus long segment : là où le numéro d'étape gêne le moins."""
    best = max(zip(points, points[1:]), key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
    (x1, y1), (x2, y2) = best
    return (x1 + x2) / 2, (y1 + y2) / 2


def check_zones(spec, nodes, source):
    """Un nœud est soit entièrement dans une zone, soit entièrement dehors : à cheval sur le
    pointillé, le schéma ne dit plus si le composant appartient au périmètre."""
    for key, node in nodes.items():
        x1, y1 = node["x"], node["y"]
        x2, y2 = x1 + node.get("w", NODE_W), y1 + node.get("h", NODE_H)
        for zone in spec.get("zones", []):
            zx1, zy1 = zone["x"], zone["y"]
            zx2, zy2 = zx1 + zone["w"], zy1 + zone["h"]
            overlaps = x1 < zx2 and x2 > zx1 and y1 < zy2 and y2 > zy1
            inside = zx1 <= x1 and x2 <= zx2 and zy1 <= y1 and y2 <= zy2
            if overlaps and not inside:
                raise ValueError(
                    f"{source}: schéma, nœud {key} à cheval sur la zone « {zone['label']} »")


def render(spec, uid, source):
    width, height = spec.get("size", [760, 300])
    nodes = spec.get("nodes", {})
    marker = f"{uid}-arrow"
    out = [
        f'<svg class="arch" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Schéma d\'intégration">',
        f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse"><path class="arch-arrow" d="M0,0 L10,5 L0,10 z"/>'
        f"</marker></defs>",
    ]
    for zone in spec.get("zones", []):
        out.append(
            f'<rect class="arch-zone" x="{zone["x"]}" y="{zone["y"]}" width="{zone["w"]}" height="{zone["h"]}"/>'
            f'<text class="arch-zone-label" x="{zone["x"] + 10}" y="{zone["y"] + 16}">{esc(zone["label"])}</text>'
        )
    check_zones(spec, nodes, source)
    flows_svg, steps_svg, legend = [], [], []
    for i, flow in enumerate(spec.get("flows", []), start=1):
        try:
            a, b = nodes[flow["from"]], nodes[flow["to"]]
        except KeyError as err:
            raise ValueError(f"{source}: schéma, nœud inconnu {err}") from None
        s1, s2 = auto_sides(a, b)
        s1, s2 = flow.get("from_side", s1), flow.get("to_side", s2)
        p1 = anchor(a, s1, flow.get("from_offset", flow.get("offset", 0)))
        p2 = anchor(b, s2, flow.get("to_offset", flow.get("offset", 0)))
        points = route(p1, s1, p2, s2)
        d = "M" + " L".join(f"{x:g},{y:g}" for x, y in points)
        dash = " arch-flow-control" if flow.get("control") else ""
        flows_svg.append(f'<path class="arch-flow{dash}" d="{d}" marker-end="url(#{marker})"/>')
        mx, my = midpoint(points)
        steps_svg.append(
            f'<circle class="arch-step" cx="{mx:g}" cy="{my:g}" r="10"/>'
            f'<text class="arch-step-text" x="{mx:g}" y="{my + 4:g}">{i}</text>'
        )
        legend.append(flow["text"])
    for key, node in nodes.items():
        unknown = set(node) - NODE_KEYS
        if unknown:
            # typiquement une valeur non guillemetée contenant une virgule dans un mapping YAML {…}
            raise ValueError(f"{source}: schéma, nœud {key}, clés inconnues {sorted(unknown)}")
        x, y = node["x"], node["y"]
        w, h = node.get("w", NODE_W), node.get("h", NODE_H)
        cls = "arch-node" + (" focus" if node.get("focus") else "") + (" external" if node.get("external") else "")
        out_node = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}"/>']
        tx = x + 12
        text_start = 44 if node.get("icon") else 12
        needed = text_start + max(len(node["label"]) * LABEL_CHAR, len(node.get("sub", "")) * SUB_CHAR) + 8
        if needed > w:
            raise ValueError(f"{source}: schéma, nœud {key} trop étroit pour son texte (w={w}, il faut ~{needed:.0f})")
        if node.get("icon"):
            out_node.append(
                f'<image href="icons/{node["icon"]}.svg" x="{x + 10}" y="{y + (h - ICON) / 2:g}" '
                f'width="{ICON}" height="{ICON}"/>'
            )
            tx = x + 44
        label_y = y + h / 2 + (0 if node.get("sub") else 5)
        out_node.append(f'<text class="arch-label" x="{tx}" y="{label_y:g}">{esc(node["label"])}</text>')
        if node.get("sub"):
            out_node.append(f'<text class="arch-sub" x="{tx}" y="{label_y + 15:g}">{esc(node["sub"])}</text>')
        out.append("".join(out_node))
    out[len(spec.get("zones", [])) + 2:len(spec.get("zones", [])) + 2] = flows_svg
    out.extend(steps_svg)
    out.append("</svg>")
    legend_html = "".join(f"<li>{esc(text)}</li>" for text in legend)
    return (
        '<figure class="block-diagram arch-figure">' + "".join(out)
        + (f'<ol class="arch-legend">{legend_html}</ol>' if legend else "")
        + "</figure>\n"
    )
