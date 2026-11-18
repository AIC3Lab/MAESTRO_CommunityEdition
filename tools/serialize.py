"""Deterministic Turtle writer for the merged MAESTRO ontology.

    serialize(graph, ontology_iri, banner) -> str

The document has the ontology header first, then one section per kind of
term (annotation properties, object properties, datatype properties, classes,
individuals) and the blank-node axioms last. Subjects are sorted by IRI inside
a section, predicates follow PREDICATE_ORDER, and objects are sorted by their
Turtle form, so the same graph always gives the same text.

Standalone replacement for the ``serialize`` helper of the MAESTRO 1.0
repository (release/build_release.py); it needs rdflib only.
"""

from __future__ import annotations

import re

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

SCHEMA = Namespace("https://schema.org/")
VANN = Namespace("http://purl.org/vocab/vann/")

RULE = "#" * 72
PN_LOCAL = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")

# Sections in document order: (heading, the owl type that puts a subject there).
SECTIONS = [
    ("Annotation properties", OWL.AnnotationProperty),
    ("Object properties", OWL.ObjectProperty),
    ("Datatype properties", OWL.DatatypeProperty),
    ("Classes", OWL.Class),
    ("Individuals", OWL.NamedIndividual),
]
OTHER_SECTION = "Other statements"

# Predicates of the ontology header, in the order of the module template (docs/02-conventions.md).
HEADER_ORDER = [
    RDF.type, OWL.versionIRI, OWL.versionInfo, OWL.priorVersion, DCTERMS.title, RDFS.label, DCTERMS.description,
    RDFS.comment, DCTERMS.creator, DCTERMS.license, DCTERMS.created, DCTERMS.modified, DCTERMS.source, RDFS.seeAlso,
    DCTERMS.conformsTo, DCTERMS.isPartOf, VANN.preferredNamespacePrefix, VANN.preferredNamespaceUri, OWL.imports,
]

# Predicates of a term, in the order of the term template. A predicate that is not
# listed sorts by its Turtle form between the last listed one and rdfs:isDefinedBy.
PREDICATE_ORDER = [
    RDF.type, RDFS.label, SKOS.prefLabel, SKOS.altLabel, SKOS.definition, RDFS.comment, SKOS.scopeNote,
    OWL.equivalentClass, OWL.equivalentProperty, OWL.deprecated, RDFS.subClassOf, RDFS.subPropertyOf, OWL.inverseOf,
    RDFS.domain, SCHEMA.domainIncludes, RDFS.range, SCHEMA.rangeIncludes, OWL.disjointWith, OWL.propertyDisjointWith,
    SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch,
    DCTERMS.isReplacedBy, DCTERMS.references, DCTERMS.source,
]
LAST_PREDICATE = RDFS.isDefinedBy


class Writer:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.prefixes = {prefix: str(ns) for prefix, ns in graph.namespaces() if prefix and prefix != "xml"}
        self._by_length = sorted(self.prefixes.items(), key=lambda kv: -len(kv[1]))

    # ----------------------------------------------------------------- terms

    def iri(self, node: URIRef) -> str:
        text = str(node)
        for prefix, namespace in self._by_length:
            if text.startswith(namespace) and PN_LOCAL.match(text[len(namespace):]):
                return f"{prefix}:{text[len(namespace):]}"
        return f"<{text}>"

    def literal(self, node: Literal) -> str:
        text = str(node).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
        text = f'"{text.replace(chr(9), chr(92) + "t")}"'
        if node.language:
            return f"{text}@{node.language}"
        if node.datatype is not None:
            return f"{text}^^{self.iri(node.datatype)}"
        return text

    def collection(self, head) -> list | None:
        """Members of the RDF list starting at ``head``, or None if it is not a well-formed list."""
        members, node, seen = [], head, set()
        while node != RDF.nil:
            if node in seen or not isinstance(node, BNode):
                return None
            seen.add(node)
            first = list(self.graph.objects(node, RDF.first))
            rest = list(self.graph.objects(node, RDF.rest))
            if len(first) != 1 or len(rest) != 1 or len(list(self.graph.predicate_objects(node))) != 2:
                return None
            members.append(first[0])
            node = rest[0]
        return members

    def term(self, node) -> str:
        if isinstance(node, Literal):
            return self.literal(node)
        if isinstance(node, URIRef):
            return self.iri(node)
        members = self.collection(node)
        if members is not None:
            return "( " + " ".join(self.term(m) for m in members) + " )"
        return "[ " + " ; ".join(self.statements(node, PREDICATE_ORDER)) + " ]"

    # ----------------------------------------------------------------- blocks

    def statements(self, subject, order: list) -> list[str]:
        """``predicate object , object`` for every predicate of ``subject``, in template order."""
        by_predicate: dict = {}
        for p, o in self.graph.predicate_objects(subject):
            by_predicate.setdefault(p, []).append(o)

        def rank(p):
            if p in order:
                return (0, order.index(p), "")
            if p == LAST_PREDICATE:
                return (2, 0, "")
            return (1, 0, self.iri(p))

        lines = []
        for p in sorted(by_predicate, key=rank):
            name = "a" if p == RDF.type else self.iri(p)
            lines.append(f"{name} " + " , ".join(sorted(self.term(o) for o in by_predicate[p])))
        return lines

    def block(self, subject: URIRef, order: list) -> str:
        return f"{self.iri(subject)} " + " ;\n    ".join(self.statements(subject, order)) + " .\n"


def heading(title: str) -> str:
    return f"{RULE}\n#    {title}\n{RULE}\n"


def serialize(graph: Graph, ontology_iri: URIRef, banner: str = "") -> str:
    """Turtle text of ``graph``; ``banner`` is a leading comment block (lines starting with '#')."""
    writer = Writer(graph)
    parts = []
    if banner:
        parts.append(banner.rstrip("\n") + "\n")
    parts.append("".join(f"@prefix {p}: <{writer.prefixes[p]}> .\n" for p in sorted(writer.prefixes)))
    parts.append(heading("Ontology"))
    parts.append(writer.block(ontology_iri, HEADER_ORDER))

    subjects = {s for s in set(graph.subjects()) if isinstance(s, URIRef) and s != ontology_iri}
    placed: set = set()
    grouped: list[tuple[str, list]] = []
    for title, owl_type in SECTIONS:
        members = sorted((s for s in subjects - placed if (s, RDF.type, owl_type) in graph), key=str)
        placed.update(members)
        grouped.append((title, members))
    grouped.append((OTHER_SECTION, sorted(subjects - placed, key=str)))
    for title, members in grouped:
        if not members:
            continue
        parts.append(heading(title))
        parts.extend(f"###  {s}\n{writer.block(s, PREDICATE_ORDER)}" for s in members)

    # Blank nodes no other statement points to: owl:AllDifferent, owl:AllDisjointClasses and the like.
    roots = [s for s in set(graph.subjects()) if isinstance(s, BNode) and (None, None, s) not in graph]
    axioms = sorted(f"[ {' ; '.join(writer.statements(s, PREDICATE_ORDER))} ] .\n" for s in roots)
    if axioms:
        parts.append(heading("General axioms"))
        parts.extend(axioms)
    return "\n".join(parts)
