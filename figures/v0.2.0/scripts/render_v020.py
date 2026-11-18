"""
MAESTRO - renders every figure of the package (ontology 0.2.0).

Writes figures/v0.2.0/{src,png,svg} from the Turtle files under core/, modules/, ext/
and usecase-knowledge-graphs/. All builders live in this folder:

    render_figures.py   01-module-stack, 02-import-graph, 04-standards-basis, 05-widget-cell,
                        06-maestro-alignment; renders the hand-authored
                        src/03-hhm-schema.gv and src/07-beyond-clusters.gv
    render.py           proposed-maestro[-with-extensions] (model from tools/gen_graph.py)
    render_kg.py        helpers shared by the knowledge-graph figures
    render_kg_ltu.py    kg-ltu-*       (usecase-knowledge-graphs/ltu-festo-mps)
    this script         13-class-taxonomy, 14-property-structure, 15-renamed-terms,
                        16-version-comparison, and the run of everything above

Usage (from the package root, with rdflib, matplotlib, Pillow and Graphviz `dot`):
    python figures/v0.2.0/scripts/render_v020.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

HERE = Path(__file__).resolve().parent              # figures/v0.2.0/scripts
FIG = HERE.parent                                   # figures/v0.2.0
PKG = FIG.parents[1]                                # package root
SRC, PNG, SVG = FIG / "src", FIG / "png", FIG / "svg"
for p in (PKG / "tools", HERE):
    sys.path.insert(0, str(p))

import common  # noqa: E402
import gen_graph  # noqa: E402
from gen_alignment import HHM_CLASSES, HHM_RELATIONS, HHM_RENAMED, package_name  # noqa: E402
import render_figures as rf  # noqa: E402
import render as ag  # noqa: E402
import render_kg as rk  # noqa: E402
import render_kg_ltu as rl  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402  (style set by render_figures)

MH_NS = common.MH_NS
VERSION = str(next(common.parse(common.UMBRELLA_FILE).objects(common.ONTOLOGY_IRI, OWL.versionInfo)))
BASELINE_COMMIT = "920094a"        # first commit: the 0.1.0 package, published as MAESTRO HHM-Core
BASELINE_FILE = "maestro-hhm-core-merged.ttl"   # its merged ontology (historical file name)
BASELINE_NS = "https://w3id.org/maestro/hhm#"   # its namespace (historical)
HHM_CLASS_NAMES = {package_name(n) for n in HHM_CLASSES}
HHM_REL_NAMES = {package_name(n) for n in HHM_RELATIONS}


# ---------------------------------------------------------------------------
#  helpers
# ---------------------------------------------------------------------------

def local(t) -> str:
    return str(t)[len(MH_NS):] if str(t).startswith(MH_NS) else str(t).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def is_mh(t) -> bool:
    return isinstance(t, URIRef) and str(t).startswith(MH_NS)


def deprecated_terms(g: Graph) -> set:
    return {s for s, o in g.subject_objects(OWL.deprecated) if o.toPython() is True}


def schema() -> Graph:
    return common.load_modules()


def dot(stem: str, dpi: int = 160, svg: bool = False) -> None:
    exe = shutil.which("dot")
    if not exe:
        raise SystemExit("Graphviz `dot` not found on PATH")
    src = SRC / f"{stem}.gv"
    subprocess.run([exe, "-Tpng", f"-Gdpi={dpi}", str(src), "-o", str(PNG / f"{stem}.png")], check=True)
    if svg:
        out = subprocess.run([exe, "-Tsvg", str(src)], check=True, capture_output=True, text=True, encoding="utf-8").stdout
        (SVG / f"{stem}.svg").write_text(re.sub(r"<!DOCTYPE[^>]*>\s*", "", out), encoding="utf-8")
    print(f"OK   png/{stem}.png" + (f" + svg/{stem}.svg" if svg else ""))


def write_gv(stem: str, text: str) -> None:
    (SRC / f"{stem}.gv").write_text(text, encoding="utf-8", newline="\n")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
#  model derived from Turtle by tools/gen_graph.py
# ---------------------------------------------------------------------------

def build_model() -> dict:
    model = gen_graph.build_model()
    (SRC / f"model-{VERSION}.json").write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding="utf-8")
    return model


# ---------------------------------------------------------------------------
#  13 - class taxonomy
# ---------------------------------------------------------------------------

def module_of(g: Graph, t) -> str:
    m = next(g.objects(t, RDFS.isDefinedBy), None)
    return str(m).rsplit("/", 1)[-1] if m else "?"


def gen_13_class_taxonomy(g: Graph) -> str:
    dep = deprecated_terms(g)
    classes = sorted((c for c in g.subjects(RDF.type, OWL.Class) if is_mh(c) and c not in dep), key=str)
    supers = {c: sorted({s for s in g.objects(c, RDFS.subClassOf) if is_mh(s) and s not in dep}, key=str) for c in classes}
    children = defaultdict(list)
    for c, ss in supers.items():
        for s in ss:
            children[s].append(c)
    value_sets = {c for c, ss in supers.items() if URIRef(MH_NS + "ValueSet") in ss}
    individuals = defaultdict(list)
    for s, o in g.subject_objects(RDF.type):
        if (s, RDF.type, OWL.NamedIndividual) in g and is_mh(o):
            individuals[o].append(local(s))
    grouping = {c for c in classes if local(c).endswith("Element") or local(c) in ("Resource", "ValueSet", "Condition")}
    by_mod = defaultdict(list)
    for c in classes:
        by_mod[module_of(g, c)].append(c)
    out = ["// GENERATED by figures/v0.2.0/scripts/render_v020.py from core/, modules/ and ext/. Do not edit.",
           "digraph Class_Taxonomy {",
           f'rankdir=LR; newrank=true; nodesep=0.12; ranksep=0.9; fontname="Helvetica"; fontsize=18; labelloc="t";',
           f'label="MAESTRO {VERSION}  ·  class taxonomy: {len(classes)} classes, every maestro: rdfs:subClassOf edge (superclass on the left)\\n'
           'Bold tinted box = grouping class (no disjointness between groups) · gold double border = HHM-Core v1 class · '
           'value-set classes list their individuals · cluster = declaring module";',
           'node [shape=box style="rounded,filled" fillcolor="#f9f9fb" fontname="Helvetica" fontsize=10 color="#1F2A36" penwidth=0.8 margin="0.08,0.03"];',
           'edge [color="#5C6B7A" arrowsize=0.6 dir=back arrowtail=empty];']
    for layer, stem in common.MODULES:
        if not by_mod.get(stem):
            continue
        title, color, lyr = gen_graph.MODULE_META[stem]
        style = {"core": "rounded", "module": "rounded,dashed"}.get(lyr, "rounded,dotted")
        out.append(f'subgraph cluster_{stem.replace("-", "_")} {{ label="{title}  ({layer}/{stem}.ttl)"; color="{color}"; '
                   f'fontcolor="{color}"; style="{style}"; penwidth=1.3; fontsize=12;')
        for c in by_mod[stem]:
            name = local(c)
            label = f"<B>maestro:{esc(name)}</B>"
            if c in value_sets or (c in individuals and name not in ("Role",)):
                inds = sorted(individuals.get(c, []))
                if inds:
                    rows, line = [], ""
                    for i in inds:
                        if len(line) + len(i) > 48:
                            rows.append(line.rstrip(" ·"))
                            line = ""
                        line += i + " · "
                    rows.append(line.rstrip(" ·"))
                    label += '<BR/><FONT POINT-SIZE="8" COLOR="#5C6B7A">' + "<BR/>".join(esc(r) for r in rows) + "</FONT>"
            attrs = []
            if c in grouping:
                attrs += [f'fillcolor="{color}22"', f'color="{color}"', "penwidth=2.0", "fontsize=12"]
            if name in HHM_CLASS_NAMES:
                attrs += ['fillcolor="#FCEFC7"', "peripheries=2", "penwidth=1.4"]
            out.append(f'  "{name}" [label=<{label}> ' + " ".join(attrs) + "];")
        out.append("}")
    for c, ss in supers.items():
        for s in ss:
            color = gen_graph.MODULE_META[module_of(g, s)][1] if module_of(g, s) in gen_graph.MODULE_META else "#5C6B7A"
            out.append(f'"{local(s)}" -> "{local(c)}" [color="{color}"];')
    out.append("}")
    write_gv("13-class-taxonomy", "\n".join(out) + "\n")
    return "13-class-taxonomy"


# ---------------------------------------------------------------------------
#  14 - property structure
# ---------------------------------------------------------------------------

def gen_14_property_structure(g: Graph) -> str:
    dep = deprecated_terms(g)
    props = {p for t in (OWL.ObjectProperty, OWL.DatatypeProperty) for p in g.subjects(RDF.type, t) if is_mh(p) and p not in dep}
    subprop = [(a, b) for a, b in g.subject_objects(RDFS.subPropertyOf) if a in props]
    inverse = [(a, b) for a, b in g.subject_objects(OWL.inverseOf) if a in props]
    transitive = {p for p in g.subjects(RDF.type, OWL.TransitiveProperty) if p in props}
    functional = {p for p in g.subjects(RDF.type, OWL.FunctionalProperty) if p in props}
    shown = {x for pair in subprop + inverse for x in pair} | transitive
    external = sorted({b for _, b in subprop if not is_mh(b)}, key=str)
    by_mod = defaultdict(list)
    for p in shown:
        if is_mh(p):
            by_mod[module_of(g, p)].append(p)

    def label(p) -> str:
        tags = []
        if p in transitive:
            tags.append("transitive")
        if p in functional:
            tags.append("functional")
        dom = ", ".join(local(d) for d in g.objects(p, RDFS.domain) if is_mh(d))
        rng = ", ".join(local(r) for r in g.objects(p, RDFS.range))
        sig = f"{dom or 'open'} → {rng or 'open'}"
        hhm = local(p) in HHM_REL_NAMES
        return (f"<{'<B>' if hhm else ''}maestro:{esc(local(p))}{'</B>' if hhm else ''}"
                f'<BR/><FONT POINT-SIZE="8" COLOR="#5C6B7A">{esc(sig)}'
                + (f'<BR/><I>{esc(" · ".join(tags))}</I>' if tags else "") + "</FONT>>")

    out = ["// GENERATED by figures/v0.2.0/scripts/render_v020.py from core/, modules/ and ext/. Do not edit.",
           "digraph Property_Structure {",
           'rankdir=LR; newrank=true; nodesep=0.18; ranksep=1.0; fontname="Helvetica"; fontsize=18; labelloc="t";',
           f'label="MAESTRO {VERSION}  ·  property structure: rdfs:subPropertyOf (super-property on the left, hollow arrow), '
           f'owl:inverseOf (purple, both ends), transitive and functional properties\\n'
           f'{len(subprop)} sub-property axioms · {len(inverse)} inverse pairs · {len(transitive)} transitive · '
           f'{len(functional)} functional properties (listed in the table) · bold name = HHM-Core v1 relation · grey ellipse = PROV-O / ODRL term";',
           'node [shape=box style="rounded,filled" fillcolor="#f9f9fb" fontname="Helvetica" fontsize=10 color="#1F2A36" penwidth=0.8 margin="0.08,0.03"];',
           'edge [arrowsize=0.7 fontname="Helvetica" fontsize=8];']
    for layer, stem in common.MODULES:
        if not by_mod.get(stem):
            continue
        title, color, lyr = gen_graph.MODULE_META[stem]
        out.append(f'subgraph cluster_{stem.replace("-", "_")} {{ label="{title}  ({layer}/{stem}.ttl)"; color="{color}"; '
                   f'fontcolor="{color}"; style="rounded"; penwidth=1.3; fontsize=12;')
        for p in sorted(by_mod[stem], key=str):
            extra = ' penwidth=2.0 fillcolor="#F0FDF4"' if p in transitive else ""
            out.append(f'  "{local(p)}" [label={label(p)} color="{color}"{extra}];')
        out.append("}")
    out.append('subgraph cluster_std { label="W3C PROV-O and ODRL 2.2 (logical bridges, ext/prov.ttl and ext/odrl.ttl)"; '
               'color="#9CA3AF"; style="rounded,dashed"; fontcolor="#5C6B7A"; fontsize=12;')
    for e in external:
        pfx = "prov" if "prov#" in str(e) else "odrl"
        out.append(f'  "{pfx}:{local(e)}" [shape=ellipse fillcolor="#F3F4F6" color="#9CA3AF" fontcolor="#374151"];')
    out.append("}")
    for a, b in subprop:
        tb = local(b) if is_mh(b) else ("prov" if "prov#" in str(b) else "odrl") + ":" + local(b)
        out.append(f'"{tb}" -> "{local(a)}" [dir=back arrowtail=empty color="#1F2A36"];')
    for a, b in inverse:
        out.append(f'"{local(a)}" -> "{local(b)}" [dir=both color="#7C3AED" style=dashed constraint=false label="inverseOf" fontcolor="#7C3AED"];')
    # functional properties, listed per module
    rows = defaultdict(list)
    for p in functional:
        rows[module_of(g, p)].append(local(p))
    cells = "".join(
        f'<TR><TD ALIGN="LEFT"><B>{esc(gen_graph.MODULE_META[m][0])}</B></TD><TD ALIGN="LEFT">{esc(" · ".join(sorted(v)))}</TD></TR>'
        for m, v in sorted(rows.items(), key=lambda kv: [s for _, s in common.MODULES].index(kv[0])))
    out.append('fn [shape=plain label=<<TABLE BORDER="1" COLOR="#1F2A36" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF">'
               f'<TR><TD COLSPAN="2"><B>owl:FunctionalProperty ({len(functional)}): one value per subject</B></TD></TR>{cells}'
               '<TR><TD COLSPAN="2" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#5C6B7A">Not functional on purpose: represents, describedIn, hasStatus, '
               'moduleOf, stepOf (limits are SHACL warnings)</FONT></TD></TR></TABLE>>];')
    out.append("}")
    write_gv("14-property-structure", "\n".join(out) + "\n")
    return "14-property-structure"


# ---------------------------------------------------------------------------
#  15 - renamed terms (matplotlib table, render_figures style)
# ---------------------------------------------------------------------------

def fig_15_renamed_terms(g: Graph):
    P = rf.PALETTE
    hhm_of = {v: k for k, v in HHM_RENAMED.items()}
    rows = []
    for old in deprecated_terms(g):
        new = next(g.objects(old, DCTERMS.isReplacedBy))
        kind = "class" if (old, RDF.type, OWL.Class) in g else (
            "datatype property" if (old, RDF.type, OWL.DatatypeProperty) in g else "object property")
        note = "merged; domain Endpoint or Binding" if local(old) == "specializesAs" else ""
        rows.append((local(old), local(new), hhm_of.get(local(new), "—"), module_of(g, old), kind, note))
    rows.append(("hasPart (BOM nesting)", "hasSubItem", "hasPart", "product", "object property",
                 "hasPart is now the generic super-property"))
    order = ["resource", "skill", "recipe", "product", "invocation", "policy", "execution", "rest"]
    rows.sort(key=lambda r: (order.index(r[3]) if r[3] in order else 99, r[0].lower()))

    row_h = 0.52
    height = rf.TITLE_BAND + 0.5 + 0.5 + len(rows) * row_h + 1.6
    W = 15
    fig, ax = plt.subplots(figsize=(W, height))
    rf.setup_axes(ax, (0, W), (0, height),
                  title=f"MAESTRO — Renamed terms ({VERSION})",
                  subtitle=f"{len(rows) - 1} deprecated 0.1.0 names plus the BOM nesting edge; each deprecated IRI stays declared with "
                           "owl:equivalentClass / owl:equivalentProperty and dct:isReplacedBy to the new term")
    cols = [(0.7, "0.1.0 name (deprecated)", "left"), (4.0, "0.2.0 name", "left"), (6.9, "HHM-Core v1 name", "left"),
            (9.4, "Module", "left"), (11.0, "Kind / note", "left")]
    head_y = height - rf.TITLE_BAND - 0.4
    for x, t, ha in cols:
        ax.text(x, head_y, t, ha=ha, va="center", fontsize=10.5, fontweight="bold", color=P["muted"])
    ax.plot([0.5, W - 0.5], [head_y - 0.26, head_y - 0.26], color=P["rule"], lw=0.8)
    layer_fill = {"core": P["cat_core"], "modules": P["cat_mod"], "ext": P["cat_ext"]}
    layer_of = {s: l for l, s in common.MODULES}
    top = head_y - 0.42
    for i, (old, new, hhm, mod, kind, note) in enumerate(rows):
        y = top - (i + 1) * row_h
        cy = y + row_h / 2
        ax.add_patch(rf.FancyBboxPatch((0.5, y + 0.03), W - 1.0, row_h - 0.06, boxstyle="round,pad=0.01,rounding_size=0.03",
                                       facecolor="white" if i % 2 == 0 else P["panel"], edgecolor="#E3E8EC", lw=0.6, zorder=0))
        ax.text(0.7, cy, f"maestro:{old}", ha="left", va="center", fontsize=9.2, color=P["muted"], family="DejaVu Sans Mono")
        ax.text(3.6, cy, "→", ha="center", va="center", fontsize=11, color=P["muted"])
        ax.text(4.0, cy, f"maestro:{new}", ha="left", va="center", fontsize=9.6, fontweight="bold", color=P["ink"], family="DejaVu Sans Mono")
        ax.text(6.9, cy, hhm if hhm == "—" else f"hhm:{hhm}", ha="left", va="center", fontsize=9.0,
                color="#8A5A00" if hhm != "—" else P["muted"], family="DejaVu Sans Mono")
        ax.add_patch(rf.FancyBboxPatch((9.4, cy - 0.17), 1.35, 0.34, boxstyle="round,pad=0.01,rounding_size=0.05",
                                       facecolor=layer_fill.get(layer_of.get(mod, "core"), P["cat_gen"]), edgecolor=P["ink"], lw=0.5))
        ax.text(10.075, cy, mod, ha="center", va="center", fontsize=8.2, fontweight="bold", color=P["ink"])
        ax.text(11.0, cy, kind + (f" — {note}" if note else ""), ha="left", va="center", fontsize=8.4, color=P["ink"])
    rf.footnote(ax, W / 2, top - len(rows) * row_h - 0.75,
                "HHM-Core v1 names map to the new terms in alignment/hhm-core.ttl (HHM_RENAMED in tools/gen_alignment.py); "
                "coverage stays 43 of 43 classes and 47 of 47 relations.\n"
                "Examples, queries, shapes and figure scripts use the new names; data written against 0.1.0 still reasons and validates.",
                fontsize=8.4)
    return rf.save(fig, "15-renamed-terms")


# ---------------------------------------------------------------------------
#  16 - 0.1.0 versus 0.2.0
# ---------------------------------------------------------------------------

def metrics(g: Graph) -> dict:
    dep = deprecated_terms(g)

    def named(t):
        return {s for s in g.subjects(RDF.type, t) if is_mh(s) and s not in dep}

    classes = named(OWL.Class)
    top = {c for c in classes if not any(is_mh(s) for s in g.objects(c, RDFS.subClassOf))}
    disjoint = len(list(g.triples((None, OWL.disjointWith, None)))) + len(list(g.subjects(RDF.type, OWL.AllDisjointClasses)))
    return {
        "Classes": len(classes),
        "Object properties": len(named(OWL.ObjectProperty)),
        "Datatype properties": len(named(OWL.DatatypeProperty)),
        "Named individuals": len(named(OWL.NamedIndividual)),
        "Top-level classes": len(top),
        "subClassOf axioms (maestro: → maestro:)": sum(1 for a, b in g.subject_objects(RDFS.subClassOf) if is_mh(a) and is_mh(b) and a not in dep),
        "subPropertyOf axioms": sum(1 for a, _ in g.subject_objects(RDFS.subPropertyOf) if a not in dep),
        "inverseOf axioms": len(list(g.triples((None, OWL.inverseOf, None)))),
        "Functional properties": len({p for p in g.subjects(RDF.type, OWL.FunctionalProperty) if p not in dep}),
        "Transitive properties": len(set(g.subjects(RDF.type, OWL.TransitiveProperty))),
        "Disjointness axioms": disjoint,
        "Deprecated terms": len(dep),
    }


def fig_16_version_comparison(g: Graph):
    try:
        old_text = subprocess.run(["git", "-C", str(PKG), "show", f"{BASELINE_COMMIT}:ontologies/{BASELINE_FILE}"],
                                  check=True, capture_output=True, text=True, encoding="utf-8").stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"SKIP 16-version-comparison: 0.1.0 baseline not readable from git ({exc})")
        return None
    # 0.1.0 used the namespace https://w3id.org/maestro/hhm#; map it so the same counts apply
    old = Graph().parse(data=old_text.replace(BASELINE_NS, MH_NS), format="turtle")
    a, b = metrics(old), metrics(g)
    (SRC / "16-version-comparison.json").write_text(json.dumps({"0.1.0": a, VERSION: b}, indent=1), encoding="utf-8")
    P = rf.PALETTE
    c_old, c_new = "#C98B2B", "#2563A8"        # validated pair (dataviz validator: CVD ΔE 26.8, normal 31.8)
    panels = [("Vocabulary", list(a)[:5]), ("Axioms and annotations", list(a)[5:])]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.6), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.55})
    for ax, (title, keys) in zip(axes, panels):
        ys = range(len(keys))[::-1]
        h = 0.36
        for y, k in zip(ys, keys):
            for off, val, col in ((h / 2 + 0.02, a[k], c_old), (-h / 2 - 0.02, b[k], c_new)):
                ax.barh(y + off, val, height=h, color=col, edgecolor="white", linewidth=1.0, zorder=2)
                ax.text(val + max(max(a[x] for x in keys), max(b[x] for x in keys)) * 0.012, y + off, str(val),
                        va="center", ha="left", fontsize=9, color=P["ink"])
        ax.set_yticks(list(ys))
        ax.set_yticklabels(keys, fontsize=10, color=P["ink"])
        ax.set_title(title, fontsize=12, fontweight="bold", color=P["ink"], loc="left", pad=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines["left"].set_color(P["rule"])
        ax.spines["bottom"].set_color(P["rule"])
        ax.tick_params(axis="x", colors=P["muted"], labelsize=9)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=P["rule"], lw=0.5, zorder=0)
        ax.set_xlim(0, max(max(a[x] for x in keys), max(b[x] for x in keys)) * 1.15)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c_old, label="0.1.0 (first commit)"), Patch(color=c_new, label=f"{VERSION} (current Turtle)")],
               loc="upper center", bbox_to_anchor=(0.5, 0.0), frameon=False, fontsize=10.5, ncol=2)
    fig.suptitle(f"MAESTRO — 0.1.0 versus {VERSION}", x=0.06, ha="left", y=1.06,
                 fontsize=15, fontweight="bold", color=P["ink"])
    fig.text(0.06, 0.995, "Counts over the merged ontology; deprecated 0.1.0 names are counted only in the last row. "
             "Top-level classes = maestro: classes without an maestro: superclass.", fontsize=9.5, color=P["muted"], style="italic")
    return rf.save(fig, "16-version-comparison")


# ---------------------------------------------------------------------------
#  main
# ---------------------------------------------------------------------------

def main() -> None:
    for d in (SRC, PNG, SVG):
        d.mkdir(parents=True, exist_ok=True)
    graphs = rf.load_modules()
    problems = rf.check_hand_authored(graphs)
    if problems:
        raise SystemExit("\n".join(problems))
    print("OK   03 / 07 name declared, non-deprecated maestro: terms only")
    g = schema()
    model = build_model()

    print(f"MAESTRO {VERSION} figures -> {FIG.relative_to(PKG).as_posix()}/")
    for fn in (rf.fig_01_module_stack, rf.fig_04_standards_basis, rf.fig_06_maestro_alignment):
        fn(graphs)
        print(f"OK   png/{fn.__name__[4:].replace('_', '-')}.png")
    for gen in (rf.gen_02_import_graph, rf.gen_05_widget_cell):
        gen(graphs)
    for stem in ("02-import-graph", "05-widget-cell"):
        dot(stem)
    for stem in ("03-hhm-schema", "07-beyond-clusters"):
        dot(stem, svg=True)
    for stem in (gen_13_class_taxonomy(g), gen_14_property_structure(g)):
        dot(stem, dpi=160, svg=True)
    print(f"OK   {fig_15_renamed_terms(g).relative_to(FIG).as_posix()}")
    out = fig_16_version_comparison(g)
    if out:
        print(f"OK   {out.relative_to(FIG).as_posix()}")

    lean = ag.proposed_model()
    ag.dot("proposed-maestro",
           ag.build_proposed(lean, {"core", "module"},
                             f"MAESTRO {VERSION}: seven HHM-Core clusters plus runtime, energy, maintenance and MaaS modules "
                             "(derived from the Turtle files by tools/gen_graph.py)"), ag.DPI_SCHEMA, svg=True)
    ag.dot("proposed-maestro-with-extensions",
           ag.build_proposed(lean, {"core", "module", "ext"},
                             f"MAESTRO {VERSION}, with the extension modules (OPC UA, digital twin, DTDL, REST, ISA-95, AutomationML)"),
           ag.DPI_SCHEMA, svg=True)

    tbox = rk.load_tbox(model)
    full = rl.load_all()
    rl.render("kg-ltu-overview", rl.build_overview(full))
    ltu = {}
    for k in rl.UNITS:
        text, stats = rl.build_unit(k, full, *tbox)
        rl.render(f"kg-ltu-{k}", text)
        ltu[k] = stats
    (SRC / "kg-ltu-summary.json").write_text(json.dumps(ltu, indent=1), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
