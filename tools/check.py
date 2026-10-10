"""Check a MAESTRO HHM-Core knowledge graph and run SPARQL queries over it.

    python tools/check.py my-data.ttl                       # SHACL check of one file
    python tools/check.py examples/widget-cell              # every .ttl in a folder
    python tools/check.py my-data.ttl --query queries/cq/cq01-station-modules-capabilities.rq
    python tools/check.py my-data.ttl --query q1.rq --query q2.rq --no-shacl

The data is loaded together with the merged ontology (dist/maestro-hhm-core-full.ttl)
and checked against every shape in shapes/. Violations make the script exit with 1;
warnings are printed but do not fail. Needs: pip install rdflib pyshacl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SH

ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY = ROOT / "dist" / "maestro-hhm-core-full.ttl"
SHAPES = ROOT / "shapes"


def short(node, g: Graph) -> str:
    if node is None:
        return "-"
    if isinstance(node, Literal):
        return str(node)
    if isinstance(node, URIRef):
        try:
            return g.namespace_manager.normalizeUri(node)
        except Exception:  # noqa: BLE001
            return str(node)
    return str(node)


def data_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(p.rglob("*.ttl"))
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"not found: {p}")
    if not files:
        sys.exit("no .ttl files given")
    return files


def run_shacl(g: Graph) -> bool:
    import pyshacl

    shapes = Graph()
    for f in sorted(SHAPES.glob("*.ttl")):
        shapes.parse(f, format="turtle")
    _, results, _ = pyshacl.validate(data_graph=g, shacl_graph=shapes, inference="rdfs",
                                     abort_on_first=False, meta_shacl=False, advanced=True)
    violations = warnings = 0
    for r in results.subjects(RDF.type, SH.ValidationResult):
        sev = results.value(r, SH.resultSeverity) or SH.Violation
        focus = results.value(r, SH.focusNode)
        path = results.value(r, SH.resultPath)
        msg = results.value(r, SH.resultMessage) or ""
        label = str(sev).rsplit("#", 1)[-1]
        print(f"  [{label}] {short(focus, g)}  {short(path, g) if path else ''}  {msg}")
        if sev == SH.Violation:
            violations += 1
        else:
            warnings += 1
    print(f"SHACL: {violations} violation(s), {warnings} warning(s)")
    return violations == 0


def run_query(g: Graph, path: Path) -> None:
    result = g.query(path.read_text(encoding="utf-8"))
    rows = list(result)
    print(f"\n{path.name}: {len(rows)} row(s)")
    if not rows:
        return
    names = [str(v) for v in result.vars]
    table = [[short(row[i], g) for i in range(len(names))] for row in rows]
    widths = [min(60, max(len(n), *(len(r[i]) for r in table))) for i, n in enumerate(names)]
    print("  " + " | ".join(n.ljust(w) for n, w in zip(names, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in table:
        print("  " + " | ".join(c[:w].ljust(w) for c, w in zip(r, widths)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", nargs="+", help=".ttl files or folders with your knowledge graph")
    ap.add_argument("--query", action="append", default=[], help="SPARQL .rq file to run (repeatable)")
    ap.add_argument("--no-shacl", action="store_true", help="skip the SHACL check")
    args = ap.parse_args()

    g = Graph()
    g.parse(ONTOLOGY, format="turtle")
    for f in data_files(args.data):
        g.parse(f, format="turtle")
        print(f"loaded {f}")
    print(f"{len(g)} triples (ontology + data)")

    ok = True
    if not args.no_shacl:
        ok = run_shacl(g)
    for q in args.query:
        run_query(g, Path(q))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
