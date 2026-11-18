# 01 - Overview

## Purpose

MAESTRO is the MAESTRO manufacturing ontology re-cut to the shape of the
HHM-Core v1 reference model. The reference model is a diagram of seven clusters and a
minimal digital-twin extension, with named classes and named relations between them.
This package keeps those names, keeps the cluster boundaries as file boundaries, and
fills each term with the MAESTRO 1.0 definition of the same concept. The result is a
small ontology (twenty modules, about 370 terms) that a partner who knows the HHM
diagram can read without learning the full MAESTRO module stack, while every term stays
traceable to MAESTRO 1.0 through `dct:source` or `dct:references`.

The umbrella is `https://w3id.org/maestro` (file `maestro.ttl`). All terms
share the namespace `https://w3id.org/maestro#`, prefix `maestro:`. Each module has its
own ontology IRI `https://w3id.org/maestro/<module>` and every term names its module
with `rdfs:isDefinedBy`.

## HHM-Core v1 clusters to modules

| HHM cluster | File | Classes |
|---|---|---|
| Product | `core/product.ttl` | `ProductType`, `ProductInstance`, `Variant`, `Feature`, `Requirement`, `Identifier`, `BOMItem`, `Material` |
| Physical Resources | `core/resource.ttl` | `Station`, `Module`, `Capability` |
| Skills | `core/skill.ttl` | `Skill`, `AtomicSkill`, `CompositeSkill`, `ParameterDef`, `ParameterValue`, `ParameterDirection`, `Precondition`, `Postcondition`, `SkillInterface` |
| Recipe / Planning | `core/recipe.ttl` | `Recipe` (alt label ProcessPlan), `PlanStep`, `ControlFlowConstraint`, `ControlFlowType`, `DataBinding` |
| Safety / Security / Policy | `core/policy.ttl` | `Policy`, `Constraint`, `Hazard`, `Risk`, `Mitigation`, `OperatingMode`, `Role`, `Permission`, `Action`, `Evidence`; folded in from MAESTRO safety: `SafetyFunction`, `EmergencyStop`, `SafetyIntegrityLevel`, `PerformanceLevel`, `RiskLevel`, `RiskAssessment` |
| Invocation Hooks | `core/invocation.ttl` | `Endpoint`, `Protocol`, `Binding`, `SkillService`, `EventStream`; folded in from MAESTRO communication: `OperationSignature`, `DataFormat`, `InterfaceDescriptionLanguage` |
| Minimal Execution (optional) | `core/execution.ttl` | `SkillExecution`, `ExecutionStatus`, `Fault`, `TimeInterval` |

Relation names follow the diagram: `hasModule`, `providesCapability`,
`hasSubSkill` (CompositeSkill to Skill, no intermediate class), `hasParameterDef`,
`hasPrecondition`, `hasPostcondition`, `requiresCapability`, `hasInterfaceContract`,
`hasStep`, `realizedBy`, `hasControlFlow`, `hasDataBinding`, `hasVariant`,
`hasFeature`, `hasRequirement`, `hasIdentifier`, `hasBOMItem`, `hasSubItem`, `madeOf`,
`hasConstraint`, `hasPermission`, `grantedTo`, `requiresMode`, `hasEvidence`, `constrains`,
`causesRisk`, `reduces`, `exposedVia`, `usesProtocol`, `hasBinding`, `executes`,
`executedOn`, `invokedVia`, `hasInput`, `hasStatus`, `raisedFault`, `hasTime`. Since
0.2.0 nine HHM-Core terms carry a clearer package name (`BOMNode`, `Mode`,
`hasBOM`, `hasPart`, `hasSubSkillLink`, `instanceOf`, `contains`, `increases`,
`mayRaise` in HHM-Core); the HHM names stay declared as deprecated equivalents (except
`hasPart`, now the generic part-whole super-property) and
`alignment/hhm-core.ttl` maps them (see 02-conventions, "Renamed terms"). Three
relations the diagram implies but does not draw were added so its nodes are usable:
`targetStep` (ControlFlowConstraint to PlanStep) and `bindsFrom` / `bindsTo`
(DataBinding to ParameterDef).

Structure added in 0.2.0: one grouping class per cluster (`SkillElement`,
`RecipeElement`, `ProductElement`, `Resource`, `InvocationElement`, ...) and `ValueSet`
over the controlled vocabularies; a transitive `hasPart` / `partOf` pair above
`hasModule`, `hasStep`, `hasSubSkill` and `hasSubItem`; named inverses (`moduleOf`,
`providedBy`, `requiredBy`, `stepOf`, `instanceOfType`, `variantOf`, `executedBy`,
`representedBy`, `hostsServer`); the super-properties `hasCondition` and
`bindsParameter`; and the new terms `Condition`, `realizesStep`, `hasOutput`,
`recommendsMitigation`, `specializes`, `paramName`, `mappingSpec` and the parameter
direction `InOut`.

Status values: `ExecutionStatus` is a controlled vocabulary (`Idle`, `Executing`,
`Held`, `Completed`, `Aborted`) declared in `core/execution.ttl`. `experimental-extensions/runtime.ttl`
adds `maestro:ExecutionStatus rdfs:subClassOf maestro:State`, so the values shared with the live
state model exist once.

## Beyond the clusters

| Group | File | Content |
|---|---|---|
| Runtime state | `experimental-extensions/runtime.ttl` | `State` and its values (`Available`, `Busy`, `FaultState`, `Alarm`, `Healthy`, `Degraded`, `Failed`, `Reserved`), `StateDimension` (`OperationalDimension`, `HealthDimension`, `ReservationDimension`, `ModeDimension`), `StateAssertion`, `RuntimeEvent`, `StateTransition`, `FaultSpecification`, `ExecutionRecord`, `Snapshot` |
| Energy | `experimental-extensions/energy.ttl` | `EnergyConsumer` (subclass of `Module`), `EnergyMeasurement`, `PowerMeasurement`, `EnergySource` (`ElectricalGrid`, `Solar`, `Wind`, `CompressedAir`) |
| Maintenance | `experimental-extensions/maintenance.ttl` | `MaintenanceAction` with `Preventive`, `Corrective`, `ConditionBased`, `Predictive`, `Inspection`; `FaultDiagnosis`, `MaintenancePlan`, `MaintenanceTask`, `Finding`, `ReturnToServiceAssessment`, `ReturnToServiceOutcome` |
| Manufacturing as a service | `core/maas.ttl` | `Actor`, `Customer`, `PhysicalResourceProvider`, `Marketplace`, `ServiceOffer`, `ServiceRequest`, `Quote`, `Contract`, `ProductionOrder` |

## The digital-twin extension

`experimental-extensions/digital-twin.ttl` is the HHM "Minimal Digital Twin Extension connected to
HHM-Core". It declares `DigitalTwin` and `TwinBinding` and the relations the diagram
draws: `represents` (range left open for `ProductInstance`, `Station`, `Module`),
`usesEventStream`, `hasExecutionHistory`, `hasTwinBinding`, and on the binding the
datatype properties `platform` (a literal) and `mapsTo` (an `xsd:anyURI`, for example a
DTDL model identifier). `exposesService` is declared in `core/maas.ttl` with its
domain left open, because a service offer and a digital twin both point at a
`SkillService`. A digital twin is not another station or module: it represents a core
entity, and execution stays attached to the module.

The remaining `experimental-extensions/` files realise the extension points the diagram names for
standards in the MAESTRO standards basis: `opcua`, `rest` and `dtdl` on Binding,
`isa88` on Station and Recipe, `isa95` on Recipe, `automationml` on Module, `prov` on
SkillExecution, `odrl` on Policy. `docs/03-standards-basis.md` lists what each one
states.

## Design boundary against MAESTRO 1.0

This package is a projection of MAESTRO 1.0, not a replacement. MAESTRO 1.0 has the
following, and this package does not:

| MAESTRO 1.0 | Where | Not here because |
|---|---|---|
| Process taxonomy (DIN 8580, VDI 2860 groups) | `ontologies/logical/process.ttl` | HHM plans with recipes and skills, not process classes |
| Capability reasoning chain (capability properties, feasibility and eligibility assessments, claims) | `ontologies/logical/capability.ttl`, `ontologies/reasoning/assessment.ttl`, `claim.ttl`, `reasoning.ttl`, `adaptation.ttl` | HHM has a bare `Capability`; `requiresCapability` and `providesCapability` are the only edges |
| Execution adapters: PLC programs, distributed function blocks, ROS, AAS | `ontologies/execution/iec61131.ttl`, `iec61499.ttl`, `ros.ttl`, `aas.ttl` | Only OPC UA, REST and DTDL are named by the HHM diagram and pinned in the standards basis |
| Quality, LCA, security, digital product passport, discovery | `ontologies/cross-cutting/quality.ttl`, `lca.ttl`, `security.ttl`, `dpp.ttl`, `discovery.ttl` | Not in the HHM clusters; DPP is a hook only |
| Planning beyond production orders (work orders, schedules, the ISA-95 activity model) | `ontologies/reasoning/planning.ttl` | Only `ProductionOrder` and the equipment hierarchy are carried (`core/maas.ttl`, `experimental-extensions/isa95.ttl`) |
| Units and quantities | `ontologies/cross-cutting/unit.ttl` | Removed by decision; `unitRef` holds a QUDT IRI |
| Sensors and observations | `ontologies/cross-cutting/sensor.ttl` | Removed by decision; SOSA remains a hook |
| Agents, deployments, traceability, motion, the skill / product / motion libraries, term status annotations and change records | `ontologies/logical/agent.ttl`, `deployment.ttl`, `ontologies/execution/trace.ttl`, `ontologies/physical/motion.ttl`, `ontologies/lib/` | Outside the HHM scope |

`ontologies/` remains the governed source and is not modified by this package.

## How the layers depend on each other

The import graph is a directed acyclic graph rooted at `core/resource.ttl`, which also
declares the shared datatype properties `description`, `version`, `manufacturer`,
`model`, `serialNumber` and `location`, and the kind of every external term the
package uses (`docs/02-conventions.md`, "External terms").

Core:

- `skill` imports `resource`.
- `recipe` imports `skill`.
- `product` imports `recipe` (for `requiresOperation` to a plan step).
- `invocation` imports `skill`.
- `policy` imports `skill` and `recipe`.
- `execution` imports `skill`, `recipe` (for `realizesStep` to a plan step) and `invocation`.
- `maas` imports `product`, `invocation` and `policy`. It sits in `core/` but is not an HHM cluster.

MAESTRO additions (in `experimental-extensions/`):

- `runtime` imports `execution` and `policy` (the mode dimension reuses the `OperatingMode` individuals).
- `energy` imports `resource` and `execution` (measurements span a `TimeInterval`).
- `maintenance` imports `resource`, `execution` (actions are triggered by a `Fault`) and `policy` (return-to-service evidence).

Extension points (in `experimental-extensions/`):

- `digital-twin` imports `product` and `execution`.
- `opcua`, `dtdl` and `rest` import `invocation`.
- `isa88` imports `recipe` and `resource`.
- `isa95` and `automationml` import `resource`.
- `prov` imports `execution` and `runtime`.
- `odrl` imports `policy`.

The umbrella imports all twenty modules and nothing else. The generated files under
`alignment/` import the umbrella and are not imported by it, so loading the umbrella
never pulls in the `hhm:` placeholder namespace or the MAESTRO 1.0 match set. Each use
case has its own umbrella file, which imports that use case's module files under `core/`
and `ext/`; each of those imports the MAESTRO module of the same name.

The load order used by the tools is the one in `tools/common.py` (`MODULES`): the eight
core files in the order above, then `runtime`, `energy`, `maintenance`, then the
nine extension-point files, all twelve under `experimental-extensions/`.
