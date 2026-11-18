"""
MAESTRO - figure renderer.

Renders the figures of the package into ``figures/v0.2.0/png/`` in the house
style: muted palette, DejaVu Sans, rounded boxes with hairline borders, a
reserved title band, 300 DPI. The usual entry point is ``render_v020.py`` in
this folder, which also draws the artifact-style graphs and figures 13 to 16.

Matplotlib figures (rendered here):
    01-module-stack        umbrella, the twenty modules by layer, satellites
    04-standards-basis     every external link the modules make, by vocabulary
    06-maestro-alignment   where each module's definitions come from (MAESTRO 1.0)

Graphviz figures (``.gv`` under ``figures/v0.2.0/src/``, rendered with ``dot``):
    02-import-graph        generated here from the owl:imports of the modules
    03-hhm-schema          hand-curated class schema of the seven clusters + twin
    05-widget-cell         generated here from queries/fixtures/widget-cell/*.ttl
    07-beyond-clusters     hand-curated schema of runtime, energy, maintenance, maas

Figures 01, 02, 04, 05 and 06 are read from the package at render time, so
they follow the Turtle files rather than a hand-kept list. Figures 03 and 07
are hand-authored; ``--check`` verifies that every ``maestro:`` name they use is
declared in the package and is not a deprecated 0.1.0 name.

Usage (from the repository root, with rdflib and matplotlib installed):
    python figures/v0.2.0/scripts/render_figures.py
    python figures/v0.2.0/scripts/render_figures.py --check
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import OWL, RDF, RDFS, SKOS, DCTERMS

HERE = Path(__file__).resolve().parent          # figures/v0.2.0/scripts
FIG = HERE.parent                                # figures/v0.2.0/
PKG = FIG.parents[1]                             # package root
sys.path.insert(0, str(PKG / "tools"))
import common  # noqa: E402
from common import MODULES, module_path, parse  # noqa: E402
from gen_alignment import HHM_CLASSES, HHM_RELATIONS  # noqa: E402

MH_NS = common.MH_NS
MH = Namespace(MH_NS)
EX_NS = "https://w3id.org/maestro/examples/widget-cell#"

SRC = FIG / "src"
PNG = FIG / "png"
VERSION = str(next(parse(common.UMBRELLA_FILE).objects(common.ONTOLOGY_IRI, OWL.versionInfo)))


# ---------------------------------------------------------------------------
#  GLOBAL STYLE
# ---------------------------------------------------------------------------

PALETTE = {
    "ink":        "#1F2A36",
    "muted":      "#5C6B7A",
    "rule":       "#CFD8DC",
    "bg":         "#FFFFFF",
    "panel":      "#F7F9FB",

    "cat_core":   "#D6E4F0",
    "cat_mod":    "#C7E8D1",
    "cat_ext":    "#E0DAF0",
    "cat_umbr":   "#F4B860",
    "cat_gen":    "#EEF1F4",

    "hsu":        "#FDE2C7",
    "w3c":        "#E0DAF0",
    "other":      "#D6E4F0",
    "hook":       "#F3F4F6",
}

plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          10,
    "axes.edgecolor":     PALETTE["ink"],
    "axes.linewidth":     0.6,
    "savefig.dpi":        300,
    "savefig.facecolor":  PALETTE["bg"],
    "savefig.bbox":       "tight",
    "savefig.pad_inches": 0.25,
    "figure.facecolor":   PALETTE["bg"],
    "figure.dpi":         150,
})

TITLE_BAND = 1.5


@dataclass
class BoxStyle:
    fill: str = PALETTE["panel"]
    edge: str = PALETTE["ink"]
    lw:   float = 0.9
    pad:  float = 0.02
    rounding: float = 0.04


def draw_box(ax, x, y, w, h, *, label, sublabel=None, style=None,
             fontsize=10, fontweight="bold", subfontsize=8.5, text_color=None):
    style = style or BoxStyle()
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={style.pad},rounding_size={style.rounding}",
        linewidth=style.lw, edgecolor=style.edge, facecolor=style.fill))
    cx, cy = x + w / 2, y + h / 2
    text_color = text_color or PALETTE["ink"]
    if sublabel:
        ax.text(cx, cy + 0.13 * h, label, ha="center", va="center",
                fontsize=fontsize, fontweight=fontweight, color=text_color)
        ax.text(cx, cy - 0.20 * h, sublabel, ha="center", va="center",
                fontsize=subfontsize, color=PALETTE["muted"], style="italic")
    else:
        ax.text(cx, cy, label, ha="center", va="center",
                fontsize=fontsize, fontweight=fontweight, color=text_color)


def draw_arrow(ax, x1, y1, x2, y2, *, color=None, lw=1.0, style="-|>",
               curve=0.0, linestyle="-"):
    color = color or PALETTE["ink"]
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=12,
        linewidth=lw, color=color, linestyle=linestyle,
        connectionstyle=f"arc3,rad={curve}", zorder=2))


def setup_axes(ax, xlim, ylim, title=None, subtitle=None, title_band=TITLE_BAND):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    cx = (xlim[0] + xlim[1]) / 2
    if title:
        ax.text(cx, ylim[1] - title_band * 0.35, title, ha="center", va="center",
                fontsize=15, fontweight="bold", color=PALETTE["ink"])
    if subtitle:
        ax.text(cx, ylim[1] - title_band * 0.72, subtitle, ha="center",
                va="center", fontsize=10, color=PALETTE["muted"], style="italic")


def footnote(ax, x, y, text, fontsize=9.0):
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=PALETTE["muted"], style="italic", linespacing=1.4,
            bbox=dict(facecolor=PALETTE["panel"], edgecolor=PALETTE["rule"],
                      boxstyle="round,pad=0.45", lw=0.6))


def save(fig, name):
    PNG.mkdir(parents=True, exist_ok=True)
    out = PNG / f"{name}.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
#  PACKAGE MODEL (read once)
# ---------------------------------------------------------------------------

CLUSTER_NAME = {
    "resource": "Physical Resources", "skill": "Skills", "recipe": "Recipe / Planning",
    "product": "Product", "invocation": "Invocation Hooks",
    "policy": "Safety / Security / Policy", "execution": "Minimal Execution",
    "runtime": "Runtime state", "energy": "Energy", "maintenance": "Maintenance",
    "maas": "Manufacturing as a service",
    "digital-twin": "Digital twin", "opcua": "OPC UA", "isa88": "ISA-88 bridge",
    "isa95": "ISA-95 hierarchy", "automationml": "AutomationML topology",
    "dtdl": "DTDL", "rest": "REST", "prov": "PROV-O bridge", "odrl": "ODRL bridge",
}


def local(iri) -> str:
    s = str(iri)
    return s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]


def discover_modules() -> list[tuple[str, str]]:
    """MODULES from tools/common.py, plus any .ttl on disk it does not list."""
    listed = list(MODULES)
    known = set(listed)
    for layer in ("core", "modules", "ext"):
        for p in sorted((PKG / layer).glob("*.ttl")):
            if (layer, p.stem) not in known:
                listed.append((layer, p.stem))
    return listed


def load_modules() -> dict[tuple[str, str], Graph]:
    return {(l, s): parse(module_path(l, s)) for l, s in discover_modules()}


def declared_terms(g: Graph) -> set[URIRef]:
    out = set()
    for t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.NamedIndividual):
        out |= {s for s in g.subjects(RDF.type, t) if str(s).startswith(MH_NS)}
    return out


# ---------------------------------------------------------------------------
#  FIGURE 01 - Module stack
# ---------------------------------------------------------------------------

def fig_01_module_stack(graphs):
    layers = defaultdict(list)
    for (layer, stem) in graphs:
        layers[layer].append(stem)
    n = sum(len(v) for v in layers.values())
    n_shapes = len(list((PKG / "shacl").glob("*.ttl")))
    n_cq = len(list((PKG / "queries" / "cq").glob("*.rq")))

    fig, ax = plt.subplots(figsize=(14, 10.2))
    xlim, ylim = (0, 14), (0, 11.2)
    setup_axes(ax, xlim, ylim,
               title="MAESTRO — Module Stack",
               subtitle=f"{n} Turtle modules in one namespace (maestro:), "
                        "unified through maestro.ttl")

    PILL_H, PILL_GAP, HEADER_SPACE, CARD_PAD = 0.40, 0.09, 0.95, 0.22

    def card_height(k, cols):
        rows = (k + cols - 1) // cols
        return HEADER_SPACE + rows * PILL_H + (rows - 1) * PILL_GAP + CARD_PAD

    # umbrella
    ux0, uy0, uw, uh = 3.9, 8.55, 6.2, 0.95
    draw_box(ax, ux0, uy0, uw, uh, label="maestro.ttl",
             sublabel="umbrella  ·  https://w3id.org/maestro  ·  owl:imports every module",
             style=BoxStyle(fill=PALETTE["cat_umbr"], edge=PALETTE["ink"], lw=1.3),
             fontsize=12, subfontsize=8.6)
    ux, uy = ux0 + uw / 2, uy0

    def draw_card(x, y, w, h, header, subheader, color, pills, cols=1):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    facecolor=color, edgecolor=PALETTE["ink"], lw=0.9))
        ax.text(x + w / 2, y + h - 0.30, header, ha="center", va="top",
                fontsize=11, fontweight="bold", color=PALETTE["ink"])
        ax.text(x + w / 2, y + h - 0.62, subheader, ha="center", va="top",
                fontsize=8.0, color=PALETTE["muted"], style="italic")
        inner = 0.18
        col_w = (w - inner * (cols + 1)) / cols
        first_y = y + h - HEADER_SPACE
        for i, (stem, sub) in enumerate(pills):
            r, c = divmod(i, cols)
            px = x + inner + c * (col_w + inner)
            py = first_y - r * (PILL_H + PILL_GAP) - PILL_H
            ax.add_patch(FancyBboxPatch((px, py), col_w, PILL_H,
                                        boxstyle="round,pad=0.01,rounding_size=0.05",
                                        facecolor="white", edgecolor=PALETTE["rule"], lw=0.55))
            ax.text(px + 0.14, py + PILL_H / 2, stem, ha="left", va="center",
                    fontsize=8.8, fontweight="bold", color=PALETTE["ink"])
            ax.text(px + col_w - 0.14, py + PILL_H / 2, sub, ha="right", va="center",
                    fontsize=7.2, color=PALETTE["muted"], style="italic")
        return (x + w / 2, y + h)

    cards = [
        ("core/", "the seven HHM-Core v1 clusters, one file each",
         PALETTE["cat_core"], layers["core"], 1, 4.55),
        ("modules/", "concerns no HHM cluster covers",
         PALETTE["cat_mod"], layers["modules"], 1, 4.10),
        ("ext/", "extension points named by the HHM diagram",
         PALETTE["cat_ext"], layers["ext"], 1, 4.55),
    ]
    row_h = max(card_height(len(m), c) for _, _, _, m, c, _ in cards)
    row_y = uy0 - 0.75 - row_h
    x = 0.25
    pad = 0.25
    targets = []
    for header, sub, color, mods, cols, w in cards:
        pills = [(s, CLUSTER_NAME.get(s, "")) for s in mods]
        targets.append(draw_card(x, row_y, w, row_h, header, sub, color, pills, cols))
        x += w + pad

    for cx, cy in targets:
        off = cx - ux
        draw_arrow(ax, ux, uy, cx, cy, lw=0.75, color=PALETTE["muted"],
                   curve=0.06 if off > 0.5 else (-0.06 if off < -0.5 else 0))

    # satellites: hang off the umbrella without being imported by it
    sat_h = 1.55
    sat_y = row_y - 0.55 - sat_h
    sats = [
        ("alignment/   (generated)", PALETTE["cat_gen"],
         [("maestro-1.0.ttl", "skos:exactMatch · closeMatch"),
          ("hhm-core.ttl", "owl:equivalentClass · Property")],
         "imports the umbrella; never imported by it", 4.55),
        (f"shacl/   ({n_shapes} SHACL files, msh:)", PALETTE["cat_gen"],
         [("shacl-<module>.ttl", "cardinality · datatype · sh:in")],
         "one file per module group · gate 10", 4.10),
        (f"usecase-knowledge-graphs/widget-cell/   +   queries/cq/ ({n_cq})", PALETTE["cat_gen"],
         [("plant.ttl", "design time"), ("market.ttl", "MaaS tier"),
          ("runtime.ttl", "maestro:Snapshot")],
         "import the umbrella · competency questions cq01–cq15", 4.55),
    ]
    x = 0.25
    for header, color, pills, note, w in sats:
        ax.add_patch(FancyBboxPatch((x, sat_y), w, sat_h,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    facecolor=color, edgecolor=PALETTE["muted"], lw=0.8,
                                    linestyle="--"))
        ax.text(x + w / 2, sat_y + sat_h - 0.26, header, ha="center", va="top",
                fontsize=9.6, fontweight="bold", color=PALETTE["ink"])
        inner = 0.16
        cols = len(pills)
        col_w = (w - inner * (cols + 1)) / cols
        for i, (stem, sub) in enumerate(pills):
            px = x + inner + i * (col_w + inner)
            py = sat_y + 0.52
            ax.add_patch(FancyBboxPatch((px, py), col_w, 0.46,
                                        boxstyle="round,pad=0.01,rounding_size=0.05",
                                        facecolor="white", edgecolor=PALETTE["rule"], lw=0.55))
            ax.text(px + col_w / 2, py + 0.30, stem, ha="center", va="center",
                    fontsize=8.0, fontweight="bold", color=PALETTE["ink"])
            ax.text(px + col_w / 2, py + 0.13, sub, ha="center", va="center",
                    fontsize=6.8, color=PALETTE["muted"], style="italic")
        ax.text(x + w / 2, sat_y + 0.24, note, ha="center", va="center",
                fontsize=7.6, color=PALETTE["muted"], style="italic")
        x += w + pad

    foot_y = sat_y - 0.55
    footnote(ax, 7.0, foot_y,
             "core/resource.ttl is the import root; each module declares its own owl:imports and the graph is acyclic (gate 2).   "
             "Nothing here imports ontologies/ at the repository root.",
             fontsize=8.8)
    y_bottom = foot_y - 0.5
    ax.set_ylim(y_bottom, ylim[1])
    fig.set_size_inches(14, 10.2 * (ylim[1] - y_bottom) / (ylim[1] - ylim[0]))
    return save(fig, "01-module-stack")


# ---------------------------------------------------------------------------
#  FIGURE 02 - Import graph (Graphviz source generated from owl:imports)
# ---------------------------------------------------------------------------

LAYER_STYLE = {
    "core":    ("core/  —  HHM-Core v1 clusters", "#3B82F6", "#E8F0FA"),
    "modules": ("modules/  —  beyond the clusters", "#12A594", "#E4F4EE"),
    "ext":     ("ext/  —  extension points", "#8B5CF6", "#EFEAF8"),
}


def gv_id(stem: str) -> str:
    return "m_" + stem.replace("-", "_")


def gen_02_import_graph(graphs):
    stem_of = {str(common.module_iri(s)): (l, s) for l, s in graphs}
    edges = []
    for (l, s), g in graphs.items():
        iri = common.module_iri(s)
        for o in g.objects(iri, OWL.imports):
            if str(o) in stem_of:
                edges.append((s, stem_of[str(o)][1]))
    n_edges = len(edges)
    lines = [
        "// GENERATED by figures/v0.2.0/scripts/render_figures.py from the owl:imports",
        "// statements of the twenty modules. Do not edit; re-run the renderer.",
        "// Render: dot -Tpng figures/v0.2.0/src/02-import-graph.gv -o figures/v0.2.0/png/02-import-graph.png",
        "digraph HHM_Imports {",
        "  rankdir=BT; labelloc=\"t\"; fontname=\"Helvetica\"; nodesep=0.35; ranksep=0.6;",
        f"  label=\"MAESTRO  ·  owl:imports graph of the {len(graphs)} modules "
        f"({n_edges} edges, acyclic, root core/resource.ttl)\\n"
        "A → B  means  A owl:imports B.   The umbrella maestro.ttl imports all of them; "
        "the generated alignment files import the umbrella.\";",
        "  node [shape=box, style=\"rounded,filled\", fontname=\"Helvetica\", fontsize=10, "
        "color=\"#1F2A36\", penwidth=0.9];",
        "  edge [fontname=\"Helvetica\", fontsize=9, color=\"#5C6B7A\", arrowsize=0.8];",
    ]
    for layer, (title, color, fill) in LAYER_STYLE.items():
        lines += [f"  subgraph cluster_{layer} {{",
                  f"    label=\"{title}\"; color=\"{color}\"; style=\"rounded\"; "
                  "fontname=\"Helvetica\"; fontsize=11;"]
        for (l, s) in graphs:
            if l == layer:
                lab = f"{s}\\n{CLUSTER_NAME[s]}" if s in CLUSTER_NAME else s
                lines.append(f"    {gv_id(s)} [label=\"{lab}\", fillcolor=\"{fill}\"];")
        lines.append("  }")
    lines += [
        "  subgraph cluster_umbrella {",
        "    label=\"\"; color=\"#FFFFFF\";",
        "    umbrella [label=\"maestro.ttl\\numbrella · imports every module\", "
        "fillcolor=\"#F4B860\", penwidth=1.4];",
        "    align [label=\"alignment/maestro-1.0.ttl · alignment/hhm-core.ttl\\n"
        "(generated) import the umbrella\", fillcolor=\"#EEF1F4\", style=\"rounded,filled,dashed\"];",
        "    align -> umbrella [style=dashed];",
        "  }",
    ]
    for a, b in sorted(edges):
        lines.append(f"  {gv_id(a)} -> {gv_id(b)};")
    lines.append("}")
    out = SRC / "02-import-graph.gv"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


# ---------------------------------------------------------------------------
#  FIGURE 04 - Standards basis (every external link, by vocabulary)
# ---------------------------------------------------------------------------

VOCAB = [
    # namespace, display name, prefix label, pinned file under references/, family
    ("http://www.w3id.org/hsu-aut/PackML#",        "PackML",                  "PackML",     "hsu-packml.ttl",           "hsu"),
    ("http://www.w3id.org/hsu-aut/WADL#",          "WADL",                    "WADL",       "hsu-wadl.ttl",             "hsu"),
    ("http://www.w3id.org/hsu-aut/DINEN61360#",    "DIN EN 61360",            "DINEN61360", "hsu-dinen61360.ttl",       "hsu"),
    ("http://www.w3id.org/hsu-aut/VDI2206#",       "VDI 2206",                "VDI2206",    "hsu-vdi2206.ttl",          "hsu"),
    ("http://www.w3id.org/hsu-aut/ISO22400-2#",    "ISO 22400-2",             "ISO22400",   "hsu-iso22400-2.ttl",       "hsu"),
    ("http://www.hsu-ifa.de/ontologies/ISA88.01#", "ISA-88.01",               "ISA88",      "hsu-isa88.ttl",            "hsu"),
    ("http://www.w3id.org/hsu-aut/DINEN62264-2#",  "DIN EN 62264-2 (ISA-95)", "DINEN62264", "hsu-dinen62264-2.ttl",     "hsu"),
    ("http://www.w3id.org/hsu-aut/OpcUa#",         "OPC UA",                  "OpcUa",      "hsu-opcua.ttl",            "hsu"),
    ("https://w3id.org/hsu-aut/AutomationML#",     "AutomationML",            "AML",        "hsu-automationml.ttl",     "hsu"),
    ("https://schema.org/",                        "schema.org",              "schema",     "schemaorg-extract.ttl",    "other"),
    ("dtmi:",                                      "DTDL v3",                 "dtmi",       "dtdl-v3-classes.ttl",      "other"),
    ("http://www.w3.org/ns/prov#",                 "W3C PROV-O",              "prov",       "prov-o.ttl",               "w3c"),
    ("http://www.w3.org/ns/odrl/2/",               "W3C ODRL 2.2 core",       "odrl",       "odrl-core-profile-22.ttl", "w3c"),
]
MATCH_PREDS = {SKOS.exactMatch: "exactMatch", SKOS.closeMatch: "closeMatch",
               SKOS.relatedMatch: "relatedMatch", SKOS.broadMatch: "broadMatch",
               SKOS.narrowMatch: "narrowMatch"}
LOGICAL_PREDS = {RDFS.subClassOf: "subClassOf", RDFS.subPropertyOf: "subPropertyOf"}


def collect_links(graphs):
    """[(vocab index, module stem, kind, subject local, predicate label, object display)]"""
    rows = []
    for (l, s), g in graphs.items():
        for pred, plabel in list(MATCH_PREDS.items()) + list(LOGICAL_PREDS.items()):
            for subj, obj in g.subject_objects(pred):
                if not isinstance(obj, URIRef) or str(obj).startswith(MH_NS):
                    continue
                if not str(subj).startswith(MH_NS):
                    continue
                for i, (ns, *_rest) in enumerate(VOCAB):
                    if str(obj).startswith(ns):
                        kind = "logical" if pred in LOGICAL_PREDS else "documentary"
                        disp = str(obj)[len(ns):] if ns != "dtmi:" else str(obj)
                        rows.append((i, s, kind, local(subj), plabel, disp))
                        break
                else:
                    raise SystemExit(f"unlisted external target in {l}/{s}: {obj}")
    return rows


def fig_04_standards_basis(graphs):
    links = collect_links(graphs)
    grouped = defaultdict(list)
    for i, s, kind, subj, plabel, disp in links:
        grouped[(i, s)].append((kind, subj, plabel, disp))
    keys = sorted(grouped)

    row_h, row_gap = 0.66, 0.08
    n_rows = len(keys)
    hooks_h = 1.55
    height = TITLE_BAND + 0.45 + 0.55 + n_rows * (row_h + row_gap) + hooks_h + 1.65
    W = 16
    fig, ax = plt.subplots(figsize=(W, height))
    xlim, ylim = (0, W), (0, height)
    n_links = len(links)
    n_doc = sum(1 for r in links if r[2] == "documentary")
    setup_axes(ax, xlim, ylim,
               title=f"MAESTRO — Standards Basis ({VERSION})",
               subtitle=f"{n_links} links from maestro: terms to external terms: {n_doc} documentary skos matches, "
                        f"{n_links - n_doc} logical bridges — every target sits in a pinned copy under references/ (CHG-023, gate 7)")

    col_v, col_pin, col_mod, col_kind, col_links = 1.55, 3.85, 5.65, 7.30, 11.65
    head_y = height - TITLE_BAND - 0.45
    for x, t in ((col_v, "Vocabulary"), (col_pin, "Pinned copy"), (col_mod, "Module"),
                 (col_kind, "Link kind"), (col_links, "maestro: term  →  external term")):
        ax.text(x, head_y, t, ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=PALETTE["muted"])
    ax.plot([0.5, W - 0.5], [head_y - 0.28, head_y - 0.28], color=PALETTE["rule"], lw=0.8)

    layer_fill = {"core": PALETTE["cat_core"], "modules": PALETTE["cat_mod"], "ext": PALETTE["cat_ext"]}
    top = head_y - 0.42
    for r, key in enumerate(keys):
        i, s = key
        ns, disp_name, pfx, pinned, fam = VOCAB[i]
        items = grouped[key]
        y = top - (r + 1) * row_h - r * row_gap
        cy = y + row_h / 2
        ax.add_patch(FancyBboxPatch((0.5, y), W - 1.0, row_h,
                                    boxstyle="round,pad=0.01,rounding_size=0.03",
                                    facecolor="white" if r % 2 == 0 else PALETTE["panel"],
                                    edgecolor="#E3E8EC", lw=0.7, zorder=0))
        draw_box(ax, col_v - 1.0, cy - 0.24, 2.0, 0.48, label=disp_name,
                 style=BoxStyle(fill=PALETTE[fam], edge=PALETTE["ink"], lw=0.85),
                 fontsize=8.6 if len(disp_name) < 16 else 7.2)
        ax.text(col_pin, cy, pinned, ha="center", va="center", fontsize=7.6,
                color=PALETTE["muted"], family="DejaVu Sans Mono")
        layer = next(l for (l, st) in graphs if st == s)
        ax.add_patch(FancyBboxPatch((col_mod - 0.74, cy - 0.20), 1.48, 0.40,
                                    boxstyle="round,pad=0.01,rounding_size=0.05",
                                    facecolor=layer_fill[layer],
                                    edgecolor=PALETTE["ink"], lw=0.6))
        ax.text(col_mod, cy, f"{layer}/{s}", ha="center", va="center", fontsize=7.9,
                fontweight="bold", color=PALETTE["ink"])
        kinds = Counter(k for k, *_ in items)
        kind_txt = "\n".join(f"{n_} {k}" for k, n_ in
                             sorted(kinds.items(), key=lambda kv: kv[0] != "documentary"))
        ax.text(col_kind, cy, kind_txt, ha="center", va="center", fontsize=7.9,
                color="#3A2F58" if "logical" in kinds else PALETTE["ink"],
                fontweight="bold" if "logical" in kinds else "normal", linespacing=1.3)
        shown = items[:4]
        parts = [f"{subj} {plabel} {pfx}:{disp}" if pfx != "dtmi" else f"{subj} {plabel} {disp}"
                 for _, subj, plabel, disp in shown]
        if len(items) > 4:
            parts.append(f"… +{len(items) - 4} more")
        line1 = ", ".join(parts[:2])
        line2 = ", ".join(parts[2:])
        text = line1 + ("\n" + line2 if line2 else "")
        ax.text(8.55, cy, text, ha="left", va="center", fontsize=7.0,
                color=PALETTE["ink"], linespacing=1.35)

    # hooks band
    hy = top - n_rows * (row_h + row_gap) - 0.25 - hooks_h
    ax.add_patch(FancyBboxPatch((0.5, hy), W - 1.0, hooks_h,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor=PALETTE["hook"], edgecolor=PALETTE["muted"], lw=0.8,
                                linestyle="--"))
    ax.text(0.85, hy + hooks_h - 0.28,
            "Hooks — named in module comments, not mapped (no IRI, no match predicate; gate 7 fails otherwise)",
            ha="left", va="center", fontsize=9.6, fontweight="bold", color=PALETTE["ink"])
    hooks = [("ECLASS", "product"), ("DPP / DPPO", "product"), ("PRONTO", "product"),
             ("CaSkMan / CSS", "skill"), ("AAS", "invocation · digital-twin"),
             ("OpenAPI", "invocation · rest"), ("SAREF4INMA", "execution"),
             ("XACML", "policy · odrl")]
    hx = 0.85
    for name, where in hooks:
        w = 1.78
        ax.add_patch(FancyBboxPatch((hx, hy + 0.48), w, 0.62,
                                    boxstyle="round,pad=0.01,rounding_size=0.05",
                                    facecolor="white", edgecolor=PALETTE["muted"], lw=0.6,
                                    linestyle="--"))
        ax.text(hx + w / 2, hy + 0.48 + 0.42, name, ha="center", va="center",
                fontsize=8.2, fontweight="bold", color=PALETTE["ink"])
        ax.text(hx + w / 2, hy + 0.48 + 0.18, where, ha="center", va="center",
                fontsize=6.3, color=PALETTE["muted"], style="italic")
        hx += w + 0.09
    ax.text(0.85, hy + 0.22,
            "Pinned but not pointed at: QUDT (maestro:unitRef holds a QUDT unit IRI as an xsd:anyURI literal) and SOSA/SSN "
            "(observation evidence stays a hook on maestro:Skill).  ext/isa88.ttl and ext/odrl.ttl declare no term of their own.",
            ha="left", va="center", fontsize=7.2, color=PALETTE["muted"], style="italic")

    footnote(ax, W / 2, hy - 0.66,
             "Documentary = skos:closeMatch / relatedMatch / broadMatch, no logical consequence.   "
             "Logical bridge = rdfs:subClassOf / subPropertyOf, only in ext/prov.ttl and ext/odrl.ttl.\n"
             "No upstream ontology is imported; the pinned copies serve verification only.  See docs/03-standards-basis.md.",
             fontsize=8.4)
    return save(fig, "04-standards-basis")


# ---------------------------------------------------------------------------
#  FIGURE 05 - Widget-cell instance graph (Graphviz source generated)
# ---------------------------------------------------------------------------

GROUP_OF_MODULE = {
    "resource": "plant", "isa95": "plant", "automationml": "plant", "energy": "plant",
    "skill": "skills", "recipe": "recipe", "product": "product", "policy": "policy",
    "invocation": "invocation", "opcua": "invocation", "rest": "invocation", "dtdl": "invocation",
    "maintenance": "maintenance", "digital-twin": "twin", "execution": "runtime",
    "runtime": "runtime", "maas": "market",
}
GROUP_META = {
    "plant":       ("Plant, hierarchy and topology  (plant.ttl)", "#12A594"),
    "skills":      ("Skills  (plant.ttl)", "#E54D2E"),
    "recipe":      ("Recipe  (plant.ttl)", "#3B82F6"),
    "product":     ("Product  (plant.ttl)", "#6E56CF"),
    "policy":      ("Policy and safety  (plant.ttl)", "#111827"),
    "invocation":  ("Invocation: OPC UA, REST, DTDL  (plant.ttl)", "#F59E0B"),
    "maintenance": ("Maintenance plan  (plant.ttl)", "#B91C1C"),
    "twin":        ("Digital twin  (plant.ttl)", "#0EA5E9"),
    "market":      ("Market tier  (market.ttl)", "#0369A1"),
    "runtime":     ("Runtime snapshot  (runtime.ttl · maestro:Snapshot)", "#7C3AED"),
}
GROUP_ORDER = ["plant", "skills", "recipe", "product", "policy", "invocation",
               "maintenance", "twin", "market", "runtime"]


def gen_05_widget_cell(graphs):
    ex_dir = PKG / "queries" / "fixtures" / "widget-cell"
    files = {"plant": ex_dir / "plant.ttl", "market": ex_dir / "market.ttl",
             "runtime": ex_dir / "runtime.ttl"}
    defined_in = {}
    for g in graphs.values():
        for term in declared_terms(g):
            for m in g.objects(term, RDFS.isDefinedBy):
                defined_in[str(term)] = local(m)
    hhm_cls = set(HHM_CLASSES)
    hhm_rel = set(HHM_RELATIONS)

    data = {k: parse(p) for k, p in files.items()}
    all_data = Graph()
    for g in data.values():
        all_data += g

    node_file, node_types = {}, defaultdict(list)
    for fname in ("plant", "market", "runtime"):
        for s, o in data[fname].subject_objects(RDF.type):
            if str(s).startswith(EX_NS) and str(o).startswith(MH_NS):
                node_file.setdefault(str(s), fname)
                if str(o) not in node_types[str(s)]:
                    node_types[str(s)].append(str(o))

    def group_of(node):
        if node_file[node] in ("market", "runtime"):
            return node_file[node]
        for t in node_types[node]:
            m = defined_in.get(t, "")
            if m in GROUP_OF_MODULE:
                return GROUP_OF_MODULE[m]
        return "plant"

    groups = defaultdict(list)
    for node in node_types:
        groups[group_of(node)].append(node)

    vocab_nodes = {}
    edges = set()
    n_triples = 0
    for s, p, o in all_data:
        if not str(s).startswith(EX_NS) or p == RDF.type or not str(p).startswith(MH_NS):
            continue
        n_triples += 1
        if isinstance(o, Literal):
            continue
        if str(o) in node_types:
            edges.add((str(s), str(o), local(p)))
        elif str(o).startswith(MH_NS):
            vocab_nodes.setdefault(str(o), "v_" + local(o))
            edges.add((str(s), str(o), local(p)))

    def nid(iri):
        return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", local(iri))

    def label(node):
        ts = [local(t) for t in node_types[node]]
        return f"ex:{local(node)}\\n({' · '.join('maestro:' + t for t in ts)})"

    # a vocabulary individual is drawn inside the cluster that uses it most
    vocab_home = {}
    for iri in vocab_nodes:
        users = Counter(group_of(s) for s, o, _ in edges if o == iri)
        vocab_home[iri] = users.most_common(1)[0][0]

    lines = [
        "// GENERATED by figures/v0.2.0/scripts/render_figures.py from queries/fixtures/widget-cell/*.ttl.",
        "// Do not edit; re-run the renderer. Literal-valued properties are omitted.",
        "// Render: dot -Tpng figures/v0.2.0/src/05-widget-cell.gv -o figures/v0.2.0/png/05-widget-cell.png",
        "digraph HHM_WidgetCell {",
        "  rankdir=LR; newrank=true; labelloc=\"t\"; fontname=\"Helvetica\"; nodesep=0.22; ranksep=0.9;",
        f"  label=\"MAESTRO  ·  widget-cell example  ·  {len(node_types)} ex: individuals, "
        f"{len(edges)} object-property edges ({n_triples} maestro: triples in all) across plant.ttl, market.ttl and runtime.ttl\\n"
        "Gold double border = individual typed by an HHM-Core v1 diagram class · solid edge = HHM-Core v1 relation · "
        "dashed = relation added by the package · grey ellipse = controlled-vocabulary individual (maestro:)\";",
        "  node [shape=box, style=\"rounded,filled\", fillcolor=\"#f9f9fb\", fontname=\"Helvetica\", "
        "fontsize=9, color=\"#1F2A36\", penwidth=0.8];",
        "  edge [fontname=\"Helvetica\", fontsize=8, arrowsize=0.7];",
    ]
    for gname in GROUP_ORDER:
        if not groups.get(gname):
            continue
        title, color = GROUP_META[gname]
        style = "rounded,dashed" if gname == "runtime" else "rounded"
        lines += [f"  subgraph cluster_{gname} {{",
                  f"    label=\"{title}\"; color=\"{color}\"; style=\"{style}\"; "
                  "fontname=\"Helvetica\"; fontsize=11; penwidth=1.2;"]
        for node in sorted(groups[gname], key=local):
            is_hhm = any(local(t) in hhm_cls for t in node_types[node])
            extra = ", fillcolor=\"#FCEFC7\", peripheries=2, penwidth=1.4" if is_hhm else ""
            lines.append(f"    {nid(node)} [label=\"{label(node)}\"{extra}];")
        for iri, vid in sorted(vocab_nodes.items()):
            if vocab_home[iri] == gname:
                lines.append(f"    {vid} [label=\"maestro:{local(iri)}\", shape=ellipse, style=\"filled\", "
                             "fillcolor=\"#EEF1F4\", color=\"#5C6B7A\", fontsize=8];")
        lines.append("  }")
    for s, o, p in sorted(edges):
        dst = nid(o) if o in node_types else vocab_nodes[o]
        color = GROUP_META[group_of(s)][1]
        style = "solid" if p in hhm_rel else "dashed"
        lines.append(f"  {nid(s)} -> {dst} [label=\"{p}\", color=\"{color}\", "
                     f"fontcolor=\"{color}\", style={style}];")
    lines.append("}")
    out = SRC / "05-widget-cell.gv"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


# ---------------------------------------------------------------------------
#  FIGURE 06 - Provenance of definitions from MAESTRO 1.0
# ---------------------------------------------------------------------------

M10_ORDER = ["core", "resource", "skill", "recipe", "product", "communication", "policy",
             "safety", "runtime", "energy", "maintenance", "maas", "planning", "opcua",
             "automationml", "dtdl", "prov"]


def fig_06_maestro_alignment(graphs):
    rows = []      # (layer, stem, terms, exact, close, new, Counter(source module))
    for (l, s), g in graphs.items():
        terms = declared_terms(g)
        ex = cl = 0
        srcs = Counter()
        for t in terms:
            so = list(g.objects(t, DCTERMS.source))
            rf = list(g.objects(t, DCTERMS.references))
            if so:
                ex += 1
            elif rf:
                cl += 1
            for o in so + rf:
                srcs[str(o).split("/")[-1].split("#")[0]] += 1
        rows.append((l, s, len(terms), ex, cl, len(terms) - ex - cl, srcs))
    cols = [m for m in M10_ORDER if any(m in r[6] for r in rows)]
    for r in rows:
        for m in r[6]:
            if m not in cols:
                cols.append(m)

    tot_terms = sum(r[2] for r in rows)
    tot_ex = sum(r[3] for r in rows)
    tot_cl = sum(r[4] for r in rows)

    cell_w, cell_h = 0.66, 0.44
    left = 4.2
    W = left + len(cols) * cell_w + 3.5
    top_pad = TITLE_BAND + 1.55
    H = top_pad + len(rows) * cell_h + 1.9
    fig, ax = plt.subplots(figsize=(W, H))
    setup_axes(ax, (0, W), (0, H),
               title="MAESTRO — Where the Definitions Come From",
               subtitle=f"{tot_ex} of {tot_terms} declared terms reuse a MAESTRO 1.0 definition as is (dct:source), "
                        f"{tot_cl} adapt one (dct:references), {tot_terms - tot_ex - tot_cl} are new — "
                        "counted per MAESTRO 1.0 source module")

    hy = H - TITLE_BAND - 1.25
    for j, m in enumerate(cols):
        x = left + j * cell_w + cell_w / 2
        ax.text(x - 0.06, hy + 0.05, m, ha="left", va="bottom", rotation=55, fontsize=8.2,
                color=PALETTE["ink"], fontweight="bold")
    ax.text(left + len(cols) * cell_w / 2, hy + 1.12,
            "MAESTRO 1.0 module   (ontologies/…/<module>.ttl)",
            ha="center", va="bottom", fontsize=8.6, color=PALETTE["muted"], style="italic")
    sx = left + len(cols) * cell_w + 0.25
    for k, t in enumerate(("terms", "exact", "close", "new")):
        ax.text(sx + k * 0.78 + 0.39, hy + 0.05, t, ha="center", va="bottom", fontsize=8.4,
                fontweight="bold", color=PALETTE["muted"])

    grid_top = hy - 0.05
    max_v = max(max(r[6].values()) if r[6] else 0 for r in rows)
    layer_fill = {"core": PALETTE["cat_core"], "modules": PALETTE["cat_mod"], "ext": PALETTE["cat_ext"]}
    for i, (l, s, n, ex, cl, nw, srcs) in enumerate(rows):
        y = grid_top - (i + 1) * cell_h
        cy = y + cell_h / 2
        ax.add_patch(FancyBboxPatch((0.45, y + 0.04), left - 0.7, cell_h - 0.08,
                                    boxstyle="round,pad=0.01,rounding_size=0.04",
                                    facecolor=layer_fill[l], edgecolor=PALETTE["ink"], lw=0.55))
        ax.text(0.62, cy, f"{l}/{s}", ha="left", va="center", fontsize=8.4,
                fontweight="bold", color=PALETTE["ink"])
        ax.text(left - 0.38, cy, CLUSTER_NAME.get(s, ""), ha="right", va="center",
                fontsize=6.4, color=PALETTE["muted"], style="italic")
        for j, m in enumerate(cols):
            x = left + j * cell_w
            v = srcs.get(m, 0)
            if v:
                t = v / max_v
                fill = (1 - 0.62 * t, 1 - 0.38 * t, 1 - 0.10 * t)   # white -> muted blue
                ax.add_patch(Rectangle((x, y), cell_w, cell_h, facecolor=fill,
                                       edgecolor="#E3E8EC", lw=0.5))
                ax.text(x + cell_w / 2, cy, str(v), ha="center", va="center", fontsize=8,
                        color=PALETTE["ink"] if t < 0.55 else "white", fontweight="bold")
            else:
                ax.add_patch(Rectangle((x, y), cell_w, cell_h, facecolor="white",
                                       edgecolor="#E3E8EC", lw=0.5))
        for k, v in enumerate((n, ex, cl, nw)):
            txt = "matches only" if (k == 0 and n == 0) else str(v)
            ax.text(sx + k * 0.78 + 0.39, cy, txt, ha="center", va="center",
                    fontsize=7.8 if txt != "matches only" else 6.2,
                    fontweight="bold" if k == 0 else "normal",
                    color=("#B23A48" if (k == 3 and v) else PALETTE["ink"]))
    footnote(ax, W / 2, grid_top - len(rows) * cell_h - 0.72,
             "A cell counts the terms of the row module whose dct:source or dct:references names the column module.  "
             "New terms have no MAESTRO 1.0 counterpart (e.g. maestro:DigitalTwin, maestro:targetStep, maestro:OpcUaBinding).\n"
             "tools/gen_alignment.py turns the same annotations into alignment/maestro-1.0.ttl (skos:exactMatch / closeMatch).  "
             "ontologies/ at the repository root stays the governed source.",
             fontsize=8.2)
    return save(fig, "06-maestro-alignment")


# ---------------------------------------------------------------------------
#  CHECK - every maestro: name in the hand-authored .gv files must be declared
# ---------------------------------------------------------------------------

HAND_AUTHORED = ("03-hhm-schema.gv", "07-beyond-clusters.gv")
EDGE_KEYWORDS = {"subClassOf", "subPropertyOf", "closeMatch", "relatedMatch", "broadMatch"}


def check_hand_authored(graphs) -> list[str]:
    declared, deprecated = set(), set()
    for g in graphs.values():
        declared |= {local(t) for t in declared_terms(g)}
        deprecated |= {local(s) for s, o in g.subject_objects(OWL.deprecated) if o.toPython() is True}
    problems = []
    for name in HAND_AUTHORED:
        path = SRC / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        text = re.sub(r"//.*", "", path.read_text(encoding="utf-8"))
        used = set(re.findall(r"\bmaestro:([A-Za-z][A-Za-z0-9]*)", text))
        # edge labels: one or more lowerCamelCase property names separated by " / "
        for lab in re.findall(r'\[label="([a-z][A-Za-z0-9]*(?: / [a-z][A-Za-z0-9]*)*)"', text):
            used |= set(lab.split(" / "))
        for u in sorted(used):
            if u not in declared and u not in EDGE_KEYWORDS:
                problems.append(f"{name}: '{u}' is not a declared maestro: term")
            elif u in deprecated:
                problems.append(f"{name}: '{u}' is a deprecated 0.1.0 name")
    return problems


# ---------------------------------------------------------------------------
#  MAIN
# ---------------------------------------------------------------------------

def render_dot(stem: str, dpi: int = 160) -> Path | None:
    dot = shutil.which("dot")
    src = SRC / f"{stem}.gv"
    if not dot:
        print(f"SKIP {src.name}: Graphviz 'dot' not on PATH")
        return None
    out = PNG / f"{stem}.png"
    subprocess.run([dot, "-Tpng", f"-Gdpi={dpi}", str(src), "-o", str(out)], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the hand-authored .gv files name declared terms only")
    args = ap.parse_args()
    graphs = load_modules()
    problems = check_hand_authored(graphs)
    for p in problems:
        print("FAIL", p)
    if args.check:
        print("OK   hand-authored figures name declared maestro: terms only" if not problems
              else f"{len(problems)} problem(s)")
        sys.exit(1 if problems else 0)
    if problems:
        sys.exit(1)

    PNG.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    for fn in (fig_01_module_stack, fig_04_standards_basis, fig_06_maestro_alignment):
        print("OK  ", fn(graphs))
    for gen in (gen_02_import_graph, gen_05_widget_cell):
        print("OK  ", gen(graphs))
    for stem in ("02-import-graph", "03-hhm-schema", "05-widget-cell", "07-beyond-clusters"):
        out = render_dot(stem)
        if out:
            print("OK  ", out)


if __name__ == "__main__":
    main()
