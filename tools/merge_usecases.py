"""Merge the module files of every use-case knowledge graph into one document.

A use case under usecase-knowledge-graphs/ is laid out like the ontology itself:

    <unit>/<name>.ttl            umbrella: the owl:Ontology header; imports the module files
    <unit>/core/<module>.ttl     statements that belong to the MAESTRO core module of that name
    <unit>/ext/<module>.ttl      statements that belong to the extension module of that name
    <unit>/<name>-merged.ttl     written here: umbrella and module files in one document

Where a statement goes:

  * ``s a C`` goes to the module that defines the class C;
  * a statement whose property is defined in an extension module goes to that module;
  * every other statement stays with its subject, in the module of the subject's class
    (the first one in load order if the subject has classes from several modules).

Individuals without a MAESTRO class (SKOS collections, PROV evidence records) are not
checked; they sit next to the individuals they describe.

Load either every Turtle file except ``*-merged.ttl`` or only the ``*-merged.ttl`` files;
both give the same statements apart from the per-file ontology headers.

    python tools/merge_usecases.py            write every <name>-merged.ttl
    python tools/merge_usecases.py --check    fail if a merged file is stale, an umbrella does not
                                              import its module files, or a statement sits in the
                                              wrong module file
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from common import MH_NS, MODULE_BASE, MODULES, PKG, module_path, read_text, write_text

KG = PKG / "usecase-knowledge-graphs"
MERGED_SUFFIX = "-merged.ttl"
MERGED_NOTE = " This file is the merged form of all module files of this use case in one document."
RULE = "#" * 65
MODULE_KEYS = [f"{layer}/{stem}" for layer, stem in MODULES]

# The prefixes below are declared first, in this order; the rest follow alphabetically.
STANDARD_PREFIXES = ["rdf", "rdfs", "owl", "xsd", "skos", "dct", "prov", "maestro"]


# ---------------------------------------------------------------- MAESTRO modules

def load_tbox() -> tuple[dict, dict]:
    """(term -> 'core/skill', term -> position in its module file) for every MAESTRO term."""
    term_module, term_order = {}, {}
    for key, (layer, stem) in zip(MODULE_KEYS, MODULES):
        path = module_path(layer, stem)
        for s in set(Graph().parse(path, format="turtle").subjects()):
            if isinstance(s, URIRef) and str(s).startswith(MH_NS):
                term_module.setdefault(s, key)
        for n, m in enumerate(re.finditer(r"^maestro:([A-Za-z0-9_\-]+)\s", read_text(path), re.M)):
            term_order.setdefault(URIRef(MH_NS + m.group(1)), n)
    return term_module, term_order


def home_module(types, term_module) -> str | None:
    """Module of an individual: that of its class, core modules before extensions."""
    keys = {term_module[t] for t in types if t in term_module}
    return min(keys, key=MODULE_KEYS.index) if keys else None


def statement_module(s, p, o, home, term_module) -> str | None:
    """Module file a statement belongs to; ``home`` is the subject's home module."""
    if p == RDF.type and o in term_module:
        return term_module[o]
    if term_module.get(p, "").startswith("ext/"):
        return term_module[p]
    return home


# ---------------------------------------------------------------- Turtle writer

PN_LOCAL = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-]*$")
PLAIN = {
    XSD.integer: re.compile(r"^[+-]?[0-9]+$"),
    XSD.decimal: re.compile(r"^[+-]?[0-9]*\.[0-9]+$"),
    XSD.double: re.compile(r"^[+-]?([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)[eE][+-]?[0-9]+$"),
    XSD.boolean: re.compile(r"^(true|false)$"),
}


class Turtle:
    """Deterministic Turtle text: sorted subjects, predicates and objects; used prefixes only."""

    def __init__(self, prefixes: dict[str, str]):
        self.prefixes = dict(prefixes)                                  # prefix -> namespace
        self._by_length = sorted(prefixes.items(), key=lambda kv: -len(kv[1]))
        self.used: set[str] = set()

    def iri(self, node) -> str:
        text = str(node)
        for prefix, namespace in self._by_length:
            if text.startswith(namespace) and PN_LOCAL.match(text[len(namespace):]):
                self.used.add(prefix)
                return f"{prefix}:{text[len(namespace):]}"
        return f"<{text}>"

    def term(self, node) -> str:
        if not isinstance(node, Literal):
            return self.iri(node)
        text = str(node)
        if "\n" in text:
            quoted = '"""' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r") + '"""'
        else:
            quoted = '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\t", "\\t") + '"'
        if node.language:
            return f"{quoted}@{node.language}"
        if node.datatype is None:
            return quoted
        if node.datatype in PLAIN and PLAIN[node.datatype].match(text):
            return text
        return f"{quoted}^^{self.iri(node.datatype)}"

    def block(self, graph: Graph, subject) -> str:
        """One subject with all its statements in ``graph``."""
        by_predicate: dict = {}
        for p, o in graph.predicate_objects(subject):
            by_predicate.setdefault(p, []).append(o)
        order = sorted(by_predicate, key=lambda p: (p != RDF.type, p != RDFS.label, str(p)))
        lines = []
        for p in order:
            objects = sorted(by_predicate[p], key=lambda o: (isinstance(o, Literal), str(o)))
            name = "a" if p == RDF.type else self.iri(p)
            terms = [self.term(o) for o in objects]
            inline = f"{name} {', '.join(terms)}"
            if len(terms) > 1 and len(inline) > 96:
                inline = f"{name} " + ",\n        ".join(terms)
            lines.append(inline)
        head = self.iri(subject)
        if order[0] == RDF.type:                                        # "s a C ;" on the first line
            return f"{head} {lines[0]}" + "".join(f" ;\n    {line}" for line in lines[1:]) + " .\n"
        return f"{head}\n    " + " ;\n    ".join(lines) + " .\n"

    def prefix_lines(self) -> str:
        names = [p for p in STANDARD_PREFIXES if p in self.used]
        names += sorted(self.used - set(STANDARD_PREFIXES))
        return "".join(f"@prefix {p}: <{self.prefixes[p]}> .\n" for p in names)


def banner(*lines: str) -> str:
    return "\n".join([RULE, *[f"# {line}".rstrip() for line in lines], RULE]) + "\n"


def sections(graph: Graph, module: str, skip, term_module, term_order, turtle: Turtle) -> list[tuple[str, list]]:
    """Subjects of one module file grouped by class: [(heading, [subject, ...]), ...]."""
    groups: dict = {}
    for s in set(graph.subjects()):
        if s in skip:
            continue
        types = list(graph.objects(s, RDF.type))
        own = sorted((t for t in types if term_module.get(t) == module), key=lambda t: term_order.get(t, 10**6))
        other = sorted((t for t in types if t not in term_module), key=str)
        if own:
            key = (0, term_order.get(own[0], 10**6), turtle.iri(own[0]))
        elif other:
            key = (1, 0, turtle.iri(other[0]))
        else:
            key = (2, 0, "Further statements about individuals described in other files")
        groups.setdefault(key, []).append(s)
    return [(key[2], sorted(groups[key], key=str)) for key in sorted(groups)]


def document(comment: list[str], turtle: Turtle, body: str) -> str:
    """Leading comment, the prefixes ``body`` used, then ``body``."""
    head = "".join(f"# {line}".rstrip() + "\n" for line in comment)
    return f"{head}\n{turtle.prefix_lines()}\n{body}".rstrip("\n") + "\n"


def module_body(graph: Graph, module: str, header, term_module, term_order, turtle: Turtle,
                with_headings: bool = True) -> str:
    """The statements of one module file, without its ontology header, grouped by class."""
    parts = []
    for heading, subjects in sections(graph, module, {header}, term_module, term_order, turtle):
        if with_headings:
            parts.append(banner(f"{heading} ({len(subjects)})"))
        parts.extend(turtle.block(graph, s) for s in subjects)
    return "\n".join(parts)


# ---------------------------------------------------------------- use-case units

def parse(path: Path) -> Graph:
    graph = Graph(bind_namespaces="none")
    graph.parse(path, format="turtle")
    return graph


def is_merged(path: Path) -> bool:
    return path.name.endswith(MERGED_SUFFIX)


def source_files(root: Path = KG) -> list[Path]:
    """Every use-case Turtle file except the generated merged ones."""
    return [p for p in sorted(root.rglob("*.ttl")) if not is_merged(p)]


def units() -> list[Path]:
    """Folders with a core/ or ext/ subfolder."""
    return sorted({p.parent for p in KG.rglob("*") if p.is_dir() and p.name in ("core", "ext")})


def umbrella_file(unit: Path) -> Path:
    files = [p for p in sorted(unit.glob("*.ttl")) if not is_merged(p)]
    if len(files) != 1:
        raise SystemExit(f"{unit.relative_to(PKG)}: expected one umbrella Turtle file, found {len(files)}")
    return files[0]


def module_files(unit: Path) -> list[tuple[str, Path]]:
    found = {f"{p.parent.name}/{p.stem}": p for layer in ("core", "ext") for p in (unit / layer).glob("*.ttl")}
    unknown = sorted(set(found) - set(MODULE_KEYS))
    if unknown:
        raise SystemExit(f"{unit.relative_to(PKG)}: no MAESTRO module named {', '.join(unknown)}")
    return [(key, found[key]) for key in MODULE_KEYS if key in found]


def ontology_iri(graph: Graph, path: Path) -> URIRef:
    subjects = sorted(s for s in graph.subjects(RDF.type, OWL.Ontology) if isinstance(s, URIRef))
    if len(subjects) != 1:
        raise SystemExit(f"{path.relative_to(PKG)}: expected one owl:Ontology header, found {len(subjects)}")
    return subjects[0]


def merged_text(unit: Path, term_module, term_order) -> str:
    umbrella_path = umbrella_file(unit)
    umbrella = parse(umbrella_path)
    iri = ontology_iri(umbrella, umbrella_path)
    modules = [(key, path, parse(path)) for key, path in module_files(unit)]
    prefixes = {}
    for graph in [umbrella] + [g for _, _, g in modules]:
        for prefix, namespace in graph.namespaces():
            prefixes.setdefault(prefix, str(namespace))
    turtle = Turtle(prefixes)

    header = Graph(bind_namespaces="none")
    own = tuple(f"{iri}/{layer}/" for layer in ("core", "ext"))
    for s, p, o in umbrella:
        if not (s == iri and p == OWL.imports and str(o).startswith(own)):
            header.add((s, p, o))
    comment = header.value(iri, RDFS.comment)
    if comment is not None:
        header.set((iri, RDFS.comment, Literal(str(comment) + MERGED_NOTE, lang=comment.language)))
    parts = [turtle.block(header, iri)]
    parts += [turtle.block(header, s) for s in sorted(set(header.subjects()) - {iri}, key=str)]
    for key, path, graph in modules:
        parts.append(banner(f"{key}.ttl"))
        parts.append(module_body(graph, key, ontology_iri(graph, path), term_module, term_order, turtle,
                                 with_headings=False))
    label = umbrella.value(iri, RDFS.label) or unit.name
    version = umbrella.value(iri, OWL.versionInfo)
    comment_lines = [f"{label} (merged, all module files)",
                     f"{iri}" + (f"  (version {version})" if version else ""),
                     f"Generated by tools/merge_usecases.py from {umbrella_path.name}, core/ and ext/ - do not edit."]
    return document(comment_lines, turtle, "\n".join(parts))


def merged_path(unit: Path) -> Path:
    return unit / (umbrella_file(unit).stem + MERGED_SUFFIX)


def placement_errors(term_module) -> list[str]:
    """Statements that sit in another module file than the rule in the module docstring says."""
    files = {path: parse(path) for path in source_files()}
    types: dict = {}
    for graph in files.values():
        for s, o in graph.subject_objects(RDF.type):
            types.setdefault(s, set()).add(o)
    errors = []
    for unit in units():
        for key, path in module_files(unit):
            for s, p, o in files[path]:
                home = home_module(types.get(s, ()), term_module)
                want = statement_module(s, p, o, home, term_module)
                if want is not None and want != key:
                    errors.append(f"{path.relative_to(PKG)}: {s} {p} belongs in {want}.ttl")
    return sorted(errors)


def import_errors(unit: Path) -> list[str]:
    path = umbrella_file(unit)
    graph = parse(path)
    iri = ontology_iri(graph, path)
    want = {URIRef(f"{iri}/{key}") for key, _ in module_files(unit)}
    have = {o for o in graph.objects(iri, OWL.imports) if str(o).startswith((f"{iri}/core/", f"{iri}/ext/"))}
    errors = [f"{path.relative_to(PKG)}: does not import {o}" for o in sorted(want - have)]
    errors += [f"{path.relative_to(PKG)}: imports {o}, which has no module file" for o in sorted(have - want)]
    for key, module in module_files(unit):
        module_iri = ontology_iri(parse(module), module)
        if module_iri != URIRef(f"{iri}/{key}"):
            errors.append(f"{module.relative_to(PKG)}: ontology IRI should be {iri}/{key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="verify instead of writing")
    args = parser.parse_args()
    term_module, term_order = load_tbox()
    errors = []
    for unit in units():
        text, path = merged_text(unit, term_module, term_order), merged_path(unit)
        triples = len(Graph().parse(data=text, format="turtle"))
        if not args.check:
            write_text(path, text)
            print(f"wrote {path.relative_to(PKG)}  ({triples} triples, {len(module_files(unit))} module files)")
        elif not path.exists() or read_text(path) != text:
            errors.append(f"{path.relative_to(PKG)}: stale, run tools/merge_usecases.py")
        errors += import_errors(unit)
    if args.check:
        errors += placement_errors(term_module)
        for error in errors:
            print("FAIL", error)
        print(f"{len(units())} use-case units checked: " + ("OK" if not errors else f"{len(errors)} problem(s)"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
