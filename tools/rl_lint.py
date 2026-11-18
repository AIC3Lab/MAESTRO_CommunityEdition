"""Structural lint of the MAESTRO modules against OWL 2 RL and the package conventions.

    problems, notes, counts = lint(schema, MH_NS)

The checks work on the RDF graph of the modules and need rdflib only. They cover
what docs/02-conventions.md asks of a module and what a profile validator would
reject:

  declarations   every class and property that is used is declared; a term that is
                 used but not declared takes a graph out of the OWL 2 profiles, so an
                 external term needs a declaration too (core/resource.ttl holds them)
  kinds          a term is one kind of thing (no punning); property axioms relate
                 properties of the same kind; characteristics sit on the right kind
  expressions    named classes only: no restrictions, unions, enumerations or other
                 anonymous classes
  ranges         a datatype property ranges over a datatype of the OWL 2 RL datatype
                 map, an object property over a class
  literals       no ill-typed literal
  hierarchy      no subclass or subproperty cycle; no class under two disjoint classes
  documentation  every term of the package has a language-tagged rdfs:label and a
                 skos:definition or rdfs:comment

This is a lint, not a reasoner: it reports the structural causes of profile
violations, not entailments. Standalone replacement for tests/profile_check.py of the
MAESTRO 1.0 repository.
"""

from __future__ import annotations

from collections import defaultdict

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD

BUILTIN_NAMESPACES = (str(RDF), str(RDFS), str(OWL), str(XSD))
PROPERTY_KINDS = {OWL.ObjectProperty: "object property", OWL.DatatypeProperty: "datatype property",
                  OWL.AnnotationProperty: "annotation property"}
OBJECT_ONLY = {OWL.TransitiveProperty, OWL.SymmetricProperty, OWL.AsymmetricProperty, OWL.IrreflexiveProperty,
               OWL.InverseFunctionalProperty}
NOT_IN_RL = {OWL.ReflexiveProperty}
ANONYMOUS_CLASS_TERMS = [OWL.Restriction, OWL.unionOf, OWL.intersectionOf, OWL.complementOf, OWL.oneOf,
                         OWL.onProperty, OWL.someValuesFrom, OWL.allValuesFrom, OWL.hasValue]
# Datatypes of the OWL 2 RL datatype map (OWL 2 Profiles, section 4.2); owl:real and owl:rational are not in RL.
RL_DATATYPES = {RDFS.Literal, RDF.PlainLiteral, RDF.XMLLiteral, XSD.decimal, XSD.integer, XSD.nonNegativeInteger,
                XSD.nonPositiveInteger, XSD.positiveInteger, XSD.negativeInteger, XSD.long, XSD.int, XSD.short,
                XSD.byte, XSD.unsignedLong, XSD.unsignedInt, XSD.unsignedShort, XSD.unsignedByte, XSD.float,
                XSD.double, XSD.string, XSD.normalizedString, XSD.token, XSD.language, XSD.Name, XSD.NCName,
                XSD.NMTOKEN, XSD.boolean, XSD.hexBinary, XSD.base64Binary, XSD.anyURI, XSD.dateTime,
                XSD.dateTimeStamp}


def builtin(term) -> bool:
    return str(term).startswith(BUILTIN_NAMESPACES)


def lint(schema: Graph, local_ns: str) -> tuple[list[str], list[str], dict[str, int]]:
    """Problems (each fails the gate), notes and term counts of the package namespace."""
    problems: list[str] = []
    notes: list[str] = []

    def show(term) -> str:
        return term.n3(schema.namespace_manager) if isinstance(term, (URIRef, Literal)) else "an anonymous node"

    def local(term) -> bool:
        return isinstance(term, URIRef) and str(term).startswith(local_ns)

    def typed(owl_type) -> set:
        return {s for s in schema.subjects(RDF.type, owl_type) if isinstance(s, URIRef)}

    classes = typed(OWL.Class)
    kinds = {kind: typed(owl_type) for owl_type, kind in PROPERTY_KINDS.items()}
    properties = set().union(*kinds.values())
    individuals = typed(OWL.NamedIndividual)

    def kind_of(term) -> str | None:
        found = [kind for kind, members in kinds.items() if term in members]
        return found[0] if len(found) == 1 else None

    # ------------------------------------------------------------- declarations
    for p in sorted(set(schema.predicates()), key=str):
        if not builtin(p) and p not in properties:
            problems.append(f"{show(p)} is used as a property but is not declared")

    class_positions = defaultdict(set)            # term -> where it is used as a class
    for s, o in schema.subject_objects(RDFS.subClassOf):
        class_positions[s].add("rdfs:subClassOf")
        class_positions[o].add("rdfs:subClassOf")
    for p in (OWL.equivalentClass, OWL.disjointWith):
        for s, o in schema.subject_objects(p):
            class_positions[s].add(show(p))
            class_positions[o].add(show(p))
    for o in schema.objects(None, RDFS.domain):
        class_positions[o].add("rdfs:domain")
    for s, o in schema.subject_objects(RDFS.range):
        if s not in kinds["datatype property"]:
            class_positions[o].add("rdfs:range")
    for axiom in schema.subjects(RDF.type, OWL.AllDisjointClasses):
        for head in schema.objects(axiom, OWL.members):
            for member in schema.items(head):
                class_positions[member].add("owl:AllDisjointClasses")
    for s, o in schema.subject_objects(RDF.type):
        if not builtin(o):
            class_positions[o].add("rdf:type")
    for term, where in sorted(class_positions.items(), key=lambda kv: str(kv[0])):
        if isinstance(term, BNode):
            problems.append(f"anonymous class in {', '.join(sorted(where))}; the package uses named classes only")
        elif term not in classes and term != OWL.Thing:
            problems.append(f"{show(term)} is used as a class ({', '.join(sorted(where))}) but is not declared")

    # ------------------------------------------------------------------- kinds
    for term in sorted(classes | properties | individuals, key=str):
        roles = [name for name, members in (("class", classes), ("individual", individuals), *kinds.items())
                 if term in members]
        if len(roles) > 1:
            problems.append(f"{show(term)} is declared as {' and '.join(roles)} (punning)")
    for p in (RDFS.subPropertyOf, OWL.equivalentProperty, OWL.inverseOf):
        for s, o in schema.subject_objects(p):
            for term in (s, o):
                if term not in properties:
                    problems.append(f"{show(term)} is used in {show(p)} but is not declared as a property")
            a, b = kind_of(s), kind_of(o)
            if a and b and a != b:
                problems.append(f"{show(s)} ({a}) {show(p)} {show(o)} ({b}): the two must be of the same kind")
            if p == OWL.inverseOf and a and b and (a, b) != ("object property", "object property"):
                problems.append(f"{show(s)} owl:inverseOf {show(o)}: only object properties have inverses")
    for p in (RDFS.domain, RDFS.range):
        for s in set(schema.subjects(p, None)):
            if s not in properties:
                problems.append(f"{show(s)} has an {show(p)} but is not declared as a property")
    for owl_type in sorted(OBJECT_ONLY | NOT_IN_RL | {OWL.FunctionalProperty}, key=str):
        for s in schema.subjects(RDF.type, owl_type):
            if owl_type in NOT_IN_RL:
                problems.append(f"{show(s)} is an {show(owl_type)}, which OWL 2 RL does not have")
            elif owl_type in OBJECT_ONLY and s not in kinds["object property"]:
                problems.append(f"{show(s)} is an {show(owl_type)} but not an object property")
            elif owl_type == OWL.FunctionalProperty and s not in kinds["object property"] | kinds["datatype property"]:
                problems.append(f"{show(s)} is functional but neither an object nor a datatype property")

    # ------------------------------------------------------------- expressions
    for term in ANONYMOUS_CLASS_TERMS:
        if (None, term, None) in schema or (None, RDF.type, term) in schema:
            problems.append(f"{show(term)} is used; the package has no restrictions, unions, enumerations or "
                            f"other anonymous classes (docs/02-conventions.md)")

    # ------------------------------------------------------------------ ranges
    for p in sorted(kinds["datatype property"], key=str):
        for r in schema.objects(p, RDFS.range):
            if r not in RL_DATATYPES:
                problems.append(f"{show(p)} has the range {show(r)}, which is not in the OWL 2 RL datatype map")
    for p in sorted(kinds["object property"], key=str):
        for r in schema.objects(p, RDFS.range):
            if r in RL_DATATYPES or str(r).startswith(str(XSD)):
                problems.append(f"object property {show(p)} has the datatype {show(r)} as range")

    # ---------------------------------------------------------------- literals
    for s, p, o in schema:
        if isinstance(o, Literal) and o.ill_typed:
            problems.append(f"{show(s)} {show(p)}: ill-typed literal {show(o)}")

    # --------------------------------------------------------------- hierarchy
    for predicate, what in ((RDFS.subClassOf, "subclass"), (RDFS.subPropertyOf, "subproperty")):
        parents = defaultdict(set)
        for s, o in schema.subject_objects(predicate):
            if isinstance(s, URIRef) and isinstance(o, URIRef) and s != o:
                parents[s].add(o)
        state: dict = {}

        def visit(node, path) -> None:
            if state.get(node) == 1:
                problems.append(f"{what} cycle: " + " -> ".join(show(n) for n in path[path.index(node):] + [node]))
                return
            if state.get(node) == 2:
                return
            state[node] = 1
            for parent in sorted(parents.get(node, ()), key=str):
                visit(parent, path + [node])
            state[node] = 2

        for node in sorted(parents, key=str):
            visit(node, [])
        if predicate == RDFS.subClassOf:
            class_parents = parents

    def ancestors(cls) -> set:
        seen, todo = set(), [cls]
        while todo:
            node = todo.pop()
            if node not in seen:
                seen.add(node)
                todo.extend(class_parents.get(node, ()))
        return seen

    disjoint = {frozenset((a, b)) for a, b in schema.subject_objects(OWL.disjointWith)}
    for axiom in schema.subjects(RDF.type, OWL.AllDisjointClasses):
        for head in schema.objects(axiom, OWL.members):
            members = list(schema.items(head))
            disjoint |= {frozenset((a, b)) for a in members for b in members if a != b}
    for cls in sorted(classes, key=str):
        up = ancestors(cls)
        for pair in disjoint:
            if len(pair) == 2 and pair <= up:
                a, b = sorted(pair, key=str)
                problems.append(f"{show(cls)} is unsatisfiable: it is under the disjoint classes {show(a)} and {show(b)}")

    # ----------------------------------------------------------- documentation
    for term in sorted((t for t in classes | properties | individuals if local(t)), key=str):
        labels = list(schema.objects(term, RDFS.label))
        if not labels:
            problems.append(f"{show(term)} has no rdfs:label")
        elif not all(isinstance(lab, Literal) and lab.language for lab in labels):
            problems.append(f"{show(term)} has an rdfs:label without a language tag")
        if (term, SKOS.definition, None) not in schema and (term, RDFS.comment, None) not in schema:
            problems.append(f"{show(term)} has no skos:definition or rdfs:comment")

    external = sorted((t for t in classes | properties if not local(t)), key=str)
    if external:
        notes.append(f"{len(external)} external terms declared")
    problems = list(dict.fromkeys(problems))       # one line per finding, in the order found
    counts = {"classes": sum(1 for t in classes if local(t)),
              "object properties": sum(1 for t in kinds["object property"] if local(t)),
              "datatype properties": sum(1 for t in kinds["datatype property"] if local(t)),
              "individuals": sum(1 for t in individuals if local(t)),
              "external declarations": len(external)}
    return problems, notes, counts


def range_conflicts(schema: Graph, data: Graph, limit: int = 0) -> list[str]:
    """Literals whose datatype is outside the declared range of their datatype property.

    Under OWL semantics such a literal makes the graph inconsistent, and the OWL 2 RL
    rule set does not report it; a language-tagged literal on a property with the range
    xsd:string is the usual case. Properties with the range rdfs:Literal admit every
    literal and are checked by the shapes instead.
    """
    integers = {XSD.integer, XSD.nonNegativeInteger, XSD.nonPositiveInteger, XSD.positiveInteger,
                XSD.negativeInteger, XSD.long, XSD.int, XSD.short, XSD.byte, XSD.unsignedLong, XSD.unsignedInt,
                XSD.unsignedShort, XSD.unsignedByte}
    admits = {XSD.decimal: {XSD.decimal} | integers, XSD.integer: integers,
              XSD.string: {XSD.string, XSD.normalizedString, XSD.token, XSD.language, XSD.Name, XSD.NCName,
                           XSD.NMTOKEN},
              XSD.dateTime: {XSD.dateTime, XSD.dateTimeStamp}}
    conflicts: list[str] = []
    for p in sorted(schema.subjects(RDF.type, OWL.DatatypeProperty), key=str):
        ranges = [r for r in schema.objects(p, RDFS.range) if r != RDFS.Literal and isinstance(r, URIRef)]
        for r in ranges:
            for s, o in data.subject_objects(p):
                if isinstance(o, Literal):
                    actual = o.datatype or (RDF.langString if o.language else XSD.string)
                    if actual in admits.get(r, {r}):
                        continue
                    found = f"{o.n3(data.namespace_manager)[:60]} ({actual.n3(schema.namespace_manager)})"
                else:
                    found = "a resource"
                conflicts.append(f"{s.n3(data.namespace_manager)} {p.n3(schema.namespace_manager)}: {found} is "
                                 f"outside the range {r.n3(schema.namespace_manager)}")
                if limit and len(conflicts) >= limit:
                    return conflicts
    return conflicts
