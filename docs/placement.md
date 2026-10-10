# Placement of the nine MAESTRO modules

The user asked for nine MAESTRO 1.0 modules to be checked and either folded into an
HHM cluster or added as modules of this package. This page records where each one
went, what was kept, what was dropped and why. Source files are under `ontologies/` at
the repository root and are not modified. Term names below are the MAESTRO 1.0 local
names; in this package they are `maestro:` terms with the same local name unless stated.

## Summary

| MAESTRO file | Decision | Target | Kept | Dropped |
|---|---|---|---|---|
| `cross-cutting/communication.ttl` | Fold in | `core/invocation.ttl` | Endpoint, Protocol, Binding, EventStream, OperationSignature, DataFormat (4 individuals), InterfaceDescriptionLanguage (4 individuals), 7 Protocol individuals, address, port, hasSignature, hasParameterDef, returns, specializesAs, usesDataFormat, describedIn, exposedVia, usesProtocol, hasBinding, emitsStream (as `maestro:emits`); WADL matches | Channel, hasEndpoint, bindsEndpoint, DtdlProtocol, conformsToStream |
| `cross-cutting/safety.ttl` | Fold in | `core/policy.ttl` | SafetyFunction, EmergencyStop, SafetyIntegrityLevel (SIL1-4), PerformanceLevel (PLa-e), RiskLevel (Low / Medium / High), RiskAssessment; Hazard, Risk, Mitigation, increases, reduces (already HHM terms); mitigates, requiredSIL, achievedSIL, requiredPerformanceLevel, achievedPerformanceLevel, assessedSubject, assessesRisk, identifiesHazard, reliesOnMitigation, riskLevel, riskEvidence, riskAssessmentMethod, assumption | deprecated hasSIL, hasPerformanceLevel |
| `runtime/runtime.ttl` | Split | `core/execution.ttl` and `modules/telemetry.ttl` | Core: SkillExecution, TimeInterval, Fault (from FaultEvent), ExecutionStatus and its values, executes, executedOn, invokedVia, hasInput, hasStatus, mayRaise (from raisedFault), hasTime, startTime, endTime, faultCode, faultCause, faultSeverity, timestamp. Module: State (+ Available, Busy, FaultState, Alarm, Healthy, Degraded, Failed, Reserved), StateDimension (4 individuals), StateAssertion, TelemetryEvent (from RuntimeEvent), StateTransition, FaultSpecification, ExecutionRecord, Snapshot; hasState, inDimension, stateSubject, stateDimension, stateValue, stateEvidence, eventSubject, fromState, enteredState, mayRaiseFault, instanceOfFault, describesExecution; validFrom, validTo, observedAt, recordedAt, snapshotTaken | performedBy, recordedBy |
| `cross-cutting/unit.ttl` | Removed (user decision) | none | nothing | Unit, Quantity, hasUnit, numericValue, symbol, baseUnit, conversionFactor, conversionOffset, all unit individuals, the QUDT bridge |
| `cross-cutting/energy.ttl` | New module | `modules/energy.ttl` | EnergyConsumer (subclass of Module), EnergyMeasurement, PowerMeasurement, EnergySource (4 individuals); suppliedBy, measuredSubject, overInterval; energyKwh, powerWatts, carbonGCO2eqPerKwh | energyValue, powerValue (Quantity-valued) |
| `cross-cutting/maintenance.ttl` | New module | `modules/maintenance.ttl` | all 12 classes; hasTask, planForAsset, performsTask, affectsAsset, triggeredBy, hasFinding, assessesWork, rtsOutcome, rtsEvidence; scheduledFor, performedAt, findingDescription, mtbfHours, remainingUsefulLifeHours; 3 outcome individuals; added diagnosesFault | nothing (Inspection keeps one parent) |
| `logical/maas.ttl` | New module | `modules/maas.ttl` | Actor, Customer, PhysicalResourceProvider, Marketplace, ServiceOffer, ServiceRequest, Quote, Contract; CustomerRole, ProviderRole, MarketplaceRole; offeredBy, offersCapability, providedAt, listedOn, exposesService, requestedBy, forProduct, quoteFor, basedOnOffer, acceptsQuote, governedBy, realizedByOrder, operates, operatedBy; requestedQuantity, submittedOn, maxQuantity, price, currency, validUntil; schema.org matches; added ProductionOrder (from `reasoning/planning.ttl`) with ordersProduct, executesRecipe, quantity, dueDate; leadTimeDays, maxLeadTimeDays | fulfilledByProcess, locatedAt (Actor gets `maestro:location` literal), Organization / Enterprise parents, Quantity-valued leadTime and maxLeadTime |
| `cross-cutting/sensor.ttl` | Removed (user decision) | none | nothing | Sensor, Observation, ObservableProperty, FeatureOfInterest, hasObservationEvidence, the SOSA bridge |
| `execution/opcua.ttl` | Realises an extension point | `ext/opcua.ttl` | OpcUaServer, OpcUaNode, OpcUaObject, OpcUaVariable, OpcUaMethod, OpcUaSkillInterface; nodeId, browseName; hostsInterface, exposes, implementsSkill; HSU OPC UA matches; added OpcUaBinding, hostedOn, bindsMethod | accessibleThrough |

## Per file

### `cross-cutting/communication.ttl` -> folded into `core/invocation.ttl`

The HHM Invocation Hooks cluster already names Endpoint, Protocol and Binding, and the
digital-twin diagram adds SkillService and EventStream. The MAESTRO communication
module describes the same layer in more detail, so its remaining terms were folded into
the same file rather than kept apart: `OperationSignature` (an operation with its
parameter definitions and return schema, declared through `hasSignature`,
`hasParameterDef` and `returns`), `DataFormat` with the individuals `JsonFormat`,
`XmlFormat`, `ProtobufFormat` and `OpcUaBinaryFormat` (via `usesDataFormat`), and
`InterfaceDescriptionLanguage` with `OpcUaNodeSetIDL`, `DtdlIDL`,
`AasSubmodelTemplateIDL` and `OpenApiIDL` (via `describedIn`). The seven protocol
individuals `OpcUaProtocol`, `DdsProtocol`, `MqttProtocol`, `ProfinetProtocol`,
`EthercatProtocol`, `ModbusProtocol` and `HttpProtocol` are plain names of technologies.
They were later moved out of the core into one extension module per protocol
(`ext/opcua.ttl`, `ext/rest.ttl` for HTTP, `ext/mqtt.ttl`, `ext/dds.ttl`,
`ext/modbus.ttl`, `ext/profinet.ttl`, `ext/ethercat.ttl`), each also declaring a binding
for its protocol; the umbrella keeps the `owl:AllDifferent` over the seven.
The data-format and interface-language individuals followed the same way:
`OpcUaBinaryFormat` and `OpcUaNodeSetIDL` to `ext/opcua.ttl`, `DtdlIDL` to
`ext/dtdl.ttl`, `OpenApiIDL` to `ext/rest.ttl`, `AasSubmodelTemplateIDL` to
`ext/digital-twin.ttl`, and `JsonFormat`, `XmlFormat` and `ProtobufFormat` to the new
`ext/data-formats.ttl`; their two `owl:AllDifferent` axioms are in the umbrella too.
`address` and `port` sit on the endpoint; they were later moved, with a binding-level
`topic`, to `ext/addressing.ttl`, which every protocol module imports; `specializesAs` lets a protocol-neutral
binding name the `Protocol` individual it specialises to. `emitsStream` became
`maestro:emits`, the name the HHM diagram uses. The three WADL matches (`OperationSignature`
close to `WADL:Method`, `Endpoint` and `DataFormat` related to `WADL:Resource` and
`WADL:Representation`) were kept because WADL is pinned.

Dropped: `Channel` (a communication channel between endpoints; the HHM diagram has no
such node, and the binding plus endpoint pair covers the use), `hasEndpoint` and
`bindsEndpoint` (replaced by the HHM edges `exposedVia` and `hasBinding`),
`DtdlProtocol` (DTDL is an interface description language, not a wire protocol; it is
`maestro:DtdlIDL` here) and `conformsToStream` (stream schemas are out of scope).

### `cross-cutting/safety.ttl` -> folded into `core/policy.ttl`

The HHM Safety / Security / Policy cluster carries Hazard, Risk and Mitigation with
`increases` and `reduces`. The MAESTRO safety module adds what an integrator records
about functional safety, so all of it went into the same cluster file: `SafetyFunction`
and its subclass `EmergencyStop`; the declared levels `SafetyIntegrityLevel` (`SIL1` to
`SIL4`) and `PerformanceLevel` (`PLa` to `PLe`) with `requiredSIL`, `achievedSIL`,
`requiredPerformanceLevel` and `achievedPerformanceLevel`; `mitigates` from a safety
function to a hazard; `RiskLevel` with `LowRisk`, `MediumRisk`, `HighRisk`; and
`RiskAssessment` with `assessedSubject`, `assessesRisk`, `identifiesHazard`,
`reliesOnMitigation`, `riskLevel`, `riskEvidence`, `riskAssessmentMethod` and
`assumption`. The module header states that levels are declared by the integrator and
that the ontology neither defines nor verifies them.

Dropped: `hasSIL` and `hasPerformanceLevel`, which MAESTRO 1.0 already marks
`owl:deprecated true` in favour of the required / achieved pairs.

### `runtime/runtime.ttl` -> split between `core/execution.ttl` and `modules/telemetry.ttl`

The HHM Minimal Execution cluster is exactly four nodes: SkillExecution,
ExecutionStatus, Fault, TimeInterval, with the seven edges the diagram draws. Those went
to `core/execution.ttl`, taking their definitions from the MAESTRO runtime module.
`maestro:Fault` is the occurrence (MAESTRO calls it `FaultEvent` and uses `Fault` for the
state value, which is `maestro:FaultState` here); `maestro:mayRaise` is the HHM name for
`raisedFault`. `timestamp` is declared in core with an open domain because faults,
runtime events and power measurements all carry one.

Everything MAESTRO says about the live state of a resource has no HHM node, so it
became `modules/telemetry.ttl`: `State` with the values `Available`, `Busy`, `FaultState`,
`Alarm`, `Healthy`, `Degraded`, `Failed`, `Reserved`; `StateDimension` with
`OperationalDimension`, `HealthDimension`, `ReservationDimension`, `ModeDimension`;
qualified `StateAssertion` (`stateSubject`, `stateDimension`, `stateValue`,
`validFrom`, `validTo`, `observedAt`, `stateEvidence`); `TelemetryEvent` (MAESTRO 1.0
`RuntimeEvent`) and
`StateTransition` (`eventSubject`, `fromState`, `enteredState`);
`FaultSpecification` (`mayRaiseFault` from a skill, `instanceOfFault` from an
occurrence); `ExecutionRecord` (`describesExecution`, `recordedAt`); and `Snapshot`
(`snapshotTaken`). The module declares `maestro:ExecutionStatus rdfs:subClassOf maestro:State`
so `Idle`, `Executing`, `Held`, `Completed` and `Aborted` exist once, in core, and
serve as both an execution status and a state value. The PackML close matches on those
four MAESTRO states were kept.

Dropped: `performedBy` (needs the agent module, which is not carried) and `recordedBy`
(same reason).

### `cross-cutting/unit.ttl` -> removed

Removed by user decision. The package has no `Unit` or `Quantity` class, no `hasUnit`,
`numericValue`, `symbol`, `baseUnit`, `conversionFactor` or `conversionOffset`, and no
unit individuals. Consequences applied throughout: `maestro:unitRef` on `maestro:ParameterDef` is
a datatype property of range `xsd:anyURI` holding a QUDT unit IRI (the example uses
`http://qudt.org/vocab/unit/MilliM`); the quantity-valued properties `energyValue`,
`powerValue`, `leadTime` and `maxLeadTime` were dropped in favour of the bare numeric
properties `energyKwh`, `powerWatts`, `leadTimeDays` and `maxLeadTimeDays`, whose unit
is fixed by the name. QUDT remains a pinned reference but is not pointed at.

### `cross-cutting/energy.ttl` -> new module `modules/energy.ttl`

Energy is not an HHM cluster, so it is a module. `EnergyConsumer` is a subclass of
`maestro:Module` (MAESTRO ranges on `core:Resource` became `maestro:Module`, the only physical
class an execution attaches to); a module is typed additionally as an energy consumer
to record its supply through `suppliedBy` to an `EnergySource` (`ElectricalGrid`,
`Solar`, `Wind`, `CompressedAir`, each with `carbonGCO2eqPerKwh`). `EnergyMeasurement`
carries `energyKwh` over a `maestro:TimeInterval` (`overInterval`); `PowerMeasurement`
carries `powerWatts` and a `timestamp` and no interval. `measuredSubject` has domain and
range left open so a module, a station or an execution can be measured.

Dropped: `energyValue` and `powerValue`, which pointed at unit-module quantities.

### `cross-cutting/maintenance.ttl` -> new module `modules/maintenance.ttl`

Maintenance is not an HHM cluster, so it is a module, and it was carried whole: the
twelve classes `MaintenanceAction`, `Preventive`, `Corrective`, `ConditionBased`
(subclass of `Preventive`), `Predictive` (subclass of `ConditionBased`), `Inspection`,
`FaultDiagnosis`, `MaintenancePlan`, `MaintenanceTask`, `Finding`,
`ReturnToServiceAssessment` and `ReturnToServiceOutcome` (`Cleared`,
`ConditionallyCleared`, `NotCleared`); the properties `hasTask`, `planForAsset`,
`performsTask`, `affectsAsset`, `triggeredBy`, `hasFinding`, `assessesWork`,
`rtsOutcome`, `rtsEvidence`, `scheduledFor`, `performedAt`, `findingDescription`;
and `mtbfHours` and `remainingUsefulLifeHours` with domain `maestro:Module`. Three changes:
`Inspection` is a subclass of `MaintenanceAction` only; `triggeredBy` and the new
`diagnosesFault` (from a `FaultDiagnosis`) point at the core `maestro:Fault`, so a corrective
action and its diagnosis link to the fault occurrence that caused them;
`planForAsset` and `affectsAsset` range over `maestro:Module`. An action takes its duration
from `maestro:hasTime` to a `maestro:TimeInterval`.

### `logical/maas.ttl` -> new module `modules/maas.ttl`

Manufacturing as a service is the market tier above the HHM clusters, so it is a
module. Carried: `Actor` with `Customer`, `PhysicalResourceProvider` and `Marketplace`
(not disjoint: one party may buy on one order and sell on the next), the three
`maestro:Role` individuals `CustomerRole`, `ProviderRole`, `MarketplaceRole`, and the chain
`ServiceOffer` (`offeredBy`, `offersCapability`, `providedAt` a `maestro:Station`,
`listedOn`, `exposesService`, `maxQuantity`, `leadTimeDays`) -> `ServiceRequest`
(`requestedBy`, `forProduct`, `requestedQuantity`, `submittedOn`, `maxLeadTimeDays`) ->
`Quote` (`quoteFor`, `basedOnOffer`, `price`, `currency`, `validUntil`) -> `Contract`
(`acceptsQuote`, `governedBy`, `realizedByOrder`). `operates` / `operatedBy` relate an
actor and a station. The five schema.org close matches were kept. `ProductionOrder` was
added from the MAESTRO planning module so a contract can be realised by an order that
`ordersProduct` a `maestro:ProductType`, `executesRecipe` a `maestro:Recipe`, and carries
`quantity` (the product cluster property, domain left open) and `dueDate`; it keeps the
ISO 22400-2 close match.

Dropped: `fulfilledByProcess` (no process module), `locatedAt` to a site (the actor
gets the free-text `maestro:location` literal declared in `core/resource.ttl`; the ISA-95
site is a separate extension), the `Organization` / `Enterprise` superclasses (agent and
planning modules are not carried), and the quantity-valued `leadTime` / `maxLeadTime`
(no unit module; replaced by `leadTimeDays` / `maxLeadTimeDays`).

### `cross-cutting/sensor.ttl` -> removed

Removed by user decision. `Sensor`, `Observation`, `ObservableProperty`,
`FeatureOfInterest`, `hasObservationEvidence` and the SOSA bridge are not included. The
SOSA/SSN extension point on `maestro:Skill` stays a documented hook in the `core/skill.ttl`
header; no `sosa:` IRI appears in the package. Evidence is recorded with `maestro:Evidence`,
readings with the energy module.

### `execution/opcua.ttl` -> realises the extension point in `ext/opcua.ttl`

The HHM diagram names OPC UA as an extension point on Binding, so the MAESTRO OPC UA
module became an `ext/` file. Carried: `OpcUaServer`, `OpcUaNode` with its subclasses
`OpcUaObject`, `OpcUaVariable` and `OpcUaMethod`, and `OpcUaSkillInterface` (a subclass
of both `OpcUaObject` and `maestro:SkillInterface`); `nodeId` and `browseName`;
`hostsInterface` (server to interface), `exposes` (interface to skill) and
`implementsSkill` (method to skill); the five HSU OPC UA close matches. Added:
`OpcUaBinding` as a subclass of `maestro:Binding`, which is what makes the file an HHM
extension rather than a stand-alone model, with `bindsMethod` to the method it invokes;
and `hostedOn` from a server to the `maestro:Module` it runs on.

Dropped: `accessibleThrough`, whose role is taken by the HHM invocation path
service -> interface -> endpoint -> binding -> signature.
