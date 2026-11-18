"""Validation gates for the MAESTRO package.

    python tools/validate.py            # all gates
    python tools/validate.py --schema   # gates 1-7 only (no examples, shapes, CQs)

Gates (each prints PASS or FAIL; the process exits 1 if any fails):
  1  parse      every .ttl parses; every .rq parses with rdflib
  2  imports    owl:imports resolve inside the package, no cycles, umbrella
                imports exactly the module list
  3  namespace  declared terms are maestro:, rdfs:isDefinedBy equals the module IRI;
                external terms are declared, and nothing more, in core/resource.ttl
  4  collision  a local name is declared in one module file only
  5  rl-lint    OWL 2 RL structural lint (tools/rl_lint.py): every class and property
                used is declared, named classes only, RL datatypes, no punning, and a
                label and a definition on every maestro: term
  6  rl-closure owlrl closure: no error triples, no disjointness conflicts; no
                literal outside the declared range of its datatype property
  7  standards  every mapping target outside maestro: is in a vocabulary of the
                standards basis, and exists in its pinned copy when references/ is
                available; hook names carry no IRIs
  8  abox-terms every maestro: term used in examples, fixtures and queries is declared
  9  split      design-time example files hold no runtime instances
 10  shacl      the shapes find no violation in the modules + examples; every probe
                in shacl/probes/ gives its expected result
 11  cq         every competency question (cq/) is answered in full over the synthetic
                fixture; every LTU (ltu/) question meets its row
                floor over the use-case graphs; coverage of the competency questions by
                the use-case graphs is reported
 12  generated  build outputs are fresh
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS, DCTERMS
from rdflib.plugins.sparql import prepareQuery

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import rl_lint  # noqa: E402
from common import (MH_NS, MAESTRO_1_0, ONTOLOGY_IRI, MODULES, PKG, HHM,  # noqa: E402
                    module_files, module_path, module_iri, alignment_files, shape_files,
                    example_files, fixture_files, probe_files, query_files, parse, ontology_of, rel, new_graph,
                    with_current_names)

SH = "http://www.w3.org/ns/shacl#"
OWLRL_ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")
HOOK_NAMES = ["ECLASS", "DPP", "PRONTO", "CaSkMan", "AAS", "OpenAPI", "SAREF4INMA", "XACML"]
RUNTIME_CLASSES = {"SkillExecution", "StateAssertion", "StateTransition", "Fault", "EnergyMeasurement",
                   "PowerMeasurement", "MaintenanceAction", "Preventive", "Corrective", "ConditionBased",
                   "Predictive", "Inspection", "ExecutionRecord", "Snapshot", "Finding", "ReturnToServiceAssessment"}
DECLARATION_TYPES = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, OWL.NamedIndividual}

# The standards basis (docs/03-standards-basis.md): namespace of each external vocabulary a
# term may be mapped to, and the file that pins it under references/.
STANDARDS_BASIS = {
    "http://www.w3id.org/hsu-aut/PackML#": "hsu-packml.ttl",
    "http://www.w3id.org/hsu-aut/WADL#": "hsu-wadl.ttl",
    "http://www.w3id.org/hsu-aut/DINEN61360#": "hsu-dinen61360.ttl",
    "http://www.w3id.org/hsu-aut/VDI2206#": "hsu-vdi2206.ttl",
    "https://schema.org/": "schemaorg-extract.ttl",
    "http://www.w3id.org/hsu-aut/ISO22400-2#": "hsu-iso22400-2.ttl",
    "http://www.hsu-ifa.de/ontologies/ISA88.01#": "hsu-isa88.ttl",
    "http://www.w3id.org/hsu-aut/DINEN62264-2#": "hsu-dinen62264-2.ttl",
    "http://www.w3id.org/hsu-aut/OpcUa#": "hsu-opcua.ttl",
    "https://w3id.org/hsu-aut/AutomationML#": "hsu-automationml.ttl",
    "dtmi:dtdl:class:": "dtdl-v3-classes.ttl",
    "http://www.w3.org/ns/prov#": "prov-o.ttl",
    "http://www.w3.org/ns/odrl/2/": "odrl-core-profile-22.ttl",
}
MAPPING_PREDICATES = {SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch,
                      RDFS.subClassOf, RDFS.subPropertyOf, OWL.equivalentClass, OWL.equivalentProperty}

# Expected results of the SHACL probes in shacl/probes/: (severity, shape) per result.
SHACL_PROBES = {
    "parameter-value-wrong-datatype.ttl": [("Violation", "ParameterValueDatatypeShape")],
    "parameter-bounds-inverted.ttl": [("Violation", "ParameterDefBoundsOrderShape")],
    "state-assertion-reversed-interval.ttl": [("Violation", "StateAssertionIntervalOrderShape")],
    "execution-step-skill-mismatch.ttl": [("Warning", "ExecutionStepSkillShape")],
    "deprecated-instanceOf-alias.ttl": [],
    "deprecated-alias-wrong-datatype.ttl": [("Violation", "ParameterValueDatatypeShape")],
    "description-language-tagged.ttl": [],
    "description-not-text.ttl": [("Violation", "DescriptionTextShape")],
}

# Row floors, keyed by file name. A query file without a floor fails gate 11.
# The cq/ floors apply over the ontology plus the synthetic fixture in queries/fixtures/;
# the ltu/ floors apply over the ontology plus the use-case graphs.
CQ_MINIMUMS = {
    "cq01-station-modules-capabilities.rq": 1,
    "cq02-composite-subskills.rq": 1,
    "cq03-recipe-steps-skills.rq": 3,
    "cq04-data-bindings.rq": 3,
    "cq05-product-structure.rq": 1,
    "cq06-bom.rq": 1,
    "cq07-policy-grants.rq": 1,
    "cq08-hazards-risks-mitigations.rq": 1,
    "cq09-invocation-path.rq": 1,
    "cq10-execution-trace.rq": 2,
    "cq11-faults.rq": 1,
    "cq12-current-state.rq": 2,
    "cq13-energy-and-power.rq": 1,
    "cq14-maintenance-status.rq": 1,
    "cq15-quotes-contracts.rq": 1,
    # LTU use-case questions (queries/ltu/) over usecase-knowledge-graphs/ltu-festo-mps/.
    "lq01-io-allocation.rq": 80,
    "lq02-line-route.rq": 4,
    "lq03-grafcet-sequences.rq": 60,
    "lq04-station-bom.rq": 90,
}

# The answer fields of each competency question: a question is answered in full when at
# least one row binds every one of them. "a|b" is satisfied by either variable. Fields a
# question treats as optional (a unit, an end time, an evidence link) are not listed.
CQ_ANSWER_FIELDS = {
    "cq01-station-modules-capabilities.rq": ["station", "module", "capability"],
    "cq02-composite-subskills.rq": ["composite", "subSkill", "requiredCapability"],
    "cq03-recipe-steps-skills.rq": ["recipe", "step", "stepOrder", "skill", "flowType"],
    "cq04-data-bindings.rq": ["step", "binding", "fromParam", "toParam"],
    "cq05-product-structure.rq": ["productType", "variant|feature|requirement|identifier|instance"],
    "cq06-bom.rq": ["productType", "partType", "quantity"],
    "cq07-policy-grants.rq": ["policy", "role", "action", "target"],
    "cq08-hazards-risks-mitigations.rq": ["hazard", "risk", "mitigation", "safetyFunction", "achievedPL|achievedSIL"],
    "cq09-invocation-path.rq": ["interface", "endpoint", "protocol", "binding", "signature"],
    "cq10-execution-trace.rq": ["execution", "skill", "resource", "endpoint", "status", "start"],
    "cq11-faults.rq": ["execution", "fault", "faultCode", "specification"],
    "cq12-current-state.rq": ["subject", "dimension", "state", "validFrom"],
    "cq13-energy-and-power.rq": ["measurement", "subject", "energyKwh", "start", "source"],
    "cq14-maintenance-status.rq": ["asset", "plan", "task", "action", "finding", "outcome"],
    "cq15-quotes-contracts.rq": ["request", "quote", "provider", "marketplace", "price", "currency", "contract", "order"],
}


class Gate:
    def __init__(self, name: str) -> None:
        self.name = name
        self.problems: list[str] = []
        self.notes: list[str] = []
        self.details: list[str] = []
        self.skipped = False

    def fail(self, msg: str) -> None:
        self.problems.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def detail(self, msg: str) -> None:
        """A line printed under the gate whether it passes or fails."""
        self.details.append(msg)

    def report(self) -> bool:
        if self.skipped:
            print(f"SKIP  {self.name}: {self.notes[0] if self.notes else ''}")
            return True
        status = "PASS" if not self.problems else "FAIL"
        extra = f" ({self.notes[0]})" if self.notes and not self.problems else ""
        print(f"{status}  {self.name}{extra}")
        for p in self.problems[:40]:
            print(f"      - {p}")
        if len(self.problems) > 40:
            print(f"      ... {len(self.problems) - 40} more")
        for d in self.details:
            print(f"        {d}")
        return not self.problems


def short(t, graph: Graph | None = None) -> str:
    """Prefixed name of ``t``: maestro: always, any other prefix when ``graph`` binds one."""
    s = str(t)
    if s.startswith(MH_NS):
        return "maestro:" + s[len(MH_NS):]
    if graph is not None and isinstance(t, URIRef):
        return t.n3(graph.namespace_manager)
    return s


# --------------------------------------------------------------------------- gates

def gate_parse(all_ttl: list[Path]) -> tuple[Gate, dict[Path, Graph]]:
    g = Gate("1 parse")
    graphs: dict[Path, Graph] = {}
    for p in all_ttl:
        try:
            graphs[p] = parse(p)
        except Exception as exc:  # noqa: BLE001
            g.fail(f"{rel(p)}: {exc}")
    n_rq = 0
    for q in query_files():
        n_rq += 1
        try:
            prepareQuery(q.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            g.fail(f"{rel(q)}: {str(exc).splitlines()[0]}")
    g.note(f"{len(graphs)} turtle files, {n_rq} queries")
    return g, graphs


def gate_imports(graphs: dict[Path, Graph]) -> Gate:
    g = Gate("2 imports")
    expected = {module_iri(stem) for _, stem in MODULES}
    edges: dict[URIRef, set[URIRef]] = {}
    for layer, stem in MODULES:
        path = module_path(layer, stem)
        mg = graphs.get(path)
        if mg is None:
            g.fail(f"{rel(path)} missing")
            continue
        iri = ontology_of(mg)
        if iri != module_iri(stem):
            g.fail(f"{rel(path)}: ontology IRI is {iri}, expected {module_iri(stem)}")
            continue
        edges[iri] = set(mg.objects(iri, OWL.imports))
        for imp in edges[iri]:
            if imp not in expected:
                g.fail(f"{rel(path)} imports {imp}, which is not a module of the package")
    umbrella = graphs.get(common.UMBRELLA_FILE)
    if umbrella is None:
        g.fail("umbrella maestro.ttl missing")
    else:
        got = set(umbrella.objects(ONTOLOGY_IRI, OWL.imports))
        for m in sorted(expected - got):
            g.fail(f"umbrella does not import {m}")
        for m in sorted(got - expected):
            g.fail(f"umbrella imports {m}, which is not a module")
    for path in alignment_files():
        ag = graphs.get(path)
        if ag is None:
            continue
        iri = ontology_of(ag)
        if iri is None or ONTOLOGY_IRI not in set(ag.objects(iri, OWL.imports)):
            g.fail(f"{rel(path)} must import the umbrella {ONTOLOGY_IRI}")
    # cycles
    state: dict[URIRef, int] = {}

    def visit(n: URIRef, stack: list[URIRef]) -> None:
        if state.get(n) == 1:
            g.fail("import cycle: " + " -> ".join(short(x) for x in stack + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in edges.get(n, ()):
            visit(m, stack + [n])
        state[n] = 2

    for n in edges:
        visit(n, [])
    # every module must reach the module that declares the external terms
    signature = module_iri(common.SIGNATURE_MODULE)

    def reaches(n: URIRef, seen: set) -> bool:
        if n == signature:
            return True
        seen.add(n)
        return any(reaches(m, seen) for m in edges.get(n, ()) if m not in seen)

    for n in sorted(edges):
        if not reaches(n, set()):
            g.fail(f"{n} does not import {signature}, directly or indirectly; its import closure lacks the "
                   f"declarations of the external terms")
    g.note(f"{len(expected)} modules, umbrella and {len(alignment_files())} alignment files")
    return g


def gate_namespace(graphs: dict[Path, Graph]) -> Gate:
    g = Gate("3 namespace")
    n = external = 0
    for layer, stem in MODULES:
        path = module_path(layer, stem)
        mg = graphs.get(path)
        if mg is None:
            continue
        iri = module_iri(stem)
        for s in set(mg.subjects()):
            if not isinstance(s, URIRef) or s == iri:
                continue
            if not str(s).startswith(MH_NS):
                # A module may only *annotate* its own terms. The one exception is the signature
                # of the external vocabulary in the root module: a bare declaration, nothing else.
                statements = list(mg.predicate_objects(s))
                if stem == common.SIGNATURE_MODULE and all(p == RDF.type and o in DECLARATION_TYPES
                                                           for p, o in statements):
                    external += 1
                elif stem == common.SIGNATURE_MODULE:
                    g.fail(f"{rel(path)}: external term {s} may only be declared (a owl:Class, owl:ObjectProperty, "
                           f"owl:DatatypeProperty or owl:AnnotationProperty), not described")
                else:
                    g.fail(f"{rel(path)}: subject {s} is outside the maestro: namespace")
                continue
            types = set(mg.objects(s, RDF.type))
            if types & DECLARATION_TYPES:
                n += 1
                defined = set(mg.objects(s, RDFS.isDefinedBy))
                if defined != {iri}:
                    g.fail(f"{rel(path)}: {short(s)} rdfs:isDefinedBy {sorted(map(str, defined)) or 'missing'}, expected {iri}")
        for prefix, ns in mg.namespaces():
            if prefix == "maestro" and str(ns) != MH_NS:
                g.fail(f"{rel(path)}: prefix maestro: bound to {ns}")
    g.note(f"{n} term declarations, {external} external terms declared in {common.SIGNATURE_MODULE}")
    return g


def gate_collisions(graphs: dict[Path, Graph]) -> Gate:
    g = Gate("4 collision")
    owners: dict[str, set[str]] = defaultdict(set)
    for layer, stem in MODULES:
        mg = graphs.get(module_path(layer, stem))
        if mg is None:
            continue
        for s, o in mg.subject_objects(RDF.type):
            if o in DECLARATION_TYPES and isinstance(s, URIRef) and str(s).startswith(MH_NS):
                owners[str(s)[len(MH_NS):]].add(stem)
    for name, mods in sorted(owners.items()):
        if len(mods) > 1:
            g.fail(f"maestro:{name} declared in {sorted(mods)}")
    lowered: dict[str, set[str]] = defaultdict(set)
    for name in owners:
        lowered[name.lower()].add(name)
    for names in lowered.values():
        if len(names) > 1:
            g.note("case-variant names: " + ", ".join(sorted(names)))
    g.note(f"{len(owners)} distinct local names")
    return g


def gate_rl_lint(schema: Graph) -> Gate:
    g = Gate("5 rl-lint")
    problems, notes, counts = rl_lint.lint(schema, MH_NS)
    for p in problems:
        g.fail(p)
    g.note(f"{counts['classes']} classes, {counts['object properties']} object properties, "
           f"{counts['datatype properties']} datatype properties, {counts['individuals']} individuals, "
           f"{counts['external declarations']} external declarations")
    for n in notes:
        g.note(n)
    return g


def owlrl_check(g: Gate, graph: Graph, label: str) -> None:
    from owlrl import DeductiveClosure, OWLRL_Semantics
    work = Graph()
    for t in graph:
        work.add(t)
    DeductiveClosure(OWLRL_Semantics).expand(work)
    for _s, _p, o in work.triples((None, OWLRL_ERROR, None)):
        g.fail(f"{label}: owlrl error: {o}")
    for a, b in work.subject_objects(OWL.disjointWith):
        for node in set(work.subjects(RDF.type, a)) & set(work.subjects(RDF.type, b)):
            if not isinstance(node, Literal):
                g.fail(f"{label}: {short(node)} is both {short(a)} and {short(b)}")
    g.note(f"{label}: {len(graph)} asserted -> {len(work)} triples")


def gate_rl_closure(schema: Graph, data: Graph | None, fixture: Graph | None) -> Gate:
    g = Gate("6 rl-closure")
    owlrl_check(g, schema, "schema")
    for label, graph in (("schema+examples", data), ("schema+fixtures", fixture)):
        if graph is None:
            continue
        owlrl_check(g, graph, label)
        # The OWL 2 RL rules do not report a literal outside the range of its property, which
        # makes the graph inconsistent under OWL semantics (a DL reasoner rejects it).
        conflicts = rl_lint.range_conflicts(schema, graph)
        for c in conflicts[:20]:
            g.fail(f"{label}: {c}")
        if len(conflicts) > 20:
            g.fail(f"{label}: ... {len(conflicts) - 20} more literals outside the range of their property")
    return g


def gate_standards(graphs: dict[Path, Graph]) -> Gate:
    g = Gate("7 standards")
    stack = None
    have_stack = common.MAESTRO_1_0_STACK.is_dir()

    def maestro_stack() -> Graph:
        nonlocal stack
        if stack is None:
            stack = Graph()
            for p in sorted(common.MAESTRO_1_0_STACK.glob("**/*.ttl")):
                stack.parse(p, format="turtle")
        return stack

    bundles: dict[str, Graph | None] = {}

    def bundle(name: str) -> Graph | None:
        if name not in bundles:
            path = common.REFERENCES / name
            bundles[name] = Graph().parse(path, format="turtle") if path.exists() else None
        return bundles[name]

    in_basis = verified = unverified = maestro_1_0 = 0
    files = module_files() + [common.UMBRELLA_FILE] + alignment_files()
    for path in files:
        mg = graphs.get(path)
        if mg is None:
            continue
        is_hhm_alignment = path.name == "hhm-core.ttl" and path.parent.name == "alignment"
        for s, p, o in mg:
            if not isinstance(o, URIRef) or str(o).startswith(MH_NS):
                continue
            is_provenance = p in (DCTERMS.source, DCTERMS.references)
            if (is_provenance or p in MAPPING_PREDICATES) and str(o).startswith(MAESTRO_1_0):
                maestro_1_0 += 1
                if have_stack and (o, None, None) not in maestro_stack():
                    g.fail(f"{rel(path)}: {short(s)} {p.n3(mg.namespace_manager)} {o}: not a MAESTRO 1.0 term")
                continue
            if p not in MAPPING_PREDICATES or str(o).startswith(rl_lint.BUILTIN_NAMESPACES):
                continue
            if str(o).startswith(str(HHM)):
                if not is_hhm_alignment:
                    g.fail(f"{rel(path)}: {short(s)} maps to the placeholder {o}; allowed only in alignment/hhm-core.ttl")
                continue
            pinned = next((f for ns, f in STANDARDS_BASIS.items() if str(o).startswith(ns)), None)
            if pinned is None:
                g.fail(f"{rel(path)}: {short(s)} -> {o}: vocabulary not in the standards basis (CHG-023)")
                continue
            in_basis += 1
            ref = bundle(pinned)
            if ref is None:
                unverified += 1
            elif (o, None, None) in ref or (None, None, o) in ref:
                verified += 1
            else:
                g.fail(f"{rel(path)}: {short(s)} -> {o}: term not found in references/{pinned}")
    # hook names must never sit next to an IRI or a mapping predicate
    pattern = re.compile(r"\b(" + "|".join(HOOK_NAMES) + r")\b")
    for path in files + shape_files() + example_files():
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and ("Match" in line or "subClassOf" in line or "subPropertyOf" in line
                                         or "equivalent" in line):
                g.fail(f"{rel(path)}:{i}: hook name next to a mapping: {line.strip()[:80]}")
    g.note(f"{in_basis} mapping targets in the standards basis"
           + (f", {verified} found in their pinned copy" if verified else ""))
    if unverified:
        g.detail(f"not checked: whether {unverified} mapping targets exist in their vocabulary "
                 f"(no pinned copies at {common.REFERENCES})")
    if maestro_1_0 and not have_stack:
        g.detail(f"not checked: whether {maestro_1_0} dct:source / dct:references targets are MAESTRO 1.0 terms "
                 f"(no MAESTRO 1.0 sources at {common.MAESTRO_1_0_STACK})")
    return g


def gate_abox_terms(schema: Graph, graphs: dict[Path, Graph]) -> Gate:
    g = Gate("8 abox-terms")
    declared = {str(s) for s in schema.subjects() if isinstance(s, URIRef) and str(s).startswith(MH_NS)}
    used: dict[str, set[str]] = defaultdict(set)
    for path in example_files() + fixture_files() + probe_files():
        eg = graphs.get(path)
        if eg is None:
            continue
        for t in eg:
            for x in t:
                if isinstance(x, URIRef) and str(x).startswith(MH_NS):
                    used[str(x)].add(rel(path))
    for q in query_files():
        for name in set(re.findall(r"\bmaestro:([A-Za-z][A-Za-z0-9_]*)", q.read_text(encoding="utf-8"))):
            used[MH_NS + name].add(rel(q))
    for term, where in sorted(used.items()):
        if term not in declared:
            g.fail(f"{short(URIRef(term))} used in {sorted(where)} but not declared")
    g.note(f"{len(used)} distinct maestro: terms used in examples, fixtures, probes and queries")
    return g


def gate_split(graphs: dict[Path, Graph]) -> Gate:
    g = Gate("9 split")
    for path in example_files():
        if path.name == "runtime.ttl":
            continue
        eg = graphs.get(path)
        if eg is None:
            continue
        for s, o in eg.subject_objects(RDF.type):
            if isinstance(o, URIRef) and str(o).startswith(MH_NS) and str(o)[len(MH_NS):] in RUNTIME_CLASSES:
                g.fail(f"{rel(path)}: {s} is a {short(o)}; runtime instances belong in runtime.ttl")
    return g


def load_shapes(paths: list[Path]) -> Graph:
    """Union of shape files; a shape IRI declared twice is an error."""
    g = Graph()
    owners: dict[URIRef, Path] = {}
    for p in paths:
        part = Graph().parse(p, format="turtle")
        for shape in set(part.subjects(RDF.type, URIRef(SH + "NodeShape"))) | set(part.subjects(RDF.type, URIRef(SH + "PropertyShape"))):
            if isinstance(shape, URIRef):
                if shape in owners:
                    raise AssertionError(f"shape {shape} declared in both {owners[shape].name} and {p.name}")
                owners[shape] = p
        for t in part:
            g.add(t)
    return g


def shacl_results(data: Graph, schema: Graph, shapes: Graph) -> list[dict]:
    """Validation results of ``data`` (which includes the schema) as plain records.

    Data written with a deprecated 0.1.0 name is validated under the name that replaced it
    (common.with_current_names); RDFS inference supplies the subclass and domain/range types.
    """
    import pyshacl
    _conforms, results, _text = pyshacl.validate(data_graph=with_current_names(data, schema), shacl_graph=shapes,
                                                 inference="rdfs", abort_on_first=False, meta_shacl=False,
                                                 advanced=True, debug=False)
    out = []
    for r in results.subjects(RDF.type, URIRef(SH + "ValidationResult")):
        def value(name: str):
            return next(iter(results.objects(r, URIRef(SH + name))), None)
        shape = value("sourceShape")
        out.append({"severity": str(value("resultSeverity") or SH + "Violation").rsplit("#", 1)[-1],
                    "focus": value("focusNode"), "path": value("resultPath"),
                    "component": value("sourceConstraintComponent"), "message": str(value("resultMessage") or ""),
                    "shape": str(shape)[len(str(common.MHSH)):] if str(shape).startswith(str(common.MHSH)) else None})
    return sorted(out, key=lambda r: (r["severity"], str(r["focus"]), str(r["path"]), r["message"]))


def gate_shacl(schema: Graph, data: Graph | None, fixture: Graph | None, graphs: dict[Path, Graph]) -> Gate:
    g = Gate("10 shacl")
    shapes = shape_files()
    if data is None or not shapes:
        g.skipped = True
        g.note("no examples or no shapes yet")
        return g
    try:
        sg = load_shapes(shapes)
    except AssertionError as exc:
        g.fail(str(exc))
        return g
    # --- modules + use-case graphs
    warnings = 0
    for r in shacl_results(data, schema, sg):
        if r["severity"] != "Violation":
            warnings += 1
        else:
            g.fail(f"{short(r['focus'], data)}: {r['message']}")
    # --- synthetic fixture
    if fixture is not None:
        for r in shacl_results(fixture, schema, sg):
            if r["severity"] == "Violation":
                g.fail(f"fixture: {short(r['focus'], fixture)}: {r['message']}")
    # --- probes
    probes = probe_files()
    for path in probes:
        expected = SHACL_PROBES.get(path.name)
        if expected is None:
            g.fail(f"{rel(path)}: no expectation in SHACL_PROBES")
            continue
        probe = new_graph()
        probe += schema
        probe += graphs[path]
        got = sorted((r["severity"], r["shape"] or r["message"]) for r in shacl_results(probe, schema, sg))
        if got != sorted(expected):
            g.fail(f"{rel(path)}: expected {sorted(expected) or 'no result'}, got {got or 'no result'}")
    for name in sorted(set(SHACL_PROBES) - {p.name for p in probes}):
        g.fail(f"shacl/probes/{name}: listed in SHACL_PROBES but missing")
    n_shapes = len(set(sg.subjects(RDF.type, URIRef(SH + "NodeShape"))))
    g.note(f"{n_shapes} node shapes; examples: {warnings} warning(s); {len(probes)} probes")
    return g


def answer_coverage(rows: list, fields: list[str]) -> tuple[int, list[str]]:
    """(rows that bind every answer field, answer fields no row binds)."""
    def bound(row, field: str) -> bool:
        return any(name in row.labels and row[name] is not None for name in field.split("|"))
    complete = sum(1 for row in rows if all(bound(row, f) for f in fields))
    return complete, [f for f in fields if not any(bound(row, f) for row in rows)]


def gate_cq(data: Graph | None, fixture: Graph | None) -> Gate:
    g = Gate("11 cq")
    queries = query_files()
    if data is None or not queries:
        g.skipped = True
        g.note("no examples or no queries yet")
        return g
    if fixture is None:
        g.fail("no synthetic fixture under queries/fixtures/; the competency questions have nothing to run over")
    answered = partial = empty = 0
    for q in queries:
        floor = CQ_MINIMUMS.get(q.name)
        if floor is None:
            g.fail(f"{q.name}: no row floor in CQ_MINIMUMS")
            continue
        text = q.read_text(encoding="utf-8")
        try:
            rows = list(data.query(text))
        except Exception as exc:  # noqa: BLE001
            g.fail(f"{q.name}: {exc}")
            continue
        if q.parent.name != "cq":
            # LTU questions: floors over the source-derived graphs
            if len(rows) < floor:
                g.fail(f"{q.name}: {len(rows)} row(s) over the use-case graphs, floor {floor}")
            continue
        fields = CQ_ANSWER_FIELDS.get(q.name)
        if fields is None:
            g.fail(f"{q.name}: no answer fields in CQ_ANSWER_FIELDS")
            continue
        # acceptance: the schema answers the question in full over the synthetic fixture
        if fixture is not None:
            fixture_rows = list(fixture.query(text))
            complete, unbound = answer_coverage(fixture_rows, fields)
            if len(fixture_rows) < floor:
                g.fail(f"{q.name}: {len(fixture_rows)} row(s) over the fixture, floor {floor}")
            elif not complete:
                g.fail(f"{q.name}: no fixture row binds every answer field (never bound: {', '.join(unbound) or '-'})")
        # coverage: what the source-derived graphs can answer today (reported, never a failure)
        complete, unbound = answer_coverage(rows, fields)
        name = q.name.split("-")[0].upper()
        if not rows:
            empty += 1
            g.detail(f"{name}  no data  the use-case graphs hold no records for this question")
        elif not complete:
            partial += 1
            g.detail(f"{name}  partial  {len(rows)} row(s), none binds every answer field"
                     + (f" (never bound: {', '.join(unbound)})" if unbound else ""))
        else:
            answered += 1
            g.detail(f"{name}  answered {complete} of {len(rows)} row(s) bind every answer field")
    for name in sorted(set(CQ_MINIMUMS) - {q.name for q in queries}):
        g.fail(f"{name}: listed in CQ_MINIMUMS but missing")
    g.note(f"{len(queries)} queries; competency questions over the use-case graphs: {answered} answered, "
           f"{partial} partial, {empty} without data")
    return g


def gate_generated() -> Gate:
    g = Gate("12 generated")
    try:
        import build
        for problem in build.check():
            g.fail(problem)
    except ImportError:
        g.note("build.py not present")
    try:
        import gen_alignment
        for problem in gen_alignment.check():
            g.fail(problem)
    except ImportError:
        g.note("gen_alignment.py not present")
    try:
        import gen_graph
        for problem in gen_graph.check():
            g.fail(problem)
    except ImportError:
        g.note("gen_graph.py not present")
    try:
        import merge_usecases
        term_module, term_order = merge_usecases.load_tbox()
        for unit in merge_usecases.units():
            path = merge_usecases.merged_path(unit)
            if not path.exists() or common.read_text(path) != merge_usecases.merged_text(unit, term_module, term_order):
                g.fail(f"{rel(path)} is stale; run tools/merge_usecases.py")
    except ImportError:
        g.note("merge_usecases.py not present")
    return g


# --------------------------------------------------------------------------- main

def union(schema: Graph, graphs: dict[Path, Graph], paths: list[Path]) -> Graph | None:
    paths = [p for p in paths if p in graphs]
    if not paths:
        return None
    out = new_graph()
    out += schema
    for p in paths:
        for prefix, ns in graphs[p].namespaces():
            out.bind(prefix, ns, override=False, replace=False)
        out += graphs[p]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schema", action="store_true", help="schema gates only (1-7)")
    args = ap.parse_args()

    all_ttl = (module_files() + [common.UMBRELLA_FILE] + alignment_files() + shape_files() + example_files()
               + fixture_files() + probe_files())
    all_ttl = [p for p in all_ttl if p.exists()]
    g1, graphs = gate_parse(all_ttl)
    ok = g1.report()
    if not ok:
        print("parse failures; later gates need every file to parse")
        return 1

    schema = new_graph()
    for layer, stem in MODULES:
        mg = graphs.get(module_path(layer, stem))
        if mg is not None:
            for prefix, ns in mg.namespaces():
                schema.bind(prefix, ns, override=False)
            schema += mg
    data = fixture = None
    if not args.schema:
        data = union(schema, graphs, example_files())
        fixture = union(schema, graphs, fixture_files())

    gates = [gate_imports(graphs), gate_namespace(graphs), gate_collisions(graphs),
             gate_rl_lint(schema), gate_rl_closure(schema, data, fixture), gate_standards(graphs)]
    if not args.schema:
        gates += [gate_abox_terms(schema, graphs), gate_split(graphs), gate_shacl(schema, data, fixture, graphs),
                  gate_cq(data, fixture), gate_generated()]
    for gate in gates:
        ok = gate.report() and ok
    unchecked = sum(1 for gate in gates for d in gate.details if d.startswith("not checked"))
    print("MAESTRO validation " + ("passed" if ok else "FAILED")
          + (f"; {unchecked} check(s) could not run in this checkout (see 'not checked' above)" if unchecked else ""))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
