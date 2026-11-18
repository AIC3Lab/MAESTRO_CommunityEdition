"""Render the LTU Festo MPS knowledge graphs in the style of proposed-maestro.png.

    python figures/v0.2.0/scripts/render_kg_ltu.py

Reads usecase-knowledge-graphs/ltu-festo-mps/<unit>/<unit>-merged.ttl (plus
shared/shared-merged.ttl), the single-file form of each unit's core/ and ext/ files, and writes, into
usecase-knowledge-graphs/:

  kg-ltu-overview.png / .svg   the whole use case on one sheet, clustered by file
                               (shared, the four stations, the line): hierarchy,
                               stations with their modules and counts, capabilities,
                               station cycle skills, GRAFCET recipes, line recipe,
                               workpiece and the links between the stations
  kg-ltu-<unit>.png / .svg     the full graph of one production unit (distributing,
                               testing, processing, handling, line), every individual in
                               the cluster of the MAESTRO module that declares its class,
                               as in figures/v0.2.0/png/kg-*.png

In the unit figures, identifiers (terminal bit, pin, BMK, part number), pre- and
postconditions are rows inside their owner node; enumeration values (direction,
protocol, flow type, action, energy source, role) are rows too. Shared individuals
(capabilities, catalogue product types, hazards, risks, tasks, the line, LTU, other
units' nodes) are grey dashed nodes. Graphviz sources go to src/kg-ltu-*.gv.
Needs Graphviz `dot` on PATH, rdflib and Pillow.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import textwrap
from collections import defaultdict
from pathlib import Path

from PIL import Image
from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef

import render_kg as rk

Image.MAX_IMAGE_PIXELS = None

HERE = Path(__file__).resolve().parent                     # figures/v0.2.0/scripts
PKG = HERE.parents[2]
EX = PKG / "usecase-knowledge-graphs" / "ltu-festo-mps"
OUT = HERE.parent / "png"
SVG = HERE.parent / "svg"
SRC = HERE.parent / "src"
DPI = 80

MH = rk.MH
BASE = "https://w3id.org/maestro/examples/ltu-festo-mps/"
UNITS = {
    "distributing": ("dis", "Distributing station (VE, station 1)", "Stack magazine + Changer; feeds workpieces to the line"),
    "testing": ("tes", "Testing station (PR, station 2)", "Material recognition, lifting, analogue height measuring, accept / reject"),
    "processing": ("pro", "Processing station (BE, station 3)", "Rotary indexing table, orientation check, drilling, electrical ejector"),
    "handling": ("han", "Handling station (HA, station 4)", "PicAlfa pick & place, sorts black / red-silver onto two slides"),
    "line": ("lin", "MPS line", "Station links, workpiece and line recipe"),
}
PREFIXES = [(MH, "maestro:"), (BASE + "shared#", "ltu:"), ("http://www.w3.org/2001/XMLSchema#", "xsd:"),
            ("http://qudt.org/vocab/unit/", "unit:")] + [(f"{BASE}{k}#", f"{p}:") for k, (p, _, _) in UNITS.items()]
SKIP_LITERALS = {MH + "description", str(RDFS.comment), str(RDFS.label)}
FOLD_TYPES = {"Identifier", "Precondition", "Postcondition"}
ROW_TYPES = {"Protocol", "Role", "ParameterDirection", "ControlFlowType", "Action", "DataFormat",
             "EnergySource", "InterfaceDescriptionLanguage", "OperatingMode", "PerformanceLevel", "RiskLevel"}
UNIT_COLOR = {"shared": "#6b7280", "distributing": "#12A594", "testing": "#E54D2E", "processing": "#3B82F6",
              "handling": "#6E56CF", "line": "#0F766E"}


def short(u: str) -> str:
    for ns, p in PREFIXES:
        if u.startswith(ns):
            return p + u[len(ns):]
    return u


def lname(u) -> str:
    return re.split(r"[#/]", str(u))[-1]


def load_all() -> Graph:
    full = Graph()
    for f in sorted(EX.glob("**/*-merged.ttl")):
        full.parse(f)
    return full


def unit_graph(key: str) -> Graph:
    g = Graph()
    for f in sorted((EX / key).glob("*-merged.ttl")):
        g.parse(f)
    return g


# ---------------------------------------------------------------- unit figure

def build_unit(key: str, full: Graph, mods, cls_mod, prop_mod, supers) -> tuple[str, dict]:
    pfx, name, system = UNITS[key]
    g = unit_graph(key)
    ns = f"{BASE}{key}#"

    def label(u) -> str:
        lab = full.value(u, RDFS.label)
        return str(lab) if lab is not None else short(str(u)).split(":", 1)[-1]

    def types_of(u) -> list[str]:
        return sorted(str(t) for t in full.objects(u, RDF.type) if str(t).startswith(MH))

    def tnames(u) -> set[str]:
        return {lname(t) for t in types_of(u)}

    def is_unit(u) -> bool:
        return isinstance(u, URIRef) and str(u).startswith(ns)

    def as_row(o) -> bool:
        if str(o).startswith(MH):
            return True                          # maestro: enumeration individual
        return bool(tnames(o) & ROW_TYPES)

    def fold_text(o) -> str:
        t = tnames(o)
        if "Identifier" in t:
            return f"{full.value(o, URIRef(MH + 'identifierScheme'))} = {full.value(o, URIRef(MH + 'identifierValue'))}"
        return label(o) + "  [" + str(full.value(o, URIRef(MH + "expression")) or "") + "]"

    folded = {s for s in g.subjects(RDF.type) if is_unit(s) and tnames(s) & FOLD_TYPES}
    own = sorted({s for s in g.subjects(RDF.type) if is_unit(s) and (s, RDF.type, OWL.Ontology) not in g
                  and s not in folded}, key=str)
    nodes: dict[URIRef, dict] = {s: {"shared": False, "rows": defaultdict(list)} for s in own}
    edges: list[tuple] = []
    for s, p, o in g:
        ps = str(p)
        if p == RDF.type or ps in SKIP_LITERALS or (s, RDF.type, OWL.Ontology) in g or s in folded:
            continue
        pn = short(ps).split(":", 1)[-1] if ps.startswith(MH) else short(ps).replace("rdfs:", "")
        if not isinstance(s, URIRef):
            continue
        if s not in nodes:                       # statement about a shared node (ltu:LTU maestro:operates ...)
            nodes[s] = {"shared": True, "rows": defaultdict(list)}
        if isinstance(o, Literal):
            if nodes[s]["shared"]:
                continue
            v = str(o)
            if o.datatype is not None and str(o.datatype).endswith("anyURI"):
                v = short(v)
            nodes[s]["rows"][pn].append(v)
        elif o in folded:
            nodes[s]["rows"][pn].append(fold_text(o))
        elif as_row(o):
            nodes[s]["rows"][pn].append(label(o) if not str(o).startswith(MH) else lname(o))
        else:
            if o not in nodes:
                nodes[o] = {"shared": not is_unit(o), "rows": defaultdict(list)}
            edges.append((s, o, pn, ps))

    members: dict[str, list] = defaultdict(list)
    loose: list = []
    for u in nodes:
        m = rk.place(types_of(u), mods, cls_mod, supers)
        (members[m] if m else loose).append(u)
    nid = {u: f"n{i}" for i, u in enumerate(nodes)}

    def node_label(u) -> str:
        n = nodes[u]
        head = "<BR/>".join(rk.esc(x) for x in textwrap.wrap(label(u), 34)) or rk.esc(short(str(u)))
        tline = rk.esc(short(str(u)) + "  a " + ", ".join(short(t) for t in types_of(u)))
        rows = []
        for k, v in sorted(n["rows"].items()):
            vals = sorted(set(v))
            if k in ("hasIdentifier", "hasPrecondition", "hasPostcondition"):
                rows += [f"{rk.esc(k)} : {rk.esc(rk.clip(x, 70))}" for x in vals]
            else:
                rows.append(f"{rk.esc(k)} : {rk.esc(rk.clip(', '.join(vals)))}")
        out = ('<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
               f'<TR><TD ALIGN="CENTER"><B>{head}</B></TD></TR>'
               f'<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="7" COLOR="#777777">{tline}</FONT></TD></TR>')
        if rows:
            out += ('<HR/><TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#555555">'
                    + '<BR ALIGN="LEFT"/>'.join(rows) + "</FONT></TD></TR>")
        return out + "</TABLE>>"

    style_of = {"core": "rounded", "module": "rounded,dashed", "ext": "rounded,dotted"}
    n_own = sum(1 for u in nodes if not nodes[u]["shared"])
    n_shared = len(nodes) - n_own
    title = (f"LTU Festo MPS - {name}: knowledge graph on MAESTRO  ·  {system}\\n"
             f"{n_own} individuals (+{len(folded)} identifiers / conditions shown as rows), {n_shared} shared nodes (grey dashed), "
             f"{len(edges)} object-property links, {len(g)} triples  ·  source usecase-knowledge-graphs/ltu-festo-mps/{key}/*.ttl")
    out = [f"// LTU Festo MPS {name} knowledge graph, clustered by MAESTRO module.",
           "// Generated by figures/v0.2.0/scripts/render_kg_ltu.py from the example Turtle files; do not edit.",
           f"digraph KG_LTU_{key.upper()} {{",
           'rankdir=LR; compound=true; nodesep=0.25; ranksep=0.9; fontname="Helvetica"; fontsize=18; newrank=true;'
           f' labelloc="t"; label="{title}";',
           'node [shape=box style="rounded,filled" fillcolor="#f9f9fb" fontname="Helvetica" fontsize=10 margin="0.08,0.04"];',
           'edge [fontname="Helvetica" fontsize=8 arrowsize=0.7];']
    order = [m["id"] for m in mods.values()]
    for mid in sorted(members, key=order.index):
        m = mods[mid]
        out.append(f'subgraph cluster_{mid} {{ label="{m["title"]}\\n{m["file"]}"; color="{m["color"]}"; '
                   f'fontcolor="{m["color"]}"; style="{style_of[m["layer"]]}"; penwidth=1.4;')
        for u in sorted(members[mid], key=lambda x: (nodes[x]["shared"], types_of(x), label(x))):
            if nodes[u]["shared"]:
                out.append(f'  {nid[u]} [label={node_label(u)} color="#9ca3af" fillcolor="#ffffff" style="rounded,filled,dashed"];')
            else:
                out.append(f'  {nid[u]} [label={node_label(u)} color="{m["color"]}" fillcolor="#f9f9fb"];')
        out.append("}")
    for u in loose:
        out.append(f'{nid[u]} [label={node_label(u)} color="#6b7280"];')
    for s, o, pn, ps in edges:
        mid = prop_mod.get(ps)
        if mid is None:
            out.append(f'{nid[s]} -> {nid[o]} [label="{pn}" color="#9ca3af" fontcolor="#6b7280" style=dotted];')
            continue
        m = mods[mid]
        st = {"core": "", "module": " style=dashed", "ext": " style=dotted"}[m["layer"]]
        out.append(f'{nid[s]} -> {nid[o]} [label="{pn}" color="{m["color"]}" fontcolor="{m["color"]}"{st}];')
    out.append("}")
    stats = {"name": name, "individuals": n_own, "folded": len(folded), "shared": n_shared,
             "links": len(edges), "triples": len(g)}
    return "\n".join(out), stats


# ---------------------------------------------------------------- overview figure

def build_overview(full: Graph) -> str:
    """Top-down overview: hierarchy, the four stations in line order with their links,
    the line recipe under them, the workpiece; capabilities as rows, not edges."""
    M = lambda x: URIRef(MH + x)  # noqa: E731
    sh = lambda x: URIRef(BASE + "shared#" + x)  # noqa: E731
    lin = lambda x: URIRef(BASE + "line#" + x)  # noqa: E731

    def label(u) -> str:
        lab = full.value(u, RDFS.label)
        return str(lab) if lab is not None else lname(u)

    def box(nid_, title, typ, rows=(), color="#6b7280", dashed=False, fill="#f9f9fb", width=44):
        head = "<BR/>".join(rk.esc(x) for x in textwrap.wrap(title, 38))
        r = ('<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
             f'<TR><TD ALIGN="CENTER"><B>{head}</B></TD></TR>'
             f'<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="8" COLOR="#777777">{rk.esc(typ)}</FONT></TD></TR>')
        lines = []
        for x in rows:
            lines += textwrap.wrap(x, width, subsequent_indent="   ") or [""]
        if lines:
            r += ('<HR/><TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#444444">'
                  + '<BR ALIGN="LEFT"/>'.join(rk.esc(x) for x in lines) + "</FONT></TD></TR>")
        r += "</TABLE>>"
        st = "rounded,filled,dashed" if dashed else "rounded,filled"
        return f'  {nid_} [label={r} color="{color}" fillcolor="{fill}" style="{st}" penwidth=1.4];'

    ids: dict = {}

    def nid(u) -> str:
        return ids.setdefault(u, f"n{len(ids)}")

    clusters: dict[str, list[str]] = defaultdict(list)
    edges: list[str] = []
    ranks: dict[str, list[str]] = defaultdict(list)

    def edge(a, b, lab, color="#4b5563", style="", extra=""):
        st = f" style={style}" if style else ""
        key = "xlabel" if "constraint=false" in extra else "label"   # dot cannot route labelled flat edges across clusters
        edges.append(f'{nid(a)} -> {nid(b)} [{key}=" {lab} " color="{color}" fontcolor="{color}"{st}{extra}];')

    # --- shared: hierarchy, capabilities, safety, catalogue
    hier = [(sh("LTU"), "ltu:LTU  a maestro:Enterprise, maestro:Actor", ["operates the four stations (maestro:operates)"]),
            (sh("LTUSite"), "ltu:LTUSite  a maestro:Site", []), (sh("MPSLab"), "ltu:MPSLab  a maestro:Area", []),
            (sh("MPSLine"), "ltu:MPSLine  a maestro:WorkCenter", [])]
    for u, typ, rows in hier:
        clusters["shared"].append(box(nid(u), label(u), typ, rows, "#0F766E"))
        ranks["top"].append(nid(u))
    edge(sh("LTU"), sh("LTUSite"), "partOfEnterprise (inverse)", "#0F766E", "dotted", " dir=back")
    edge(sh("LTUSite"), sh("MPSLab"), "partOfSite (inverse)", "#0F766E", "dotted", " dir=back")
    edge(sh("MPSLab"), sh("MPSLine"), "partOfArea (inverse)", "#0F766E", "dotted", " dir=back")
    caps = [c for c in sorted(full.subjects(RDF.type, M("Capability")), key=label) if str(c).startswith(BASE + "shared#")]
    clusters["shared"].append(box("caps", f"{len(caps)} capabilities", "ltu:*Capability  a maestro:Capability",
                                  [", ".join(label(c) for c in caps)], "#9ca3af", dashed=True, fill="#ffffff", width=60))
    n_pt = len({s for s in full.subjects(RDF.type, M("ProductType")) if str(s).startswith(BASE + "shared#PT_")})
    clusters["shared"].append(box("catalogue", f"Festo component catalogue: {n_pt} part numbers",
                                  "ltu:PT_<part no.>  a maestro:ProductType + maestro:Identifier",
                                  ["the station bills of materials point here (maestro:nodeFor)"], "#9ca3af", dashed=True, fill="#ffffff"))
    clusters["shared"].append(box("safety", "MPS notes on safety", "ltu:MPSSafetyRules  a maestro:Policy",
                                  ["8 shared + 2 Handling constraints",
                                   "hazards: cylinder motion on air-on, moving station, overpressure; + drill spindle, lift in working area",
                                   "trainees may maestro:Invoke the station cycles", "emergency stop per station console"],
                                  "#111827", width=50))
    clusters["shared"].append(box("protocols", "Protocols, roles, tasks", "maestro:Protocol, maestro:Role, maestro:MaintenanceTask",
                                  ["SysLink digital I/O (XMA2, XMG1)", "SysLink analogue (XMA3)", "StationLink optical 1-bit link",
                                   "roles: Instructor, Trainee", "4 cleaning / check tasks"], "#F59E0B"))
    ranks["top"] += ["caps", "catalogue", "safety", "protocols"]

    # --- the four stations
    for key in ["distributing", "testing", "processing", "handling"]:
        pfx, name, system = UNITS[key]
        nsu = f"{BASE}{key}#"
        st = URIRef(nsu + "Station")
        mods_ = sorted(full.objects(st, M("hasModule")), key=label)
        sigs = [s for s in full.subjects(RDF.type, M("ParameterDef")) if str(s).startswith(nsu)
                and lname(s).split("_")[0] in ("DI", "DO", "AI", "CC")]
        boms = [s for s in full.subjects(RDF.type, M("BOMItem")) if str(s).startswith(nsu)]
        skills = {s for s in full.subjects(RDF.type) if str(s).startswith(nsu)
                  and ((s, RDF.type, M("AtomicSkill")) in full or (s, RDF.type, M("CompositeSkill")) in full)}
        eps = sorted(lname(e) for e in full.subjects(RDF.type, M("Endpoint")) if str(e).startswith(nsu))
        idrows = [f"{full.value(i, M('identifierScheme'))}: {full.value(i, M('identifierValue'))}"
                  for i in full.objects(st, M("hasIdentifier"))]
        provided = sorted({label(c) for m in mods_ for c in full.objects(m, M("providesCapability"))})
        col = UNIT_COLOR[key]
        clusters[key].append(box(nid(st), name, f"{pfx}:Station  a maestro:Station, maestro:WorkUnit  ({key}/plant.ttl)",
                                 [system] + sorted(idrows) +
                                 [f"modules ({len(mods_)}): " + ", ".join(label(m) for m in mods_),
                                  "modules provide: " + ", ".join(provided),
                                  f"{len(sigs)} signals (maestro:ParameterDef) over " + ", ".join(eps),
                                  f"{len(boms)} BOM nodes, {len(skills)} skills"], col, width=58))
        ranks["stations"].append(nid(st))
        edge(sh("MPSLine"), st, "partOfWorkCenter (inverse)", "#0F766E", "dotted", " dir=back")
        cyc = [s for s in full.subjects(RDF.type, M("CompositeSkill")) if str(s).startswith(nsu)][0]
        subs = sorted(label(x) for x in full.objects(cyc, M("hasSubSkill")))
        req = sorted(label(c) for c in full.objects(cyc, M("requiresCapability")))
        faults = [str(full.value(f, M("faultCode"))) for f in full.objects(cyc, M("mayRaiseFault"))]
        clusters[key].append(box(nid(cyc), label(cyc), f"{short(str(cyc))}  a maestro:CompositeSkill",
                                 ["hasSubSkillLink: " + ", ".join(subs), "requiresCapability: " + ", ".join(req)]
                                 + (["mayRaiseFault: " + ", ".join(faults)] if faults else []), "#E54D2E", width=58))
        ranks["skills"].append(nid(cyc))
        seq = URIRef(nsu + "ControlSequence")
        steps = list(full.objects(seq, M("hasStep")))
        flows = defaultdict(int)
        for s in steps:
            for c in full.objects(s, M("hasControlFlow")):
                flows[lname(full.value(c, M("flowType")))] += 1
        clusters[key].append(box(nid(seq), label(seq), f"{pfx}:ControlSequence  a maestro:Recipe  ({key}/product.ttl)",
                                 [f"{len(steps)} GRAFCET steps (maestro:PlanStep)",
                                  "transitions: " + ", ".join(f"{v} {k}" for k, v in sorted(flows.items()))], "#3B82F6"))
        ranks["seqs"].append(nid(seq))
        edge(st, cyc, "skill of the station", "#9ca3af", "dotted")
        edge(cyc, seq, "hasStep / realizedBy (inverse)", "#3B82F6", "", " dir=back")

    # station links (AutomationML internal links in line/plant.ttl)
    def station_of_port(port):
        for m in full.subjects(M("hasInterface"), port):
            for st in full.subjects(M("hasModule"), m):
                return st
    for link in sorted(full.subjects(RDF.type, M("InternalLink")), key=str):
        if not str(link).startswith(BASE + "line#"):
            continue
        a, b = sorted(full.objects(link, M("linksInterface")), key=str)
        sa, sb = station_of_port(a), station_of_port(b)
        if "Material" in lname(link):
            src, dst = (sa, sb) if "Out" in lname(a) else (sb, sa)
            edge(src, dst, "material hand-over (lin:InternalLink)", "#111827", "bold", " constraint=false")
        else:
            tx, rx = (sa, sb) if "Tx" in lname(a) else (sb, sa)
            edge(tx, rx, "StationLink busy / free (lin:InternalLink)", "#EA580C", "dashed", " constraint=false")

    # --- line recipe and workpiece
    rec = lin("MPSLineRecipe")
    clusters["line"].append(box(nid(rec), label(rec), "lin:MPSLineRecipe  a maestro:Recipe  (line/product.ttl)", [], "#3B82F6"))
    lsteps = sorted(full.objects(rec, M("hasStep")), key=lambda s: int(full.value(s, M("stepOrder"))))
    for s in lsteps:
        cond = [str(full.value(cf, M("expression"))) for cf in full.objects(s, M("hasControlFlow"))]
        clusters["line"].append(box(nid(s), label(s), f"{short(str(s))}  a maestro:PlanStep",
                                    [f"to next step when: {c}" for c in cond], "#3B82F6", width=46))
        ranks["line"].append(nid(s))
        for k in full.objects(s, M("realizedBy")):
            edge(k, s, "realizedBy (inverse)", "#3B82F6", "", " dir=back")
    for a, b in zip(lsteps, lsteps[1:]):
        edge(a, b, "Precedes", "#3B82F6", "bold", " constraint=false")
    ranks["product"].append(nid(rec))
    edge(rec, lsteps[0], "hasStep (x4)", "#3B82F6", "", " dir=back")
    wp = lin("Workpiece")
    vrows = [f"{label(v)}: height {full.value(full.value(v, M('hasRequirement')), M('requiredValue'))}"
             for v in sorted(full.objects(wp, M("hasVariant")), key=label)]
    clusters["line"].append(box(nid(wp), label(wp), "lin:Workpiece  a maestro:ProductType  + 3 maestro:Variant", vrows, "#6E56CF", width=52))
    fo = lin("F_Opening")
    clusters["line"].append(box(nid(fo), label(fo), "lin:F_Opening  a maestro:Feature", ["requirement: opening faces upwards (mandatory)"], "#6E56CF"))
    ranks["product"] += [nid(wp), nid(fo)]
    edge(wp, fo, "hasFeature", "#6E56CF", "", " constraint=false")
    edge(lsteps[2], fo, "requiresOperation (inverse)", "#6E56CF", "", " dir=back")

    title = ("LTU Festo MPS line: knowledge graph overview on MAESTRO\\n"
             "Distributing -> Testing -> Processing -> Handling  ·  shared/shared.ttl + <unit>/plant.ttl + <unit>/product.ttl  ·  "
             f"{len(full)} triples  ·  every individual and link in kg-ltu-<unit>.png")
    out = ["// LTU Festo MPS knowledge graph overview, clustered by file / production unit.",
           "// Generated by figures/v0.2.0/scripts/render_kg_ltu.py from the example Turtle files; do not edit.",
           "digraph KG_LTU_OVERVIEW {",
           'rankdir=TB; compound=true; nodesep=0.5; ranksep=0.9; fontname="Helvetica"; fontsize=22; newrank=true;'
           f' labelloc="t"; label="{title}";',
           'node [shape=box style="rounded,filled" fillcolor="#f9f9fb" fontname="Helvetica" fontsize=12 margin="0.12,0.06"];',
           'edge [fontname="Helvetica" fontsize=10 arrowsize=0.8];']
    titles = {"shared": "shared/shared.ttl  (ltu:)"} | {k: f"{k}/  plant.ttl + product.ttl  ({UNITS[k][0]}:)" for k in UNITS}
    for k in ["shared", "distributing", "testing", "processing", "handling", "line"]:
        out.append(f'subgraph cluster_{k} {{ label="{titles[k]}"; color="{UNIT_COLOR[k]}"; fontcolor="{UNIT_COLOR[k]}"; '
                   'fontsize=16; style="rounded"; penwidth=2; labeljust="l";')
        out += clusters[k]
        out.append("}")
    for r in ("top", "stations", "skills", "seqs", "line", "product"):
        out.append("{ rank=same; " + "; ".join(ranks[r]) + "; }")
    for r in ("top", "stations", "skills", "seqs", "line", "product"):
        out += [f"{a} -> {b} [style=invis weight=10];" for a, b in zip(ranks[r], ranks[r][1:])]
    # pin each column: station -> cycle skill -> GRAFCET recipe -> its line step
    for col in zip(ranks["stations"], ranks["skills"], ranks["seqs"], ranks["line"]):
        out += [f"{a} -> {b} [style=invis weight=100];" for a, b in zip(col, col[1:])]
    out.append(f'{ranks["top"][3]} -> {ranks["stations"][0]} [style=invis weight=5];')
    out += edges
    out.append("}")
    return "\n".join(out)


def render(name: str, text: str) -> None:
    exe = shutil.which("dot")
    if not exe:
        raise SystemExit("Graphviz `dot` not found on PATH")
    gv = SRC / f"{name}.gv"
    gv.write_text(text, encoding="utf-8")
    png = OUT / f"{name}.png"
    subprocess.run([exe, "-Tpng", f"-Gdpi={DPI}", str(gv), "-o", str(png)], check=True)
    svg = subprocess.run([exe, "-Tsvg", str(gv)], check=True, capture_output=True, text=True, encoding="utf-8").stdout
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)
    SVG.mkdir(exist_ok=True)
    (SVG / f"{name}.svg").write_text(svg, encoding="utf-8")
    with Image.open(png) as im:
        print(f"  png/{name}.png  {im.width} x {im.height}")


def main() -> None:
    SRC.mkdir(exist_ok=True)
    import gen_graph
    mods, cls_mod, prop_mod, supers = rk.load_tbox(gen_graph.build_model())
    full = load_all()
    render("kg-ltu-overview", build_overview(full))
    summary = {}
    for k in UNITS:
        text, stats = build_unit(k, full, mods, cls_mod, prop_mod, supers)
        render(f"kg-ltu-{k}", text)
        summary[k] = stats
    (SRC / "kg-ltu-summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
