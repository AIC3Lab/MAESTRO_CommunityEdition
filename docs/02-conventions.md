# 02 - Conventions

Rules every file of the package follows. `tools/validate.py` checks most of
them (the gate number is given where one applies).

## Module header

Every module file declares one `owl:Ontology` with this header. Compared with the
MAESTRO 1.0 header (`ontologies/logical/skill.ttl`) it drops `owl:priorVersion`,
`vs:term_status` and `core:changeRecord` and adds the `vann:` prefix pair.

```turtle
<https://w3id.org/maestro/skill> a owl:Ontology ;
    owl:versionIRI <https://w3id.org/maestro/skill/0.2.0> ;
    owl:versionInfo "0.2.0" ;
    dct:title "MAESTRO: Skills" ;
    rdfs:label "MAESTRO: Skills"@en ;
    dct:description "HHM-Core v1 Skills cluster: atomic and composite skills, typed parameters, pre- and postconditions and the protocol-neutral skill interface."@en ;
    rdfs:comment "Skills are logical specifications; execution technologies implement them. MAESTRO-local vocabulary; it is not aligned with, and makes no conformance claim to, any external standard. Definitions are reused from the MAESTRO 1.0 skill and core modules; dct:source names the term a definition was taken from."@en ;
    dct:creator "Melwin Xavier" ;
    dct:license <https://opensource.org/licenses/MIT> ;
    dct:created "2026-09-30"^^xsd:date ;
    dct:modified "2026-10-14"^^xsd:date ;
    dct:source <https://github.com/melwinxavier/MAESTRO> ;
    rdfs:seeAlso <https://w3id.org/maestro/skill> , <https://w3id.org/maestro/core> ;
    dct:conformsTo <https://www.w3.org/TR/owl2-profiles/#OWL_2_RL> ;
    dct:isPartOf <https://w3id.org/maestro> ;
    vann:preferredNamespacePrefix "maestro" ;
    vann:preferredNamespaceUri "https://w3id.org/maestro#"^^xsd:anyURI ;
    owl:imports <https://w3id.org/maestro/resource> .
```

Rules:

- Module IRI `https://w3id.org/maestro/<module>`, version IRI `<module IRI>/<version>`,
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
    rdfs:isDefinedBy <https://w3id.org/maestro/skill> .
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
only (gate 4). Shapes use `msh:` = `https://w3id.org/maestro/shapes#`; the synthetic
fixture in `queries/fixtures/widget-cell/` uses `ex:` =
`https://w3id.org/maestro/examples/widget-cell#`.

## External terms

The package uses terms it does not own: the Dublin Core, VANN, SKOS and schema.org
properties that annotate every term, and the PROV-O and ODRL classes and properties
that `experimental-extensions/prov.ttl` and `experimental-extensions/odrl.ttl` bridge to. OWL 2 requires every class and
property that is used to be declared; an undeclared one takes the ontology out of the
OWL 2 RL and OWL 2 DL profiles. No upstream ontology is imported, so the declarations
are stated once, in the last section of the root module `core/resource.ttl`, which
every module imports:

```turtle
skos:definition a owl:AnnotationProperty .
prov:Activity a owl:Class .
prov:used a owl:ObjectProperty .
```

Rules (gates 2, 3 and 5):

- A declaration names the kind of the term and nothing else: no label, no definition,
  no `rdfs:isDefinedBy`, no axiom copied from the upstream ontology. The term keeps its
  own namespace.
- External terms are declared in `core/resource.ttl` only; every other module may use
  them but has no subject outside `maestro:`.
- The documentary properties (`dct:*`, `vann:*`, `skos:*`, `schema:domainIncludes`,
  `schema:rangeIncludes`) are annotation properties. Importing the full SKOS, PROV-O or
  ODRL ontology later would give some of them another kind and needs a fresh profile
  check.
- A module that uses a new external term adds its declaration there in the same
  change; gate 5 fails on a class or property that is used but not declared.

## `rdfs:isDefinedBy`

`rdfs:isDefinedBy` on a term equals the ontology IRI of the file that declares it, and
nothing else. A term that is only mentioned in another file (for example `maestro:Recipe`
inside `experimental-extensions/isa88.ttl`, or `maestro:ExecutionStatus` inside `experimental-extensions/runtime.ttl`) does not
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
  faulted state value and `FaultEvent` for the occurrence), `maestro:raisedFault
  dct:references <https://w3id.org/maestro/runtime#raisedFault>`, `maestro:unitRef
  dct:references <https://w3id.org/maestro/skill#unitRef>` (object property there,
  datatype property here).
- Neither: the term has no MAESTRO 1.0 counterpart (`maestro:location`, `maestro:targetStep`,
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

- Declare disjointness between named classes only: `owl:disjointWith` for pairs
  (`AtomicSkill` / `CompositeSkill`, `Recipe` / `PlanStep`, `ProductInstance` /
  `ProductType`), `owl:AllDisjointClasses` for groups (the value-set classes, in
  `experimental-extensions/runtime.ttl` and `experimental-extensions/maintenance.ttl` over the value sets each imports;
  the kinds of product information in `core/product.ttl`). Never declare the cluster
  grouping classes (`SkillElement`, `InvocationElement`, `Resource`, ...) disjoint: the
  examples deliberately type one node in two clusters, for instance an
  `maestro:ParameterDef` that is also an `maestro:DtdlProperty`, or an `maestro:Station` that is also
  an `maestro:WorkUnit`.
- Group the classes of each cluster under one grouping class (`SkillElement`,
  `RecipeElement`, `ProductElement`, `Resource`, `InvocationElement`,
  `ExecutionElement`, `PolicyElement`, `SafetyElement`, `RuntimeStateElement`,
  `EnergyElement`, `MaintenanceElement`, `MaaSElement`, `DigitalTwinElement`,
  `EquipmentHierarchyElement`) and every value-set class under `ValueSet`.
- Make structural part-whole edges sub-properties of the transitive `maestro:hasPart`
  (`hasModule`, `hasStep`, `hasSubSkill`, `hasSubItem`), so `maestro:hasPart+` reaches every
  nested part.
- Mark a property `owl:FunctionalProperty` only when one value per subject is part of
  its meaning: a timestamp, an identifier value, a port, a parameter's type, unit,
  bounds and direction, a step order, a flow type, the two ends of a data binding,
  the SIL and PL levels, `valueOf` and `instanceOfType`. A functional object property
  with two values makes an OWL 2 RL reasoner merge the values with `owl:sameAs`, so
  relations that can legitimately have several values (`represents`, `describedIn`,
  `hasStatus`) or that change through reconfiguration (`moduleOf`, `stepOf`) are not
  functional; their limits are SHACL warnings.
- Model controlled vocabularies as named individuals of a class (`OperatingMode`, `Protocol`,
  `DataFormat`, `InterfaceDescriptionLanguage`, `ExecutionStatus`, `State`,
  `StateDimension`, `RiskLevel`, `SafetyIntegrityLevel`, `PerformanceLevel`,
  `EnergySource`, `ReturnToServiceOutcome`, `ControlFlowType`, `ParameterDirection`,
  `Action`, and the three market roles as `Role` individuals).
- Give numeric datatype properties the range `rdfs:Literal` and check the datatype in
  SHACL with `sh:or (xsd:decimal xsd:integer xsd:double xsd:float)` (MAESTRO ADR-0007).
  At 0.2.0: `minValue`, `maxValue`, `energyKwh`, `powerWatts`, `mtbfHours`,
  `remainingUsefulLifeHours`. Money and counts with a fixed type keep it
  (`price xsd:decimal`, `quantity`, `stepOrder`).
- Give a text property that may carry a language tag the range `rdfs:Literal` as well,
  and check in SHACL that the value is an `xsd:string` or an `rdf:langString`
  (`msh:DescriptionTextShape`). This applies to `maestro:description`. A language-tagged
  literal is not an `xsd:string`: with the range `xsd:string`, every `"..."@en`
  description makes the graph inconsistent under OWL semantics, which a DL reasoner
  reports and the OWL 2 RL rule set does not. Gate 6 therefore also compares every
  literal with the declared range of its datatype property. The other `xsd:string`
  properties (`version`, `model`, `location`, `faultCode`, ...) keep that range and take
  plain strings only; a language-tagged value on one of them fails gate 6.
- `maestro:value` has no range; the datatype of the literal is the `maestro:paramType` of
  its parameter definition, by exact datatype IRI (`msh:ParameterValueDatatypeShape`).
- Use `xsd:dateTime` for every time-valued datatype property (`startTime`, `endTime`,
  `timestamp`, `validFrom`, `validTo`, `observedAt`, `recordedAt`, `snapshotTaken`,
  `scheduledFor`, `performedAt`, `submittedOn`, `validUntil`, `dueDate`). `xsd:date`
  appears only in the header metadata `dct:created` / `dct:modified`.
- Put minimum cardinalities, value-set closure and every other closed-world check in
  `shacl/`, not in the ontology.

Do not:

- No `owl:unionOf` in `rdfs:domain` or `rdfs:range`. When the HHM diagram draws one
  relation to several classes, leave the domain or range open and say so in
  `rdfs:comment` ("Range left open ... to stay within OWL 2 RL"). Examples:
  `constrains` (Skill / PlanStep / Module / Endpoint), `executedOn`, `represents`,
  `measuredSubject`, `hasIdentifier`, `hasEvidence`, `hasTime`, `exposedVia`.
- No `owl:oneOf` enumerations; use individuals.
- No cardinality restrictions or other anonymous superclasses. Inside the modules,
  `owl:equivalentClass` / `owl:equivalentProperty` appear only on a deprecated 0.1.0
  name, pointing at the term that replaced it (`owl:deprecated true`,
  `dct:isReplacedBy`); equivalences to external vocabularies live in the generated
  `alignment/hhm-core.ttl`, which the umbrella does not import.
- `owl:inverseOf` only for a named inverse of a structural or frequently navigated
  relation (`moduleOf`, `providedBy`, `requiredBy`, `stepOf`, `instanceOfType`,
  `variantOf`, `executedBy`, `representedBy`, `hostsServer`, `partOf`). Data states the
  direction the HHM diagram draws; the reasoner adds the inverse.

## Renamed terms (0.2.0)

Twelve 0.1.0 names were replaced by clearer ones. Each old IRI stays declared in its
module as `owl:deprecated true`, `owl:equivalentClass` / `owl:equivalentProperty` and
`dct:isReplacedBy` of the new term, so data written against 0.1.0 still reasons,
validates and answers the queries. The shapes are written against the 0.2.0 names and
RDFS inference does not follow an OWL equivalence, so `tools/validate.py` first restates
everything said with a deprecated name under the name that replaced it
(`with_current_names` in `tools/common.py`); a SHACL run outside the validator needs the
same step, or OWL 2 RL inference. The HHM-Core names among them are mapped to the new
terms in `alignment/hhm-core.ttl` (`HHM_RENAMED` in `tools/gen_alignment.py`).

| 0.1.0 name | 0.2.0 name | HHM-Core name |
|---|---|---|
| `BOMNode` | `BOMItem` | `BOMNode` |
| `hasBOM` | `hasBOMItem` | `hasBOM` |
| `hasPart` (BOM nesting) | `hasSubItem`; `hasPart` is now the generic transitive super-property | `hasPart` |
| `Mode` | `OperatingMode` | `Mode` |
| `contains` | `hasConstraint` | `contains` |
| `increases` | `causesRisk` | `increases` |
| `riskLevel` | `hasRiskLevel` | - |
| `hasSubSkillLink` | `hasSubSkill` | `hasSubSkillLink` |
| `instanceOf` | `valueOf` | `instanceOf` |
| `mayRaise` | `raisedFault` | `mayRaise` |
| `exposesInterface` | `implementsInterface` | - |
| `relatedStep` | `targetStep` | - |
| `urlTemplate` | `uriTemplate` | - |
| `specializesAs` | merged into `usesProtocol` (domain open: `Endpoint`, `Binding`) | - |
- No external superclass except the two logical bridges (`experimental-extensions/prov.ttl`, `experimental-extensions/odrl.ttl`),
  whose targets are in pinned references (gate 5, gate 7).

Gate 5 runs the structural lint `tools/rl_lint.py` over the modules; gate 6 runs the
owlrl closure over modules alone, over modules plus examples and over modules plus the
synthetic fixture, and fails on any disjointness conflict or on a literal outside the
range of its property. The lint and the closure are not a DL reasoner: after a change
to a range, a characteristic or a disjointness axiom, also run a profile validator
(ROBOT `validate-profile --profile RL`) and a DL reasoner (HermiT) over the merged
ontology and the use-case graphs.

## Design time versus runtime

Runtime instances belong in a runtime snapshot graph: the `ext/runtime.ttl` file of a use
case, with its `maestro:Snapshot` node (the fixture `queries/fixtures/widget-cell/runtime.ttl`
shows one). The other use-case files may not contain instances of
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

Since 0.2.0 the package is published as plain MAESTRO: terms in `https://w3id.org/maestro#` (prefix `maestro:`), ontology IRI `https://w3id.org/maestro`, module IRIs `https://w3id.org/maestro/<module>`. The ontology IRI was the MAESTRO 1.0 umbrella IRI, and most module IRIs (`skill`, `recipe`, `product`, `policy`, `runtime`, `energy`, `maintenance`, `maas`, `resource`, `opcua`, `prov`, ...) equal MAESTRO 1.0 module IRIs, so this package replaces MAESTRO 1.0 under those identifiers. The term namespaces still differ (`https://w3id.org/maestro#` here, `https://w3id.org/maestro/<module>#` in MAESTRO 1.0), so instance data does not clash, but never import both ontology stacks into one store or tool session.

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
values are distinct.
