"""Generate docs/graph.html, the class and property graph of the package.

    python tools/gen_graph.py            # write docs/graph.html
    python tools/gen_graph.py --check    # report a stale page, write nothing

The page renders Graphviz in the browser (viz.js from cdnjs) from a model
derived here from the Turtle modules: one cluster per module, one box per
class listing its datatype properties, one arrow per object property.
Properties with an open domain or range are drawn between the classes their
schema:domainIncludes and schema:rangeIncludes annotations name. Relations of the HHM-Core diagrams are drawn solid,
added relations dashed. Terms marked owl:deprecated (0.1.0 names kept as equivalents) are not drawn. The template is tools/graph_template.html.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS, DCTERMS, XSD

SCHEMA = Namespace("https://schema.org/")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (MH_NS, MODULES, PKG, layer_dir, module_path, module_iri, parse, rel, write_text,  # noqa: E402
                    read_text)
from gen_alignment import HHM_RELATIONS, package_name  # noqa: E402

HHM_PACKAGE_RELATIONS = {package_name(n) for n in HHM_RELATIONS}

TEMPLATE = PKG / "tools" / "graph_template.html"
OUT = PKG / "docs" / "graph.html"

MODULE_META = {
    "resource": ("Physical Resources", "#12A594", "core"),
    "skill": ("Skills", "#E54D2E", "core"),
    "recipe": ("Recipe / Planning", "#3B82F6", "core"),
    "product": ("Product", "#6E56CF", "core"),
    "invocation": ("Invocation Hooks", "#F59E0B", "core"),
    "policy": ("Safety / Security / Policy", "#111827", "core"),
    "execution": ("Minimal Execution (optional)", "#8B5CF6", "core"),
    "runtime": ("Runtime State", "#7C3AED", "module"),
    "energy": ("Energy", "#CA8A04", "module"),
    "maintenance": ("Maintenance", "#B91C1C", "module"),
    "maas": ("Manufacturing as a Service", "#0369A1", "module"),
    "digital-twin": ("Digital Twin", "#0EA5E9", "ext"),
    "opcua": ("OPC UA", "#EA580C", "ext"),
    "isa88": ("ISA-88 bridge", "#6B7280", "ext"),
    "isa95": ("ISA-95 hierarchy", "#0F766E", "ext"),
    "automationml": ("AutomationML topology", "#4B5563", "ext"),
    "dtdl": ("DTDL", "#2563EB", "ext"),
    "rest": ("REST", "#D97706", "ext"),
    "prov": ("PROV-O bridge", "#9333EA", "ext"),
    "odrl": ("ODRL bridge", "#374151", "ext"),
}
EXT_NOTES = {
    "product": ["DPP / product passport view (hook only)", "ECLASS semanticId (hook only)", "PRONTO variant/BOM semantics (hook only)"],
    "resource": ["AutomationML / CAEX topology -> experimental-extensions/automationml.ttl", "ISA-88 equipment model -> experimental-extensions/isa88.ttl", "Package-wide: ValueSet, transitive hasPart / partOf (super-property of hasModule, hasStep, hasSubSkill, hasSubItem)"],
    "skill": ["QUDT: unitRef holds a QUDT unit IRI (hook only)", "SOSA observation evidence (hook only)", "CSS / CaSkMan patterns (hook only)"],
    "recipe": ["ISA-88 procedural model -> experimental-extensions/isa88.ttl", "ISA-95 / IEC 62264 -> experimental-extensions/isa95.ttl, maestro:ProductionOrder"],
    "policy": ["SHACL shapes in shacl/ ; ODRL core profile -> experimental-extensions/odrl.ttl ; XACML (hook only)"],
    "invocation": ["OPC UA -> experimental-extensions/opcua.ttl", "REST (WADL) -> experimental-extensions/rest.ttl", "DTDL -> experimental-extensions/dtdl.ttl", "AAS submodel publish (hook only)"],
    "execution": ["PROV-O -> experimental-extensions/prov.ttl", "SAREF4INMA traceability (hook only)"],
    "runtime": ["ExecutionStatus (core) is a subclass of State"],
    "energy": ["Bare-number properties carry fixed units (kWh, W, g CO2-eq/kWh)"],
    "maintenance": ["Module also carries mtbfHours and remainingUsefulLifeHours"],
    "maas": ["Role individuals CustomerRole, ProviderRole, MarketplaceRole", "schema.org and ISO 22400-2 closeMatch"],
    "digital-twin": ["AAS packaging, DTDL twin model via mapsTo (hook only)"],
    "opcua": ["HSU OPC UA ODP closeMatch"],
    "isa88": ["Documentary closeMatch: Recipe -> ISA88:RecipeProcedure, PlanStep -> ISA88:Phase, Station -> ISA88:Unit, Module -> ISA88:EquipmentModule"],
    "isa95": ["HSU DIN EN 62264-2 ODP closeMatch"],
    "automationml": ["Module becomes an InternalElement; HSU AutomationML ODP matches"],
    "dtdl": ["DTDL v3 metamodel class identifiers"],
    "rest": ["HSU WADL ODP: RestBinding close to WADL:Method"],
    "prov": ["SkillExecution subClassOf prov:Activity; executes / hasInput / executedOn subPropertyOf prov:used; hasOutput subPropertyOf prov:generated"],
    "odrl": ["Policy, Permission subClassOf odrl:Policy, odrl:Permission; hasPermission / action / target / grantedTo subPropertyOf odrl:"],
}


def local(t) -> str:
    return str(t)[len(MH_NS):]


# Datatype properties whose range is rdfs:Literal because they hold plain or language-tagged
# text; every other rdfs:Literal range is the numeric contract (docs/02-conventions.md).
TEXT_PROPERTIES = {"description"}


def package_terms(g: Graph, owl_type) -> list:
    """The maestro: terms of one kind declared in ``g``; declared external terms are not drawn."""
    return sorted((t for t in g.subjects(RDF.type, owl_type) if isinstance(t, URIRef) and str(t).startswith(MH_NS)),
                  key=str)


def dt_label(g: Graph, p: URIRef) -> str:
    rng = next(g.objects(p, RDFS.range), None)
    if rng is None:
        return "literal"
    if rng == RDFS.Literal:
        return "text" if local(p) in TEXT_PROPERTIES else "number"
    return str(rng).rsplit("#", 1)[-1]


def deprecated(g: Graph, t) -> bool:
    return any(o.toPython() is True for o in g.objects(t, OWL.deprecated))


def build_model() -> dict:
    graphs = {stem: parse(module_path(layer, stem)) for layer, stem in MODULES}
    union = Graph()
    for g in graphs.values():
        union += g
    class_owner = {}
    for stem, g in graphs.items():
        for c in g.subjects(RDF.type, OWL.Class):
            if isinstance(c, URIRef) and str(c).startswith(MH_NS):
                class_owner[local(c)] = stem
    # open-domain datatype properties, attached to the classes their schema:domainIncludes name
    hinted: dict[str, list[str]] = defaultdict(list)
    for p in package_terms(union, OWL.DatatypeProperty):
        if (p, RDFS.domain, None) in union:
            continue
        for cls in union.objects(p, SCHEMA.domainIncludes):
            if isinstance(cls, URIRef) and str(cls).startswith(MH_NS):
                hinted[local(cls)].append(f"{local(p)} : {dt_label(union, p)}  (open domain)")
    individuals_by_class: dict[str, list[str]] = defaultdict(list)
    for s, o in union.subject_objects(RDF.type):
        if (s, RDF.type, OWL.NamedIndividual) in union and isinstance(o, URIRef) and str(o).startswith(MH_NS) \
                and o != OWL.NamedIndividual and local(o) in class_owner:
            lbl = str(next(union.objects(s, RDFS.label), local(s)))
            individuals_by_class[local(o)].append(lbl)
    modules = []
    for layer, stem in MODULES:
        g = graphs[stem]
        title, color, lyr = MODULE_META[stem]
        classes, props, sub = [], [], []
        # datatype properties by domain
        dps_by_domain: dict[str, list[str]] = defaultdict(list)
        open_dps = []
        for p in package_terms(g, OWL.DatatypeProperty):
            if deprecated(g, p):
                continue
            doms = [local(d) for d in g.objects(p, RDFS.domain) if isinstance(d, URIRef) and str(d).startswith(MH_NS)]
            text = f"{local(p)} : {dt_label(g, p)}"
            if doms:
                for d in doms:
                    dps_by_domain[d].append(text)
            else:
                open_dps.append(text)
        for c in package_terms(g, OWL.Class):
            if deprecated(g, c):
                continue
            name = local(c)
            dps = list(dps_by_domain.get(name, [])) + sorted(hinted.get(name, []))
            inds = sorted(set(individuals_by_class.get(name, [])))
            if inds:
                shown = ", ".join(inds[:8]) + (f", … ({len(inds)})" if len(inds) > 8 else "")
                dps.append("individuals: " + shown)
            src = None
            if (c, DCTERMS.source, None) in g:
                src = "MAESTRO 1.0"
            elif (c, DCTERMS.references, None) in g:
                src = "adapted from MAESTRO 1.0"
            classes.append([name, dps, src] if src and lyr != "core" or (src and stem in ("policy", "invocation") and _folded(g, c)) else [name, dps])
            for parent in g.objects(c, RDFS.subClassOf):
                if isinstance(parent, URIRef) and str(parent).startswith(MH_NS):
                    sub.append([name, local(parent)])
        # subclass axioms stated about classes owned elsewhere (e.g. ExecutionStatus in runtime)
        for s, o in g.subject_objects(RDFS.subClassOf):
            if isinstance(s, URIRef) and isinstance(o, URIRef) and str(s).startswith(MH_NS) and str(o).startswith(MH_NS):
                pair = [local(s), local(o)]
                if pair not in sub:
                    sub.append(pair)
        for p in package_terms(g, OWL.ObjectProperty):
            if deprecated(g, p):
                continue
            name = local(p)
            doms = [local(d) for pred in (RDFS.domain, SCHEMA.domainIncludes) for d in g.objects(p, pred)
                    if isinstance(d, URIRef) and str(d).startswith(MH_NS)]
            rngs = [local(r) for pred in (RDFS.range, SCHEMA.rangeIncludes) for r in g.objects(p, pred)
                    if isinstance(r, URIRef) and str(r).startswith(MH_NS)]
            pairs = [(d, r) for d in doms for r in rngs]
            if not pairs and doms:
                pairs = [(d, "open") for d in doms]
            style = "" if name in HHM_PACKAGE_RELATIONS else "dashed"
            tag = None
            if (p, DCTERMS.references, None) in g:
                tag = "adapted"
            elif (p, DCTERMS.source, None) not in g:
                tag = "added"
            for d, r in pairs:
                if r == "open":
                    continue
                props.append([name, d, r, style, tag])
        notes = list(EXT_NOTES.get(stem, []))
        own = {c[0] for c in classes}
        foreign = [f"{d}.{txt}" for d, texts in dps_by_domain.items() if d not in own for txt in texts]
        if foreign:
            notes.append("datatype properties on classes of other modules: " + ", ".join(foreign))
        if open_dps:
            notes.append("open-domain datatype properties (drawn on the classes that use them): " + ", ".join(open_dps))
        modules.append({"id": stem.replace("-", "_"), "layer": lyr, "title": title, "file": f"{layer_dir(layer)}/{stem}.ttl",
                        "color": color, "classes": classes, "sub": sub, "props": props, "ext": notes})
    return {"ns": "maestro:", "modules": modules}


def _folded(g: Graph, c: URIRef) -> bool:
    """A core class folded in from a MAESTRO module other than the cluster's own source."""
    for o in g.objects(c, DCTERMS.source):
        s = str(o)
        if "/safety#" in s or "/communication#" in s:
            return True
    return False


def render() -> str:
    tpl = read_text(TEMPLATE)
    model = build_model()
    return tpl.replace("__MODEL_JSON__", json.dumps(model, ensure_ascii=False, indent=1))


def check() -> list[str]:
    content = render()
    if not OUT.exists():
        return [f"{rel(OUT)} missing; run tools/gen_graph.py"]
    if read_text(OUT) != content:
        return [f"{rel(OUT)} is stale; run tools/gen_graph.py"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        problems = check()
        for p in problems:
            print("STALE", p)
        return 1 if problems else 0
    content = render()
    write_text(OUT, content)
    model = json.loads(content[content.index("const MODEL = ") + len("const MODEL = "):content.index(";\n\n// ---------- where the nine")])
    n_cls = sum(len(m["classes"]) for m in model["modules"])
    n_props = len({p[0] for m in model["modules"] for p in m["props"]})
    print(f"wrote {rel(OUT)}: {len(model['modules'])} modules, {n_cls} classes, {n_props} object properties drawn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
