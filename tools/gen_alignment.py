"""Generate the alignment files of the MAESTRO package.

    python tools/gen_alignment.py --write   # (re)write docs/hhm-conformance.md and alignment/*.ttl
    python tools/gen_alignment.py --check   # report stale files, write nothing

The two alignment files are optional outputs that the package does not ship.
They are written only when the MAESTRO 1.0 sources are available (the
ontologies/ folder next to the package, as in the MAESTRO 1.0 repository),
because every target of alignment/maestro-1.0.ttl has to be verified against
them. docs/hhm-conformance.md needs the package only and is always written.

alignment/maestro-1.0.ttl
    One skos:exactMatch per dct:source and one skos:closeMatch per
    dct:references annotation found on the package's terms, pointing at the
    MAESTRO 1.0 term the definition was taken from. Every target is checked
    to exist in the MAESTRO stack (ontologies/**).

alignment/hhm-core.ttl
    owl:equivalentClass / owl:equivalentProperty between the package's terms
    and the HHM-Core v1 terms of the consortium diagram, in the placeholder
    namespace https://w3id.org/hhm-core#. The HHM term list below is the
    class and relation set drawn in the two HHM-Core v1 diagrams the package
    follows; the package adopted the HHM names, so the mapping is by local
    name and the script reports any HHM term the package lacks.

Both files import the umbrella and are not imported by it: the equivalences
target an unpublished namespace, and the MAESTRO matches would pull the
MAESTRO 1.0 IRIs into the default closure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, DCTERMS

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (MH_NS, MAESTRO_1_0, MAESTRO_1_0_STACK, ONTOLOGY_IRI, PKG, HHM, MODULES,  # noqa: E402
                    load_modules, module_path, parse, rel, write_text, read_text)

OUT_MAESTRO = PKG / "alignment" / "maestro-1.0.ttl"
OUT_HHM = PKG / "alignment" / "hhm-core.ttl"
OUT_CONFORMANCE = PKG / "docs" / "hhm-conformance.md"

# HHM-Core v1: the classes and relations of the consortium diagram
# ("HHM Core Ontology (v1)") and of its minimal digital-twin extension.
HHM_CLASSES = [
    # Product
    "ProductType", "ProductInstance", "Variant", "Feature", "Requirement", "Identifier", "BOMNode", "Material",
    # Physical resources
    "Station", "Module", "Capability",
    # Skills
    "Skill", "AtomicSkill", "CompositeSkill", "ParameterDef", "ParameterValue", "Precondition", "Postcondition",
    "SkillInterface",
    # Recipe / planning
    "Recipe", "PlanStep", "ControlFlowConstraint", "DataBinding",
    # Safety / security / policy
    "Policy", "Constraint", "Hazard", "Risk", "Mitigation", "Mode", "Role", "Permission", "Evidence",
    # Invocation hooks
    "Endpoint", "Protocol", "Binding",
    # Minimal execution
    "SkillExecution", "ExecutionStatus", "Fault", "TimeInterval",
    # Digital-twin diagram
    "SkillService", "EventStream", "DigitalTwin", "TwinBinding",
]
HHM_RELATIONS = [
    "hasVariant", "hasFeature", "hasBOM", "madeOf", "hasPart", "appliesTo", "hasIdentifier", "hasInstance",
    "hasModule", "providesCapability",
    "hasParameterDef", "hasPrecondition", "hasPostcondition", "requiresCapability", "hasInterfaceContract",
    "hasSubSkillLink", "instanceOf",
    "hasStep", "hasControlFlow", "hasDataBinding", "realizedBy", "requiresOperation",
    "contains", "increases", "reduces", "hasEvidence", "grantedTo", "requiresMode", "requiresPermission", "constrains",
    "exposedVia", "usesProtocol", "hasBinding",
    "executes", "executedOn", "invokedVia", "hasInput", "hasStatus", "mayRaise", "hasTime",
    # Digital-twin diagram
    "emits", "represents", "exposesService", "usesEventStream", "hasExecutionHistory", "hasTwinBinding", "mapsTo",
]

# HHM-Core terms the package carries under a clearer name since 0.2.0 (HHM name -> package name).
# The HHM name stays declared in the package as an owl:deprecated equivalent of the new term.
HHM_RENAMED = {
    "BOMNode": "BOMItem", "Mode": "OperatingMode",
    "hasBOM": "hasBOMItem", "hasPart": "hasSubItem", "hasSubSkillLink": "hasSubSkill", "instanceOf": "valueOf",
    "contains": "hasConstraint", "increases": "causesRisk", "mayRaise": "raisedFault",
}


def package_name(hhm_name: str) -> str:
    """Local name of the package term that carries an HHM-Core term."""
    return HHM_RENAMED.get(hhm_name, hhm_name)

HEADER_PREFIXES = """@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix maestro:   <https://w3id.org/maestro#> .
"""


def header(iri: str, title: str, description: str, comment: str, version: str) -> str:
    return (f"<{iri}> a owl:Ontology ;\n"
            f"    owl:versionIRI <{iri}/{version}> ;\n"
            f"    owl:versionInfo \"{version}\" ;\n"
            f"    dct:title \"{title}\" ;\n"
            f"    rdfs:label \"{title}\"@en ;\n"
            f"    dct:description \"{description}\"@en ;\n"
            f"    rdfs:comment \"{comment}\"@en ;\n"
            f"    dct:creator \"Melwin Xavier\" ;\n"
            f"    dct:license <https://opensource.org/licenses/MIT> ;\n"
            f"    dct:source <https://github.com/melwinxavier/MAESTRO> ;\n"
            f"    dct:isPartOf <{ONTOLOGY_IRI}> ;\n"
            f"    owl:imports <{ONTOLOGY_IRI}> .\n")


def local(t: URIRef) -> str:
    return str(t)[len(MH_NS):]


def term_kinds(schema: Graph) -> dict[URIRef, str]:
    kinds: dict[URIRef, str] = {}
    for s, o in schema.subject_objects(RDF.type):
        if not (isinstance(s, URIRef) and str(s).startswith(MH_NS)):
            continue
        if o == OWL.Class:
            kinds[s] = "class"
        elif o in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
            kinds[s] = "property"
        elif o == OWL.NamedIndividual and s not in kinds:
            kinds[s] = "individual"
    return kinds


def maestro_stack() -> Graph:
    g = Graph()
    for p in sorted(MAESTRO_1_0_STACK.glob("**/*.ttl")):
        g.parse(p, format="turtle")
    return g


def gen_maestro(schema: Graph, version: str, stack: Graph | None) -> tuple[str, list[str]]:
    problems: list[str] = []
    exact, close = [], []
    for s, o in schema.subject_objects(DCTERMS.source):
        if isinstance(s, URIRef) and str(s).startswith(MH_NS) and isinstance(o, URIRef) and str(o).startswith(MAESTRO_1_0):
            exact.append((s, o))
    for s, o in schema.subject_objects(DCTERMS.references):
        if isinstance(s, URIRef) and str(s).startswith(MH_NS) and isinstance(o, URIRef) and str(o).startswith(MAESTRO_1_0):
            close.append((s, o))
    if stack is not None:
        for s, o in exact + close:
            if (o, None, None) not in stack:
                problems.append(f"{local(s)}: {o} is not a MAESTRO 1.0 term")
    kinds = term_kinds(schema)
    deprecated = {s for s, o in schema.subject_objects(OWL.deprecated) if o.toPython() is True}
    unmapped = sorted(local(t) for t, k in kinds.items() if k != "individual" and t not in deprecated
                      and t not in {s for s, _ in exact} and t not in {s for s, _ in close})
    n_terms = sum(1 for t, k in kinds.items() if k != "individual" and t not in deprecated)
    comment = (f"Generated by tools/gen_alignment.py from the dct:source and dct:references annotations of the package. "
               f"{len(exact)} exact and {len(close)} close matches; {n_terms - len(unmapped)} of {n_terms} classes and "
               f"properties have a MAESTRO 1.0 counterpart (not counting the {len(deprecated)} deprecated 0.1.0 names). "
               f"Terms without one: {', '.join(unmapped) or 'none'}.")
    lines = [HEADER_PREFIXES,
             "#################################################################",
             "# GENERATED - do not edit. Regenerate with tools/gen_alignment.py --write",
             "#################################################################", "",
             header(f"{ONTOLOGY_IRI}/alignment/maestro-1.0", "MAESTRO: alignment to MAESTRO 1.0",
                    "Documentary matches from the terms of the package to the MAESTRO 1.0 terms whose definitions they reuse.",
                    comment, version),
             "# exactMatch: same concept, definition reused (dct:source)"]
    for s, o in sorted(exact, key=lambda x: (local(x[0]), str(x[1]))):
        lines.append(f"maestro:{local(s)} skos:exactMatch <{o}> .")
    lines += ["", "# closeMatch: adapted or narrowed concept (dct:references)"]
    for s, o in sorted(close, key=lambda x: (local(x[0]), str(x[1]))):
        lines.append(f"maestro:{local(s)} skos:closeMatch <{o}> .")
    return "\n".join(lines) + "\n", problems


def gen_hhm(schema: Graph, version: str) -> tuple[str, list[str]]:
    problems: list[str] = []
    kinds = term_kinds(schema)
    by_name = {local(t): (t, k) for t, k in kinds.items()}
    cls_lines, prop_lines, missing = [], [], []
    for name in HHM_CLASSES:
        hit = by_name.get(package_name(name))
        if hit is None or hit[1] != "class":
            missing.append(name)
            continue
        cls_lines.append(f"maestro:{package_name(name)} owl:equivalentClass hhm:{name} .")
    for name in HHM_RELATIONS:
        hit = by_name.get(package_name(name))
        if hit is None or hit[1] != "property":
            missing.append(name)
            continue
        prop_lines.append(f"maestro:{package_name(name)} owl:equivalentProperty hhm:{name} .")
    if missing:
        problems.append("HHM-Core terms without a package term: " + ", ".join(missing))
    comment = (f"Generated by tools/gen_alignment.py. Coverage of the HHM-Core v1 diagrams: "
               f"{len(cls_lines)} of {len(HHM_CLASSES)} classes and {len(prop_lines)} of {len(HHM_RELATIONS)} relations. "
               f"{len(HHM_RENAMED)} HHM terms are carried under a clearer package name: "
               + ", ".join(f"{h} -> {p}" for h, p in HHM_RENAMED.items()) + ". "
               "The hhm: namespace is a placeholder: HHM-Core v1 was supplied as a Graphviz schema, not as published IRIs; "
               "repoint it when the consortium issues one. Logical axioms to a placeholder namespace are kept out of the "
               "umbrella import closure.")
    lines = [HEADER_PREFIXES + "@prefix hhm:  <https://w3id.org/hhm-core#> .\n",
             "#################################################################",
             "# GENERATED - do not edit. Regenerate with tools/gen_alignment.py --write",
             "#################################################################", "",
             header(f"{ONTOLOGY_IRI}/alignment/hhm-core", "MAESTRO: alignment to HHM-Core v1",
                    "Equivalences between the terms of the package and the HHM-Core v1 consortium reference model.",
                    comment, version),
             "# Classes"] + cls_lines + ["", "# Relations"] + prop_lines
    return "\n".join(lines) + "\n", problems


def gen_conformance(schema: Graph, version: str) -> str:
    """docs/hhm-conformance.md: every class and relation of the HHM-Core v1 diagrams and the package term that carries it."""
    from rdflib.namespace import RDFS
    kinds = term_kinds(schema)
    by_name = {local(t): t for t in kinds}

    def module_of(t: URIRef) -> str:
        m = next(schema.objects(t, RDFS.isDefinedBy), None)
        return str(m).rsplit("/", 1)[-1] if m else ""

    def row(name: str, want: str) -> str:
        t = by_name.get(package_name(name))
        if t is None or kinds[t] != want:
            return f"| `{name}` | missing | | |"
        name = package_name(name)
        dom = ", ".join(f"`{local(o)}`" for o in schema.objects(t, RDFS.domain) if isinstance(o, URIRef) and str(o).startswith(MH_NS)) or "open"
        rng = ", ".join(f"`{local(o)}`" for o in schema.objects(t, RDFS.range) if isinstance(o, URIRef) and str(o).startswith(MH_NS))
        if want == "class":
            return f"| `{name}` | `maestro:{name}` | {module_of(t)} | |"
        note = f"{dom} -> {rng}" if rng else f"{dom} -> open"
        return f"| `{name}` | `maestro:{name}` | {module_of(t)} | {note} |"

    def carried(n: str, want: str) -> bool:
        t = by_name.get(package_name(n))
        return t is not None and kinds[t] == want

    n_cls = sum(1 for n in HHM_CLASSES if carried(n, "class"))
    n_rel = sum(1 for n in HHM_RELATIONS if carried(n, "property"))
    out = [f"# HHM-Core v1 conformance ({version})", "",
           "Generated by `tools/gen_alignment.py`; do not edit. Every class and relation drawn in the HHM Core "
           "Ontology (v1) diagram and in its minimal digital-twin extension, with the package term that carries it "
           "and the module that declares it. The package adopted the HHM names, so a term is conformant when it "
           "exists under the same local name, except for the terms renamed in 0.2.0 for clarity ("
           + ", ".join(f"`{h}` -> `maestro:{p}`" for h, p in HHM_RENAMED.items())
           + "); the HHM names of those remain declared as deprecated equivalents. The three implied relations "
           "`targetStep`, `bindsFrom` and `bindsTo` are additions, not HHM terms, and are not listed.", "",
           f"Coverage: {n_cls} of {len(HHM_CLASSES)} classes, {n_rel} of {len(HHM_RELATIONS)} relations.", "",
           "## Classes", "", "| HHM-Core | Package term | Module | |", "|---|---|---|---|"]
    out += [row(n, "class") for n in HHM_CLASSES]
    out += ["", "## Relations", "", "| HHM-Core | Package term | Module | Domain -> range |", "|---|---|---|---|"]
    out += [row(n, "property") for n in HHM_RELATIONS]
    out += ["", "## HHM extension points", "",
            "| Extension point (HHM diagram) | Realised by | Status |", "|---|---|---|",
            "| DPP / DPPO / RePlanIT product passport | - | hook only (not in the standards basis) |",
            "| ECLASS / eClassOWL semanticId | - | hook only (not in the standards basis) |",
            "| PRONTO variant / BOM semantics | - | hook only (not in the standards basis) |",
            "| AutomationML / CAEX topology | `experimental-extensions/automationml.ttl` | HSU AutomationML ODP |",
            "| ISA-88 equipment model | `experimental-extensions/isa88.ttl` | HSU ISA88.01 ODP, documentary |",
            "| CSS / CaSkMan capability-skill patterns | - | hook only (not in the standards basis) |",
            "| SOSA / SSN observation evidence | - | hook only (sensor module removed by decision) |",
            "| QUDT / OM units | `maestro:unitRef` literal (QUDT unit IRI) | hook only (unit module removed by decision) |",
            "| ISA-88 procedural model | `experimental-extensions/isa88.ttl` | HSU ISA88.01 ODP, documentary |",
            "| ISA-95 / IEC 62264 | `experimental-extensions/isa95.ttl`, `maestro:ProductionOrder` | HSU DIN EN 62264-2 ODP, HSU ISO 22400-2 ODP |",
            "| Rules / validation (SHACL / ODRL / XACML) | `shacl/`, `experimental-extensions/odrl.ttl` | SHACL; ODRL 2.2 core profile; XACML hook only |",
            "| OPC UA / VDMA | `experimental-extensions/opcua.ttl` | HSU OPC UA ODP |",
            "| REST / OpenAPI | `experimental-extensions/rest.ttl` | HSU WADL ODP; OpenAPI named as interface description language only |",
            "| DTDL | `experimental-extensions/dtdl.ttl` | DTDL v3 metamodel class identifiers |",
            "| AAS submodel publication | `maestro:AasSubmodelTemplateIDL`, `maestro:TwinBinding` | hook only (not in the standards basis) |",
            "| SAREF4INMA traceability | - | hook only (not in the standards basis) |",
            "| PROV-O provenance | `experimental-extensions/prov.ttl` | W3C PROV-O, logical bridge |", ""]
    return "\n".join(out)


def generate(with_stack: bool = True) -> tuple[dict[Path, str], list[str]]:
    schema = load_modules()
    umbrella = parse(PKG / "maestro.ttl")
    version = str(next(umbrella.objects(ONTOLOGY_IRI, OWL.versionInfo)))
    stack = maestro_stack() if with_stack else None
    m_text, m_problems = gen_maestro(schema, version, stack)
    h_text, h_problems = gen_hhm(schema, version)
    c_text = gen_conformance(schema, version)
    return {OUT_MAESTRO: m_text, OUT_HHM: h_text, OUT_CONFORMANCE: c_text}, m_problems + h_problems


def check() -> list[str]:
    """Stale generated files. The two alignment files are optional outputs: the package does
    not ship them, so they are compared only where they exist; docs/hhm-conformance.md is
    committed and always compared."""
    files, problems = generate(with_stack=False)
    for path, content in files.items():
        if not path.exists():
            if path == OUT_CONFORMANCE:
                problems.append(f"{rel(path)} missing; run tools/gen_alignment.py --write")
        elif read_text(path) != content:
            problems.append(f"{rel(path)} is stale; run tools/gen_alignment.py --write")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        problems = check()
        for p in problems:
            print("STALE", p)
        print("alignment files " + ("fresh" if not problems else "STALE"))
        return 1 if problems else 0
    have_stack = MAESTRO_1_0_STACK.is_dir()
    files, problems = generate(with_stack=have_stack)
    for p in problems:
        print("PROBLEM", p)
    if problems:
        return 1
    if not have_stack:
        # Without the MAESTRO 1.0 sources the targets of alignment/maestro-1.0.ttl cannot be
        # verified, and an unverified mapping is not written. The conformance table needs
        # the package only.
        print(f"MAESTRO 1.0 sources not found at {MAESTRO_1_0_STACK}: the alignment files are not written, "
              f"because their targets cannot be verified; only {rel(OUT_CONFORMANCE)} is generated")
        files = {OUT_CONFORMANCE: files[OUT_CONFORMANCE]}
    if args.write:
        for path, content in files.items():
            write_text(path, content)
            if path.suffix == ".ttl":
                Graph().parse(path, format="turtle")
            print("wrote", rel(path))
    else:
        for path, content in files.items():
            print(f"--- {rel(path)} ({content.count(chr(10))} lines)")
        print("dry run; pass --write to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
