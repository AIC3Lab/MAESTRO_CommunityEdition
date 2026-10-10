# 02 - Conventions

Rules every file under `maestro-hhm-core/` follows. `tools/validate.py` checks most of
them (the gate number is given where one applies).

## Module header

Every module file declares one `owl:Ontology` with this header. Compared with the
MAESTRO 1.0 header (`ontologies/logical/skill.ttl`) it drops `owl:priorVersion`,
`vs:term_status` and `core:changeRecord` and adds the `vann:` prefix pair.

```turtle
<https://w3id.org/maestro/hhm/skill> a owl:Ontology ;
    owl:versionIRI <https://w3id.org/maestro/hhm/skill/0.1.0> ;
    owl:versionInfo "0.1.0" ;
    dct:title "MAESTRO HHM-Core: Skills" ;
    rdfs:label "MAESTRO HHM-Core: Skills"@en ;
    dct:description "HHM-Core v1 Skills cluster: atomic and composite skills, typed parameters, pre- and postconditions and the protocol-neutral skill interface."@en ;
    rdfs:comment "Skills are logical specifications; execution technologies implement them. MAESTRO-local vocabulary; it is not aligned with, and makes no conformance claim to, any external standard. Definitions are reused from the MAESTRO 1.0 skill and core modules; dct:source names the term a definition was taken from."@en ;
    dct:creator "Melwin Xavier" ;
    dct:license <https://opensource.org/licenses/MIT> ;
    dct:created "2026-09-30"^^xsd:date ;
    dct:modified "2026-09-30"^^xsd:date ;
    dct:source <https://github.com/melwinxavier/MAESTRO> ;
    rdfs:seeAlso <https://w3id.org/maestro/skill> , <https://w3id.org/maestro/core> ;
    dct:conformsTo <https://www.w3.org/TR/owl2-profiles/#OWL_2_RL> ;
    dct:isPartOf <https://w3id.org/maestro/hhm> ;
    vann:preferredNamespacePrefix "maestro" ;
    vann:preferredNamespaceUri "https://w3id.org/maestro#"^^xsd:anyURI ;
    owl:imports <https://w3id.org/maestro/hhm/resource> .
```

Rules:

- Module IRI `https://w3id.org/maestro/hhm/<module>`, version IRI `<module IRI>/<version>`,
  `owl:versionInfo` equal to the umbrella. `build.py` fails on drift; `--set-version`
  is the only way to bump.
- `rdfs:comment` on the header states the standards position of the module in one of
  two forms: "MAESTRO-local vocabulary; it is not aligned with, and makes no
  conformance claim to, any external standard", or "Apart from <documentary links to
  the pinned pattern>, this module is MAESTRO-local vocabulary and makes no conformance
  claim to any external standard".
- `rdfs:seeAlso` names the MAESTRO 1.0 modules the definitions come from, or the pinned
  upstream repository for a bridge file.
- `owl:imports` lists package modules only (gate 2). The umbrella imports exactly the
  `MODULES` list of `tools/common.py`; the alignment files import the umbrella.
- A comment block above the header (Turtle `#` lines) states the HHM cluster or
  extension point the file realises and names the hooks it does not realise.

## Term template

```turtle
maestro:ParameterDef a owl:Class ;
    rdfs:label "Parameter definition"@en ;
    skos:definition "Typed parameter definition of a skill: a data type, an optional unit reference and an optional numeric range."@en ;
    rdfs:comment "HHM-Core Skills cluster (ParameterDef: type, unitRef, range). Also used as the parameter and return schema of an maestro:OperationSignature."@en ;
    dct:source <https://w3id.org/maestro/skill#ParameterDef> ;
    rdfs:isDefinedBy <https://w3id.org/maestro/hhm/skill> .
```

Properties add `rdfs:domain` and `rdfs:range` where a single class applies; individuals
are declared `a owl:NamedIndividual , maestro:<Class>` and carry the same annotations (see
`maestro:SIL1` in `core/policy.ttl`). Every term has:

- `rdfs:label` with language tag `@en` (gate 5);
- `skos:definition` (or, where a definition would only repeat the label, `rdfs:comment`)
  with `@en` (gate 5);
- `rdfs:comment` where the HHM cluster or edge is named, a domain or range was left
  open, or a design difference to MAESTRO 1.0 or to a matched standard needs stating;
- `dct:source` or `dct:references` when a MAESTRO 1.0 counterpart exists (see below);
- `rdfs:isDefinedBy <module IRI>` (gate 3).

No `vs:term_status`, no `core:changeRecord`: the package has one version and no change
record system.

## Single namespace

Every term is in `https://w3id.org/maestro#` (gate 3). Modules do not have their own
namespaces; the module is recorded on the term through `rdfs:isDefinedBy`, and the
prefix `maestro:` is the same in every file. A local name may be declared in one module file
only (gate 4). Shapes use `mhsh:` = `https://w3id.org/maestro/hhm/shapes#`; the example
uses `ex:` = `https://w3id.org/maestro/hhm/examples/widget-cell#`.

## `rdfs:isDefinedBy`

`rdfs:isDefinedBy` on a term equals the ontology IRI of the file that declares it, and
nothing else. A term that is only mentioned in another file (for example `maestro:Recipe`
inside `ext/isa88.ttl`, or `maestro:ExecutionStatus` inside `modules/telemetry.ttl`) does not
get a second `rdfs:isDefinedBy` there, and its declaration (`a owl:Class`) is not
repeated.

## `dct:source` versus `dct:references`

Both point at the MAESTRO 1.0 term IRI (`https://w3id.org/maestro/<module>#<Term>`).

- `dct:source`: the definition text is reused as is and the concept is the same.
  `gen_alignment.py` turns it into `skos:exactMatch` in `alignment/maestro-1.0.ttl`.
  Example: `maestro:hasParameterDef dct:source <https://w3id.org/maestro/skill#hasParameterDef>`.
- `dct:references`: the definition was adapted or the concept was narrowed or renamed.
  It becomes `skos:closeMatch`. Examples: `maestro:Fault dct:references
  <https://w3id.org/maestro/runtime#FaultEvent>` (MAESTRO 1.0 uses `Fault` for the
  faulted state value and `FaultEvent` for the occurrence), `maestro:mayRaise
  dct:references <https://w3id.org/maestro/runtime#raisedFault>`, `maestro:unitRef
  dct:references <https://w3id.org/maestro/skill#unitRef>` (object property there,
  datatype property here).
- Neither: the term has no MAESTRO 1.0 counterpart (`maestro:location`, `maestro:relatedStep`,
  `maestro:bindsFrom`, `maestro:bindsTo`, `maestro:DigitalTwin`, `maestro:TwinBinding`, `maestro:OpcUaBinding`,
  `maestro:diagnosesFault`, `maestro:hostedOn`, `maestro:bindsMethod`).

A term never carries both. `gen_alignment.py` asserts that every target exists in
`ontologies/**`.

## Label style

Labels are sentence case: first word capitalised, the rest lower case (`"Parameter
definition"`, `"has module"`, `"energy (kWh)"`). Proper names and acronyms keep their
capitals (`"OPC UA server"`, `"Protocol Buffers"`, `"SIL 1"`, `"DTDL interface"`).
Property labels are the property name split into words. Class local names are
UpperCamelCase, property and datatype local names lowerCamelCase, individual local
names UpperCamelCase (`maestro:ElectricalGrid`, `maestro:OperationalDimension`).

## OWL 2 RL: do and do not

Do:

- Declare disjointness with `owl:disjointWith` between two named classes only:
  `AtomicSkill` / `CompositeSkill`, `Recipe` / `PlanStep`, `ProductInstance` /
  `ProductType`.
- Model controlled vocabularies as named individuals of a class (`Mode`, `Protocol`,
  `DataFormat`, `InterfaceDescriptionLanguage`, `ExecutionStatus`, `State`,
  `StateDimension`, `RiskLevel`, `SafetyIntegrityLevel`, `PerformanceLevel`,
  `EnergySource`, `ReturnToServiceOutcome`, `ControlFlowType`, `ParameterDirection`,
  `Action`, and the three market roles as `Role` individuals). Individuals that name a
  technology (`Protocol`, `DataFormat`, `InterfaceDescriptionLanguage`) are declared in
  an `ext/` module, not in the core; the umbrella holds their `owl:AllDifferent`.
- Give numeric datatype properties the range `rdfs:Literal` and check the datatype in
  SHACL with `sh:or (xsd:decimal xsd:integer xsd:double xsd:float)` (MAESTRO ADR-0007).
  At 0.1.0: `minValue`, `maxValue`, `energyKwh`, `powerWatts`, `mtbfHours`,
  `remainingUsefulLifeHours`. Money and counts with a fixed type keep it
  (`price xsd:decimal`, `quantity`, `stepOrder`).
- Use `xsd:dateTime` for every time-valued datatype property (`startTime`, `endTime`,
  `timestamp`, `validFrom`, `validTo`, `observedAt`, `recordedAt`, `snapshotTaken`,
  `scheduledFor`, `performedAt`, `submittedOn`, `validUntil`, `dueDate`). `xsd:date`
  appears only in the header metadata `dct:created` / `dct:modified`.
- Put cardinality and value constraints in `shapes/`, not in the ontology.

Do not:

- No `owl:unionOf` in `rdfs:domain` or `rdfs:range`. When the HHM diagram draws one
  relation to several classes, leave the domain or range open and say so in
  `rdfs:comment` ("Range left open ... to stay within OWL 2 RL"). Examples:
  `constrains` (Skill / PlanStep / Module / Endpoint), `executedOn`, `represents`,
  `measuredSubject`, `hasIdentifier`, `hasEvidence`, `hasTime`, `exposedVia`.
- No `owl:oneOf` enumerations; use individuals.
- No cardinality restrictions or other anonymous superclasses; no `owl:equivalentClass`
  inside the modules (the generated `alignment/hhm-core.ttl` is the only place with
  equivalences, and it is not imported by the umbrella).
- No `owl:inverseOf`: each relation is stated in one direction (the one the HHM
  diagram draws) and the other direction is a query. Where MAESTRO 1.0 has both
  directions, the alignment file records the inverse.
- No external superclass except the two logical bridges (`ext/prov.ttl`, `ext/odrl.ttl`),
  whose targets are in pinned references (gate 5, gate 7).

Gate 5 runs the MAESTRO `tests/profile_check.py` lint over the modules; gate 6 runs the
owlrl closure over modules alone and over modules plus examples and fails on any
disjointness conflict.

## Design time versus runtime

Runtime instances belong in a runtime snapshot graph. In the example this is
`examples/widget-cell/runtime.ttl`, whose ontology node is also typed `maestro:Snapshot` and
carries `maestro:snapshotTaken`. `plant.ttl` and `market.ttl` may not contain instances of
`SkillExecution`, `StateAssertion`, `StateTransition`, `Fault`, `EnergyMeasurement`,
`PowerMeasurement`, `MaintenanceAction` and its subclasses, `ExecutionRecord`,
`Snapshot`, `Finding` or `ReturnToServiceAssessment` (gate 9, `RUNTIME_CLASSES` in
`validate.py`). `maestro:hasState`, the shortcut for the current operational state, is used
only inside a snapshot. Design-time files hold the specifications: skills, recipes,
products, policies, fault specifications, maintenance plans and tasks, twins.

## Encoding and line endings

All text files are UTF-8 without BOM and use LF line endings. The repository has
`core.autocrlf=true`, so the tools write with `encoding="utf-8", newline="\n"` and
compare generated output after `.replace("\r\n", "\n")`; never redirect tool output
into a file with PowerShell `>`. `tools/common.py` reconfigures stdout and stderr to
UTF-8 so labels with non-ASCII characters print on a Windows console. Turtle files keep
lines under a reasonable width except for definition strings, which stay on one line
so `grep` finds them.

## Coexistence with MAESTRO 1.0

Local names in this package coincide on purpose with MAESTRO 1.0 local names
(`Station`, `Module`, `Skill`, `Recipe`, `PlanStep`, `Policy`, `Endpoint`, `Quote`,
`Actor`, and many more). The IRIs differ only in the namespace. When both stacks are
loaded into one store, write queries with explicit prefixes (`maestro:Station` versus
`res:Station`), never with a shared prefix or with `FILTER(STRENDS(STR(?c), "Station"))`.
The MAESTRO repository helper `tests/profile_check.py` treats every IRI under
`https://w3id.org/maestro/` as a MAESTRO term, which is why `maestro:` terms pass its
declaration checks; that is intended, but it also means the two stacks must never be
merged into one file.

## Open domains and distinct individuals

A property that several unrelated classes use (for example `maestro:description`,
`maestro:hasTime`, `maestro:constrains`) has no `rdfs:domain` or `rdfs:range`, because an
`owl:unionOf` there would leave OWL 2 RL. The intended endpoints are recorded with
`schema:domainIncludes` and `schema:rangeIncludes` instead. These are annotations:
they do not entail types, they document intent, and `tools/gen_graph.py` reads them
to draw the relation.

Every controlled vocabulary (modes, protocols, data formats, statuses, states,
levels, outcomes, roles, control-flow types, parameter directions) closes with an
`owl:AllDifferent` axiom over its members, so a reasoner knows that two named
values are distinct. The axiom sits in the module that declares the members; the one
exception is `maestro:Protocol`, whose individuals are declared in one extension module per
protocol, so its `owl:AllDifferent` sits in the umbrella `maestro-hhm-core.ttl`, the
only file that imports all of them.
