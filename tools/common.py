"""Shared constants and loaders for the MAESTRO tools.

The tools run on this package alone and need rdflib, pyshacl and owlrl. Two
checks read material that is not part of the package and say so when it is
absent: the pinned copies of the external vocabularies (``references/``) and
the MAESTRO 1.0 sources (``ontologies/``), both looked up next to the package
folder, where they sit when the package is checked out inside the MAESTRO 1.0
repository. Everything here is import-safe: no file is written and no gate
runs at import time.
"""

from __future__ import annotations

import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF

# Windows consoles default to cp1252; labels such as "°C" would raise.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover - non-console streams
    pass

PKG = Path(__file__).resolve().parents[1]          # package root
REPO = PKG.parent                                  # MAESTRO 1.0 repository root, when the package sits inside it
REFERENCES = REPO / "references"                   # pinned copies of the external vocabularies (optional)
MAESTRO_1_0_STACK = REPO / "ontologies"            # MAESTRO 1.0 sources (optional)

MH_NS = "https://w3id.org/maestro#"
MH = Namespace(MH_NS)
HHM = Namespace("https://w3id.org/hhm-core#")
MHSH = Namespace("https://w3id.org/maestro/shapes#")
MAESTRO_1_0 = "https://w3id.org/maestro/"
ONTOLOGY_IRI = URIRef("https://w3id.org/maestro")
MODULE_BASE = "https://w3id.org/maestro/"

# Folder of each layer under the package root. A use case keeps the short layer
# names for its own subfolders (<unit>/core/, <unit>/ext/).
LAYER_DIRS = {"core": "core", "ext": "experimental-extensions"}

# Load order: dependencies first. Each entry is (layer, file stem).
MODULES: list[tuple[str, str]] = [
    ("core", "resource"),
    ("core", "skill"),
    ("core", "recipe"),
    ("core", "product"),
    ("core", "invocation"),
    ("core", "policy"),
    ("core", "execution"),
    ("core", "maas"),
    ("ext", "runtime"),
    ("ext", "energy"),
    ("ext", "maintenance"),
    ("ext", "digital-twin"),
    ("ext", "opcua"),
    ("ext", "isa88"),
    ("ext", "isa95"),
    ("ext", "automationml"),
    ("ext", "dtdl"),
    ("ext", "rest"),
    ("ext", "prov"),
    ("ext", "odrl"),
]
UMBRELLA_FILE = PKG / "maestro.ttl"
MERGED_FILE = PKG / "maestro-merged.ttl"
# The module that declares the kind of the external terms the package uses (gate 3).
SIGNATURE_MODULE = "resource"


def layer_dir(layer: str) -> str:
    return LAYER_DIRS.get(layer, layer)


def module_path(layer: str, stem: str) -> Path:
    return PKG / layer_dir(layer) / f"{stem}.ttl"


def module_iri(stem: str) -> URIRef:
    return URIRef(MODULE_BASE + stem)


def module_files() -> list[Path]:
    return [module_path(layer, stem) for layer, stem in MODULES]


def alignment_files() -> list[Path]:
    return sorted((PKG / "alignment").glob("*.ttl"))


def shape_files() -> list[Path]:
    return sorted((PKG / "shacl").glob("*.ttl"))


def example_files() -> list[Path]:
    """Umbrella and module files of every use case; the generated *-merged.ttl copies are left out."""
    return [p for p in sorted((PKG / "usecase-knowledge-graphs").glob("**/*.ttl"))
            if not p.name.endswith("-merged.ttl")]


def query_files() -> list[Path]:
    return sorted((PKG / "queries").glob("**/*.rq"))


def fixture_files() -> list[Path]:
    """Synthetic acceptance data of the competency questions; never loaded with the use-case graphs."""
    return sorted((PKG / "queries" / "fixtures").glob("**/*.ttl"))


def probe_files() -> list[Path]:
    """Synthetic graphs that test the shapes themselves (shacl/probes/README.md)."""
    return sorted((PKG / "shacl" / "probes").glob("*.ttl"))


def new_graph() -> Graph:
    """A graph that binds only the core prefixes, so serialisations stay small."""
    g = Graph(bind_namespaces="core")
    g.bind("maestro", MH)
    return g


def parse(path: Path) -> Graph:
    g = new_graph()
    g.parse(path, format="turtle")
    return g


def load(paths) -> Graph:
    g = new_graph()
    for p in paths:
        g.parse(p, format="turtle")
    return g


def load_modules() -> Graph:
    return load(module_files())


def ontology_of(g: Graph) -> URIRef | None:
    """The single owl:Ontology subject of a module file."""
    subjects = [s for s in g.subjects(RDF.type, OWL.Ontology) if isinstance(s, URIRef)]
    return subjects[0] if len(subjects) == 1 else None


def deprecated_equivalents(schema: Graph) -> dict[URIRef, URIRef]:
    """Deprecated 0.1.0 name -> the term that replaced it (owl:equivalentClass / owl:equivalentProperty)."""
    names: dict[URIRef, URIRef] = {}
    for old in schema.subjects(OWL.deprecated, Literal(True)):
        for p in (OWL.equivalentClass, OWL.equivalentProperty):
            for new in schema.objects(old, p):
                if isinstance(old, URIRef) and isinstance(new, URIRef):
                    names[old] = new
    return names


def with_current_names(data: Graph, schema: Graph) -> Graph:
    """Copy of ``data`` that also states, under its 0.2.0 name, everything stated with a deprecated name.

    The deprecated names are OWL equivalents of the terms that replaced them. RDFS inference
    does not follow owl:equivalentProperty / owl:equivalentClass, so the shapes, which are
    written against the 0.2.0 names, would not see data written against 0.1.0.
    """
    names = deprecated_equivalents(schema)
    out = new_graph()
    for prefix, ns in data.namespaces():
        out.bind(prefix, ns, override=False)
    out += data
    for s, p, o in data:
        if p in names:
            out.add((s, names[p], o))
        if p == RDF.type and o in names:
            out.add((s, p, names[o]))
    return out


def rel(path: Path) -> str:
    try:
        return path.relative_to(PKG).as_posix()
    except ValueError:                             # a file outside the package (references/, MAESTRO 1.0)
        return path.as_posix()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")
