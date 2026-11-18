"""Render the proposed-model graphs of the MAESTRO graph artifact as PNG files.

    python figures/v0.2.0/scripts/render.py

Input: the class and property model tools/gen_graph.py derives from the Turtle modules
(one entry per module with its classes, subclass links and object properties).

Outputs (in figures/v0.2.0/): src/*.gv (Graphviz sources), png/*.png and svg/*.svg of the
two proposed-model figures. Needs Graphviz `dot` on PATH and Pillow.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import subprocess
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

HERE = Path(__file__).resolve().parent                     # figures/v0.2.0/scripts
PKG = HERE.parents[2]
SRC, PNG, SVG = HERE.parent / "src", HERE.parent / "png", HERE.parent / "svg"
sys.path.insert(0, str(PKG / "tools"))
DPI_SCHEMA = 80    # the proposed model is very large; 80 dpi keeps it near 7000 px wide

# ---------------------------------------------------------------- proposed model

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def node_label(name: str, dps: list[str]) -> str:
    rows = ""
    if dps:
        rows = ('<HR/><TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#555555">'
                + '<BR ALIGN="LEFT"/>'.join(esc(d) for d in dps) + "</FONT></TD></TR>")
    return ('<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3"><TR><TD ALIGN="CENTER"><B>'
            + esc(name) + "</B></TD></TR>" + rows + "</TABLE>>")


def build_proposed(model: dict, layers: set[str], title: str) -> str:
    mods = [m for m in model["modules"] if m["layer"] in layers]
    visible = {c[0] for m in mods for c in m["classes"]}
    out = ["digraph MAESTRO_HHM_Core {",
           'rankdir=LR; compound=true; nodesep=0.3; ranksep=0.85; fontname="Helvetica"; fontsize=18; newrank=true;'
           ' labelloc="t"; label="' + title + '";',
           'node [shape=box style="rounded,filled" fillcolor="#f9f9fb" fontname="Helvetica" fontsize=10 margin="0.08,0.04"];',
           'edge [fontname="Helvetica" fontsize=8 arrowsize=0.7];']
    edges = []
    for m in mods:
        style = {"core": "rounded", "module": "rounded,dashed"}.get(m["layer"], "rounded,dotted")
        if not m["classes"]:
            continue
        out.append(f'subgraph cluster_{m["id"]} {{ label="{m["title"]}\\n{m["file"]}"; color="{m["color"]}"; '
                   f'fontcolor="{m["color"]}"; style="{style}"; penwidth=1.4;')
        for c in m["classes"]:
            name, dps = c[0], c[1]
            fill = "#e8f1ff" if len(c) > 2 and c[2] else "#f9f9fb"
            out.append(f'  {name} [label={node_label("maestro:" + name, dps)} color="{m["color"]}" fillcolor="{fill}"];')
        if m.get("ext"):
            note = esc("\\n".join(m["ext"])).replace('"', '\\"')
            out.append(f'  EXT_{m["id"]} [shape=note fillcolor="#fff7ed" color="#c2410c" fontsize=8 label="{note}"];')
            out.append(f'  {m["classes"][0][0]} -> EXT_{m["id"]} [style=dotted color="#c2410c" arrowhead=none];')
        out.append("}")
        for a, b in m.get("sub", []):
            if a in visible and b in visible:
                edges.append(f'{a} -> {b} [arrowhead=empty label="subClassOf" color="{m["color"]}" penwidth=1.2];')
        for p in m["props"]:
            name, d, r, style_ = p[0], p[1], p[2], p[3]
            if d in visible and r in visible:
                edges.append(f'{d} -> {r} [label="{name}" color="{m["color"]}" fontcolor="{m["color"]}"'
                             + (f" style={style_}" if style_ else "") + "];")
    return "\n".join(out + edges + ["}"])


# ---------------------------------------------------------------- driver

def dot(name: str, text: str, dpi: int = DPI_SCHEMA, svg: bool = False) -> Path:
    exe = shutil.which("dot")
    if not exe:
        raise SystemExit("Graphviz `dot` not found on PATH")
    gv, png = SRC / f"{name}.gv", PNG / f"{name}.png"
    gv.write_text(text, encoding="utf-8")
    subprocess.run([exe, "-Tpng", f"-Gdpi={dpi}", str(gv), "-o", str(png)], check=True)
    with Image.open(png) as im:
        print(f"  {png.relative_to(HERE.parent.parent)}  {im.width} x {im.height}")
    if svg:
        out = subprocess.run([exe, "-Tsvg", str(gv)], check=True, capture_output=True, text=True, encoding="utf-8").stdout
        out = re.sub(r"<!DOCTYPE[^>]*>\s*", "", out)   # no DTD, so the SVG can be published as an artifact file
        SVG.mkdir(exist_ok=True)
        (SVG / f"{name}.svg").write_text(out, encoding="utf-8")
        print(f"  {(SVG / f'{name}.svg').relative_to(HERE.parent.parent)}")
    return png


def proposed_model() -> dict:
    """The package model from tools/gen_graph.py. The subClassOf edges to maestro:ValueSet cross every
    cluster, so they are left out here (figure 13 draws them) and named in a note instead."""
    import gen_graph
    model = gen_graph.build_model()
    for m in model["modules"]:
        m["sub"] = [pair for pair in m["sub"] if pair[1] != "ValueSet"]
        if m["id"] == "resource":
            m["ext"] = list(m["ext"]) + ["ValueSet: superclass of every value-set class (edges in figure 13)"]
    return model


def main() -> None:
    for d in (PNG, SRC, SVG):
        d.mkdir(exist_ok=True)
    model = proposed_model()
    print("Proposed MAESTRO")
    dot("proposed-maestro",
        build_proposed(model, {"core", "module"},
                       "MAESTRO: seven HHM-Core clusters plus runtime, energy, maintenance and MaaS modules"), DPI_SCHEMA, svg=True)
    dot("proposed-maestro-with-extensions",
        build_proposed(model, {"core", "module", "ext"},
                       "MAESTRO, with the extension modules (OPC UA, digital twin, DTDL, REST, ISA-95, AutomationML)"), DPI_SCHEMA, svg=True)


if __name__ == "__main__":
    main()
