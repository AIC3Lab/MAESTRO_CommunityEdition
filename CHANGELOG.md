# Changelog

All notable changes to the MAESTRO package are recorded here. The format
follows Keep a Changelog; the package uses semantic versioning. The version is stamped
on the umbrella and on every module (`owl:versionInfo`, `owl:versionIRI`); `build.py`
fails on drift.

## [Unreleased]

Community Edition: entries about use-case graphs that are not part of this repository
are left out.

### Fixed (validation audit of 2026-11-13)

Findings of `VALIDATION_REPORT.md`; the issue identifiers are those of the report.

- **C01, ontology inconsistent with its data.** `maestro:description` had the range
  `xsd:string`, and 433 descriptions in the use-case graphs carry a language tag; a
  language-tagged literal is not an `xsd:string`, so the ontology plus the use-case graphs
  were inconsistent under OWL semantics. The range is now `rdfs:Literal`, and the new shape
  `msh:DescriptionTextShape` requires an `xsd:string` or `rdf:langString` literal. No
  description was changed. HermiT finds the modules plus the use-case graphs consistent.
- **O01, OWL 2 RL / DL profile.** The external terms the package uses were not declared.
  `core/resource.ttl` now declares their kind in a closing section: the Dublin Core, VANN,
  SKOS and schema.org annotation properties, and the PROV-O and ODRL classes and properties
  of the two bridge modules (32 declarations; no import, no upstream axiom). ROBOT accepts
  `maestro-merged.ttl`, the umbrella and every module's import closure as OWL 2 RL and
  OWL 2 DL.
- **S01, S04, S05, missing shapes.** `msh:ParameterValueDatatypeShape` (the datatype of a
  `maestro:value` is the `maestro:paramType` of its definition, by exact datatype IRI),
  `msh:ParameterDefBoundsOrderShape` (minimum not above maximum) and
  `msh:StateAssertionIntervalOrderShape` (`validTo` not before `validFrom`). The use-case
  graphs raise none of them.
- **S02.** `msh:ExecutionStepSkillShape` reports a warning, as intended; `sh:severity` sat
  on the SPARQL constraint, where SHACL ignores it.
- **S03.** Data written with a deprecated 0.1.0 name is validated like data written with
  the name that replaced it: `tools/validate.py` restates it under the 0.2.0 name before
  running the shapes.
- **Q01.** CQ04 also returns bindings from or to a bidirectional (`maestro:InOut`)
  parameter.
- **Q02, Q03, competency questions.** Gate 11 separates what the schema can answer from
  what the use-case graphs contain. The competency questions must be answered in full
  (row floor, and a row binding every answer field, `CQ_ANSWER_FIELDS`) over the synthetic
  fixture `queries/fixtures/widget-cell/`, the former widget-cell example restored as
  marked test data with one bidirectional binding added. Over the use-case graphs each
  question is reported as answered, partial or without data: seven answered, CQ08 and
  CQ14 partial, CQ09 to CQ13 and CQ15 without data. No record was added to a use-case
  graph.
- **T01, standalone tools.** The tools no longer import helpers of the MAESTRO 1.0
  repository. New `tools/serialize.py` writes the merged ontology (same text as before for
  the same graph) and `tools/rl_lint.py` is the OWL 2 RL structural lint of gate 5, which
  now fails on a class or property that is used but not declared. Gate 6 also fails on a
  literal outside the declared range of its datatype property. Gate 7 checks every mapping
  target against the vocabularies of the standards basis and, where the pinned references
  and the MAESTRO 1.0 sources are available, against those; otherwise it states what it
  did not check.
- **T03, D01.** `tools/build.py` writes `maestro-merged.ttl`, `catalog-v001.xml` and
  `docs/terms.md` in place and removes nothing outside `dist/`; the `ontologies/` copies
  are gone from the build. The merged ontology and the term dictionary were regenerated,
  which also brings five module comments in the merged file up to date.
- **D02, D03.** `docs/04-competency-questions.md` and `queries/README.md` describe the
  fixture and the coverage report. The two alignment files are documented as optional
  outputs that are not shipped; `tools/gen_alignment.py` writes them only when the
  MAESTRO 1.0 sources are there to verify their targets.

### Added

- `shacl/probes/`: eight small synthetic graphs, each with an expected result, that test
  the shapes themselves (gate 10).

### Changed (extension folder renamed)

- The ontology folder `ext/` is now `experimental-extensions/`. The twelve module files,
  their ontology IRIs (`https://w3id.org/maestro/<module>`) and every term IRI are
  unchanged; `catalog-v001.xml` resolves the module IRIs to the new paths. The `ext/`
  subfolder of each use case under `usecase-knowledge-graphs/` keeps its name, and so do
  the use-case module IRIs (`…/<use case>/ext/<module>`).
- `tools/common.py` maps the layer `ext` to its folder (`LAYER_DIRS`); `build.py` and
  `gen_graph.py` write paths through it. Path mentions in the module headers and
  comments, the shapes, the guides under `docs/` and `docs/graph.html` follow the new
  name. The 0.2.0 figures under `figures/v0.2.0/` still show `ext/`.

### Changed (use-case knowledge graphs split by module)

- Every use case under `usecase-knowledge-graphs/` is laid out like the ontology: an
  umbrella file with the `owl:Ontology` header, one Turtle file per MAESTRO module under
  `core/` and `ext/`, and a generated `<name>-merged.ttl`. These replace `plant.ttl`,
  `product.ttl`, `market.ttl`, `runtime.ttl` and `shared.ttl`. The statements are the same; individuals keep their IRIs.
  `usecase-knowledge-graphs/README.md` describes the layout and where a statement goes.
- Ontology IRIs: the use-case IRI (for example `…/ltu-festo-mps/handling`) is
  now the umbrella; module files are `…/<use case>/core/<module>` and
  `…/<use case>/ext/<module>`. The former per-file IRIs `…/product` and `…/market`
  are gone.
- New `tools/merge_usecases.py` writes the merged files; `--check` reports a stale merged
  file, an umbrella that does not import its module files and a statement in the wrong
  module file. The figure scripts read the merged files; the validators skip them.

### Changed (published as MAESTRO)

- The package is now called MAESTRO instead of MAESTRO HHM-Core. Terms moved from
  `https://w3id.org/maestro/hhm#` (prefix `mh:`) to `https://w3id.org/maestro#` (prefix
  `maestro:`); the ontology IRI is `https://w3id.org/maestro`, module IRIs
  `https://w3id.org/maestro/<module>`, shapes `https://w3id.org/maestro/shapes#` (prefix
  `msh:`), examples `https://w3id.org/maestro/examples/...`. The umbrella file is
  `maestro.ttl`, the merged ontology `ontologies/maestro-merged.ttl`. Modules, shapes,
  examples, queries, tools, docs and figures use the new IRIs and names.
- The ontology IRI and most module IRIs were MAESTRO 1.0 identifiers; this package replaces
  MAESTRO 1.0 under them (docs/02-conventions.md, "Coexistence with MAESTRO 1.0").
  `rdfs:seeAlso` links that became self-references were removed.
- Kept: the HHM-Core v1 reference model as documentation of where the structure comes from
  (`alignment/hhm-core.ttl`, `docs/hhm-conformance.md`, the cluster comments, figure 03).
- `tools/validate.py` gate 8 and the figure name check match the `maestro:` prefix.

### Added (ontology 0.2.0)

- Grouping classes, one per cluster, with no disjointness between them:
  `SkillElement`, `RecipeElement`, `ProductElement`, `Resource` (over `Station` and
  `Module`), `InvocationElement` (also over the OPC UA and DTDL node classes),
  `ExecutionElement`, `PolicyElement`, `SafetyElement`, `RuntimeStateElement`,
  `EnergyElement`, `MaintenanceElement`, `MaaSElement`, `DigitalTwinElement`,
  `EquipmentHierarchyElement`; `ValueSet` over every value-set class;
  `Condition` over `Precondition` and `Postcondition`.
- Part-whole hierarchy: `hasPart` (moved to `core/resource.ttl`, now transitive and
  domain-open) with inverse `partOf`; `hasModule`, `hasStep`, `hasSubSkill` and the new
  `hasSubItem` are sub-properties.
- Inverse properties: `moduleOf`, `providedBy`, `requiredBy`, `stepOf`,
  `instanceOfType`, `variantOf`, `executedBy`, `representedBy`, `hostsServer`.
- Super-properties `hasCondition` (over `hasPrecondition`, `hasPostcondition`) and
  `bindsParameter` (over `bindsFrom`, `bindsTo`); `returns` stays as declared.
  `bindsInterface` is a sub-property of the new `specializes`.
- New terms: `realizesStep` (execution to plan step; `core/execution.ttl` now imports
  `recipe`), `hasOutput` (sub-property of `prov:generated`), `recommendsMitigation`,
  `specializes` (Binding to SkillInterface), `paramName`, `mappingSpec`, and the
  parameter direction `InOut`.
- `grantedTo` is a sub-property of `odrl:assignee`.
- `owl:FunctionalProperty` on single-valued attributes: `paramType`, `unitRef`,
  `minValue`, `maxValue`, `parameterDirection`, `valueOf`, `paramName`, `stepOrder`,
  `flowType`, `bindsFrom`, `bindsTo`, `identifierValue`, `identifierScheme`,
  `instanceOfType`, `address`, `port`, `startTime`, `endTime`, `timestamp`,
  `requiredSIL`, `achievedSIL`, `requiredPerformanceLevel`, `achievedPerformanceLevel`,
  `httpMethod`, `uriTemplate`, `startedAtTime`, `endedAtTime`.
- Disjointness: `owl:AllDisjointClasses` over the value-set classes
  (`modules/runtime.ttl`, `modules/maintenance.ttl`) and over the kinds of product
  information (`core/product.ttl`).
- Shapes: `ModuleStationShape` and `PlanStepRecipeShape` (warnings: at most one station
  per module, one recipe per step), `ExecutionStepSkillShape` (warning: an execution's
  skill should realise the step it realises), and property shapes for `paramName`,
  `hasOutput`, `realizesStep`, `recommendsMitigation`, `specializes` and
  `mappingSpec`. Data bindings may start or end at an `InOut` parameter.

### Changed (ontology 0.2.0)

- Renamed for clarity (old IRI kept, see Deprecated): `BOMNode` -> `BOMItem`,
  `hasBOM` -> `hasBOMItem`, BOM nesting `hasPart` -> `hasSubItem`, `Mode` ->
  `OperatingMode`, `contains` -> `hasConstraint`, `increases` -> `causesRisk`,
  `riskLevel` -> `hasRiskLevel`, `hasSubSkillLink` -> `hasSubSkill`, `instanceOf` ->
  `valueOf`, `mayRaise` -> `raisedFault`, `exposesInterface` -> `implementsInterface`,
  `relatedStep` -> `targetStep`, `urlTemplate` -> `uriTemplate`; `specializesAs` merged
  into `usesProtocol`, whose domain is now open (`Endpoint`, `Binding`). Examples,
  queries, shapes and figure scripts use the new names.
- `tools/gen_alignment.py`: `HHM_RENAMED` maps the nine renamed HHM-Core terms, so
  `alignment/hhm-core.ttl` and `docs/hhm-conformance.md` keep full coverage (43 of 43
  classes, 47 of 47 relations); deprecated names are not counted as unmapped in
  `alignment/maestro-1.0.ttl`. `tools/gen_graph.py` skips deprecated terms.
- `docs/02-conventions.md`: OWL 2 RL rules updated for grouping classes, group
  disjointness, functional properties, inverses and deprecated equivalents; table of
  renamed terms.
- Version 0.2.0 on the umbrella (with `owl:priorVersion` 0.1.0) and every module.

### Removed (folder cleanup, only the latest version kept)

- The 0.1.0 figures (`figures/png/`, `figures/src/`, `figures/artifact-graphs/{png,svg,src}`,
  `examples/kg-ltu-*.png|svg`) and the artifact snapshot `proposed-model.json`; the 0.2.0
  set in `figures/v0.2.0/` replaces them.
- `dist/`: a duplicate of `ontologies/`; `tools/build.py` still writes it locally, and
  `.gitignore` now keeps it out of the repository, with `__pycache__/` and Word lock files.
- The render scripts moved to `figures/v0.2.0/scripts/` and build their model from the
  Turtle files (`tools/gen_graph.py`); `src/03-hhm-schema.gv` and `src/07-beyond-clusters.gv`
  are now the hand-authored 0.2.0 sources, and `--check` also rejects deprecated names.

### Deprecated (ontology 0.2.0)

- `BOMNode`, `hasBOM`, `Mode`, `contains`, `increases`, `riskLevel`,
  `hasSubSkillLink`, `instanceOf`, `mayRaise`, `exposesInterface`, `relatedStep`,
  `urlTemplate`, `specializesAs`: declared `owl:deprecated true` with
  `owl:equivalentClass` / `owl:equivalentProperty` and `dct:isReplacedBy` of the new
  term, so 0.1.0 data still reasons and validates.

### Added

- `examples/ltu-festo-mps/`: the LTU use case, a four-station Festo Didactic MPS line
  (Distributing 648811, Testing 648812, Processing 648813, Handling 655633) built from
  the station manuals, electric and pneumatic circuit diagrams, parts lists, data
  sheets and GRAFCET function charts, with `maestro:` terms only. Standard example layout:
  `shared/shared.ttl` (LTU, the line work centre, capabilities, SysLink / StationLink
  protocols, safety rules, cleaning tasks, Festo component catalogue), then one folder
  per production unit with `plant.ttl` and `product.ttl`. A station `plant.ttl` holds
  the functional `maestro:Module`s, a bill of materials over the catalogue, every I/O
  signal as an `maestro:ParameterDef` with its SysLink bit, pin and BMK identifiers behind
  `maestro:Endpoint`s for XMA2 / XMA3 / XMG1, one atomic skill per GRAFCET action plus a
  composite station-cycle skill, hazards and care plans; its `product.ttl` the GRAFCET
  as an `maestro:Recipe` with control-flow constraints. `line/plant.ttl` links the stations
  (material and StationLink ports); `line/product.ttl` holds the workpiece with its
  colour variants and the line recipe.
- `queries/ltu/`: four LTU questions (I/O allocation, line route by capability,
  GRAFCET sequences, station bills of materials) with floors in `CQ_MINIMUMS`.

- `ontologies/`: committed, generated copy of the umbrella and the twenty modules plus
  the merged single-file ontology `maestro-merged.ttl`, a catalog and a README,
  written by `tools/build.py` and covered by the gate 12 stale check.
- `figures/`: seven architecture figures in the style of the repository-level figures
  (module stack, `owl:imports` graph, HHM cluster schema, standards basis, widget-cell
  instance graph, MAESTRO 1.0 definition provenance, beyond-cluster modules), with the
  renderer `figures/scripts/render_figures.py`. Figures 01, 02, 04, 05 and 06 are
  derived from the Turtle files at render time; `--check` verifies that the two
  hand-authored Graphviz sources name declared `maestro:` terms only.

## [0.1.0] - 2026-09-30

First version. Structure follows the HHM-Core v1 reference model; definitions are
reused from MAESTRO 1.0 term by term (`dct:source` / `dct:references`).

### Added

- `owl:AllDifferent` on every controlled vocabulary; `schema:domainIncludes` /
  `schema:rangeIncludes` on properties whose OWL domain or range is left open;
  the faulted state value is `maestro:FaultState`.

- Umbrella `maestro.ttl` (`https://w3id.org/maestro`) importing twenty
  modules, and the committed root `catalog-v001.xml`.
- Core modules, one per HHM cluster: `core/resource.ttl` (Station, Module, Capability),
  `core/skill.ttl` (Skill, AtomicSkill, CompositeSkill, ParameterDef, ParameterValue,
  ParameterDirection, Precondition, Postcondition, SkillInterface), `core/recipe.ttl`
  (Recipe, PlanStep, ControlFlowConstraint, ControlFlowType, DataBinding),
  `core/product.ttl` (ProductType, ProductInstance, Variant, Feature, Requirement,
  Identifier, BOMNode, Material), `core/invocation.ttl` (Endpoint, Protocol, Binding,
  SkillService, EventStream, plus OperationSignature, DataFormat and
  InterfaceDescriptionLanguage folded in from the MAESTRO communication module),
  `core/policy.ttl` (Policy, Constraint, Hazard, Risk, Mitigation, Mode, Role,
  Permission, Action, Evidence, plus SafetyFunction, EmergencyStop,
  SafetyIntegrityLevel, PerformanceLevel, RiskLevel and RiskAssessment folded in from
  the MAESTRO safety module), `core/execution.ttl` (SkillExecution, ExecutionStatus,
  Fault, TimeInterval).
- Three relations implied by the HHM diagram but not drawn: `maestro:relatedStep`,
  `maestro:bindsFrom`, `maestro:bindsTo`.
- Modules: `modules/runtime.ttl` (State, StateDimension, StateAssertion, RuntimeEvent,
  StateTransition, FaultSpecification, ExecutionRecord, Snapshot; declares
  `maestro:ExecutionStatus rdfs:subClassOf maestro:State`), `modules/energy.ttl`
  (EnergyConsumer, EnergyMeasurement, PowerMeasurement, EnergySource),
  `modules/maintenance.ttl` (MaintenanceAction and its four kinds, Inspection,
  FaultDiagnosis, MaintenancePlan, MaintenanceTask, Finding,
  ReturnToServiceAssessment, ReturnToServiceOutcome), `modules/maas.ttl` (Actor,
  Customer, PhysicalResourceProvider, Marketplace, ServiceOffer, ServiceRequest, Quote,
  Contract, ProductionOrder).
- Extensions: `ext/digital-twin.ttl` (DigitalTwin, TwinBinding), `ext/opcua.ttl`
  (OpcUaServer, OpcUaNode, OpcUaObject, OpcUaVariable, OpcUaMethod,
  OpcUaSkillInterface, OpcUaBinding), `ext/isa88.ttl`, `ext/isa95.ttl` (Enterprise,
  Site, Area, WorkCenter, WorkUnit), `ext/automationml.ttl` (InternalElement,
  ExternalInterface, InternalLink), `ext/dtdl.ttl` (DtdlInterface, DtdlCommand,
  DtdlTelemetry, DtdlProperty, DtdlBinding), `ext/rest.ttl` (RestInterface,
  RestBinding), `ext/prov.ttl`, `ext/odrl.ttl`.
- Controlled vocabularies as named individuals: parameter directions, control-flow
  types, protocols, data formats, interface description languages, modes, actions,
  SIL 1-4, PL a-e, risk levels, execution statuses, states, state dimensions, energy
  sources, return-to-service outcomes, market roles.
- Documentary matches to pinned HSU-AUT ontology design patterns (PackML, WADL, DIN EN
  61360, VDI 2206, ISA-88.01, DIN EN 62264-2, OPC UA, AutomationML, ISO 22400-2), to
  schema.org and to DTDL v3; logical bridges to PROV-O and the ODRL 2.2 core profile.
- Generated alignments `alignment/maestro-1.0.ttl` (SKOS matches from per-term
  provenance) and `alignment/hhm-core.ttl` (equivalences to the `hhm:` placeholder
  namespace), produced by `tools/gen_alignment.py`.
- SHACL shapes under `shapes/` (prefix `msh:`), one file per module group.
- Example ABox `examples/widget-cell/` in three files: `plant.ttl` (design time),
  `market.ttl` (manufacturing as a service), `runtime.ttl` (runtime snapshot).
- Competency questions `queries/cq/cq01` to `cq15` with row floors in `validate.py`.
- Tools: `tools/common.py`, `tools/validate.py` (twelve gates), `tools/build.py`
  (merged `dist/` outputs, root catalog, generated `docs/terms.md`),
  `tools/gen_alignment.py` (alignments and generated `docs/hhm-conformance.md`),
  `tools/gen_graph.py` (generated `docs/graph.html`).
- Documentation: `README.md`, `docs/01-overview.md`, `docs/02-conventions.md`,
  `docs/03-standards-basis.md`, `docs/04-competency-questions.md`, `docs/placement.md`;
  generated `docs/terms.md`, `docs/hhm-conformance.md`, `docs/graph.html`.

### Not included (by decision)

- No unit module: `maestro:unitRef` is an `xsd:anyURI` literal holding a QUDT unit IRI;
  numeric properties fix the unit in their name.
- No sensor module: SOSA/SSN stays a documented hook on `maestro:Skill`.
- ECLASS, DPP, PRONTO, CaSkMan / CSS, AAS, OpenAPI, SAREF4INMA and XACML are named as
  hooks only, without IRIs or mappings.
