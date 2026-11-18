"""Shared helpers of the knowledge-graph figures (used by render_kg_ltu.py and render_v020.py).

load_tbox() maps every maestro: class and property to the module that declares it, and
place() picks the module cluster an individual is drawn in (an individual typed only with
an extension class goes to the core cluster of its superclass, e.g.
maestro:DtdlInterface -> Skills). esc() and clip() prepare label text for Graphviz.
Needs rdflib.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph

HERE = Path(__file__).resolve().parent                     # figures/v0.2.0/scripts
PKG = HERE.parents[2]

MH = "https://w3id.org/maestro#"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def clip(s: str, n: int = 46) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


# ---------------------------------------------------------------- T-box: class and property -> module

def load_tbox(model: dict):
    mods = {m["id"]: m for m in model["modules"]}
    by_file = {m["file"]: m["id"] for m in model["modules"]}
    cls_mod, prop_mod, supers = {}, {}, defaultdict(set)
    for f, mid in by_file.items():
        p = PKG / f
        if not p.exists():
            continue
        g = Graph().parse(p)
        for c in g.subjects(RDF.type, OWL.Class):
            if str(c).startswith(MH):
                cls_mod.setdefault(str(c), mid)
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for pr in g.subjects(RDF.type, kind):
                if str(pr).startswith(MH):
                    prop_mod.setdefault(str(pr), mid)
        for a, b in g.subject_objects(RDFS.subClassOf):
            supers[str(a)].add(str(b))
    return mods, cls_mod, prop_mod, supers


def place(types: list[str], mods, cls_mod, supers) -> str | None:
    """Module cluster for an individual: a core/module class wins over an extension class;
    an extension-only individual goes to the core/module cluster of a superclass if one exists."""
    rank = {"core": 0, "module": 1, "ext": 2}
    cands = [cls_mod[t] for t in types if t in cls_mod]
    if not cands:
        return None
    best = min(cands, key=lambda m: (rank[mods[m]["layer"]], m))
    if mods[best]["layer"] != "ext":
        return best
    seen, todo = set(), list(types)
    while todo:
        t = todo.pop()
        for s in sorted(supers.get(t, ())):
            if s in seen:
                continue
            seen.add(s)
            if s in cls_mod and mods[cls_mod[s]]["layer"] != "ext":
                return cls_mod[s]
            todo.append(s)
    return best
