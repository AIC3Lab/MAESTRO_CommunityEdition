# Use-case knowledge graphs

Instance data (A-box) for MAESTRO. Every use case is laid out like the ontology itself:
one Turtle file per MAESTRO module it uses, under `core/` and `ext/`, an umbrella file
that imports them, and one merged file with everything.

```
<use case>/
  <name>.ttl            umbrella: the owl:Ontology header (label, sources, version); imports the module files
  core/                 one file per MAESTRO core module the use case uses
    resource.ttl          stations, modules, capabilities
    skill.ttl             skills, parameters (signals, data points), conditions, values
    recipe.ttl            recipes, plan steps, control flow, data bindings
    product.ttl           product types, features, requirements, identifiers, BOM items, materials
    invocation.ttl        endpoints, services, protocols, data formats
    policy.ttl            policies, constraints, roles, hazards, risks, mitigations
    maas.ttl              provider / operator profile
  ext/                  one file per MAESTRO extension module the use case uses
    isa95.ttl             enterprise, site, area, work center, work unit
    automationml.ttl      interfaces and the links between them
    dtdl.ttl  energy.ttl  maintenance.ttl  runtime.ttl  prov.ttl  ...
  <name>-merged.ttl     generated: umbrella and all module files in one document
```

| Use case set | Units (one `core/` + `ext/` + merged set each) |
|---|---|
| [`ltu-festo-mps/`](ltu-festo-mps/README.md) | `distributing/`, `testing/`, `processing/`, `handling/`, `line/`, `shared/` |

A module file exists only where the use case has statements for that module.

## Where a statement goes

- `s a C` goes to the file of the module that defines the class `C`. An individual with a
  core class and an extension class is in both files: `han:Station a maestro:Station` in
  `core/resource.ttl`, `han:Station a maestro:WorkUnit` in `ext/isa95.ttl`.
- A statement whose property is defined in an extension module goes to that extension
  file (`maestro:partOfWorkCenter` to `ext/isa95.ttl`, `maestro:hasInterface` to
  `ext/automationml.ttl`).
- Every other statement stays with its subject, in the file of the subject's class: label,
  description, evidence links and all core properties.
- Individuals without a MAESTRO class sit next to what they describe: SKOS collections of
  parameters and the value classification in `core/skill.ttl`, equipment specification
  catalogues in `core/resource.ttl`, PROV evidence records and reified mapping statements
  in `ext/prov.ttl`.

Each module file has its own `owl:Ontology` header, `<use case IRI>/core/<module>` or
`<use case IRI>/ext/<module>`, with `dct:isPartOf` the use case and `owl:imports` the
MAESTRO module of the same name. Individuals keep their IRIs; only the files changed.

## Loading

Load `maestro-merged.ttl` from the repository root and then either

- every `*-merged.ttl` file (one per unit), or
- every Turtle file except `*-merged.ttl`.

Both give the same statements apart from the per-file ontology headers. Do not hand-edit a
`*-merged.ttl` file: edit the files under `core/` and `ext/` and run

```bash
python tools/merge_usecases.py            # rewrite every <name>-merged.ttl
python tools/merge_usecases.py --check    # stale merged file, missing import or misplaced statement -> exit 1
```
