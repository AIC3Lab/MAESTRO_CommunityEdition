# 03 - Standards basis

The package follows the MAESTRO rule from CHG-023 (`docs/04-standard-alignment.md` and
`references/README.md` at the repository root): a link to an external term is allowed
only when that term exists in a pinned copy under `references/`. `tools/validate.py`
gate 7 checks every `skos:*Match`, `rdfs:subClassOf`, `rdfs:subPropertyOf` and
`owl:equivalent*` target outside `maestro:` against those files, using the MAESTRO
`tests/mapping_register.py` vocabulary table. No upstream ontology is imported; the
pinned copies serve verification only.

Two kinds of link are used:

- **Documentary**: `skos:closeMatch`, `skos:relatedMatch`, `skos:broadMatch`. No
  logical consequence. Where meanings differ, the `maestro:` term carries a `skos:scopeNote`
  or an `rdfs:comment` saying how.
- **Logical bridge**: `rdfs:subClassOf` / `rdfs:subPropertyOf` to the external term.
  Only in `ext/prov.ttl` and `ext/odrl.ttl`, mirroring the axioms MAESTRO 1.0 makes in
  its default stack.

## Vocabularies referenced at 0.1.0

| Vocabulary | Pinned file under `references/` | Module | Kind | Links |
|---|---|---|---|---|
| PackML (HSU-AUT ODP), prefix `PackML:` `http://www.w3id.org/hsu-aut/PackML#` | `hsu-packml.ttl` | `core/execution.ttl` | documentary | `maestro:Idle` closeMatch `PackML:Idle`; `maestro:Executing` closeMatch `PackML:Execute`; `maestro:Held` closeMatch `PackML:Held`; `maestro:Completed` closeMatch `PackML:Complete`; `maestro:Aborted` closeMatch `PackML:Aborted` |
| WADL (HSU-AUT ODP), `WADL:` `http://www.w3id.org/hsu-aut/WADL#` | `hsu-wadl.ttl` | `core/invocation.ttl` | documentary | `maestro:Endpoint` relatedMatch `WADL:Resource`; `maestro:OperationSignature` closeMatch `WADL:Method`; `maestro:DataFormat` relatedMatch `WADL:Representation` |
| WADL (HSU-AUT ODP) | `hsu-wadl.ttl` | `ext/rest.ttl` | documentary | `maestro:RestInterface` relatedMatch `WADL:Resource`; `maestro:RestBinding` closeMatch `WADL:Method` |
| DIN EN 61360 (HSU-AUT ODP), `DINEN61360:` `http://www.w3id.org/hsu-aut/DINEN61360#` | `hsu-dinen61360.ttl` | `core/product.ttl` | documentary | `maestro:Requirement` closeMatch `DINEN61360:Instance_Description` |
| VDI 2206 (HSU-AUT ODP), `VDI2206:` `http://www.w3id.org/hsu-aut/VDI2206#` | `hsu-vdi2206.ttl` | `core/resource.ttl` | documentary | `maestro:Module` closeMatch `VDI2206:Module` |
| schema.org, `schema:` `https://schema.org/` | `schemaorg-extract.ttl` | `modules/maas.ttl` | documentary | `maestro:Actor` closeMatch `schema:Organization`; `maestro:ServiceOffer` closeMatch `schema:Offer`; `maestro:ServiceRequest` closeMatch `schema:Demand`; `maestro:Quote` closeMatch `schema:PriceSpecification`; `maestro:Contract` closeMatch `schema:Order` |
| ISO 22400-2 (HSU-AUT ODP), `ISO22400:` `http://www.w3id.org/hsu-aut/ISO22400-2#` | `hsu-iso22400-2.ttl` | `modules/maas.ttl` | documentary | `maestro:ProductionOrder` closeMatch `ISO22400:ProductionOrder` |
| ISA-88.01 (HSU-AUT ODP), `ISA88:` `http://www.hsu-ifa.de/ontologies/ISA88.01#` | `hsu-isa88.ttl` | `ext/isa88.ttl` | documentary | `maestro:Recipe` closeMatch `ISA88:RecipeProcedure`; `maestro:PlanStep` closeMatch `ISA88:Phase`; `maestro:Station` closeMatch `ISA88:Unit`; `maestro:Module` closeMatch `ISA88:EquipmentModule`; each with a `skos:scopeNote` |
| DIN EN 62264-2 / ISA-95 (HSU-AUT ODP), `DINEN62264:` `http://www.w3id.org/hsu-aut/DINEN62264-2#` | `hsu-dinen62264-2.ttl` | `ext/isa95.ttl` | documentary | `maestro:Enterprise`, `maestro:Site`, `maestro:Area`, `maestro:WorkCenter`, `maestro:WorkUnit` closeMatch `DINEN62264:Enterprise`, `Site`, `Area`, `Work_Center`, `Work_Unit`; `maestro:partOfEnterprise`, `maestro:partOfSite`, `maestro:partOfArea`, `maestro:partOfWorkCenter` closeMatch `DINEN62264:SiteIsPartOfEnterprise`, `AreaIsPartOfSite`, `CenterIsPartOfArea`, `UnitIsPartOfCenter` |
| OPC UA (HSU-AUT ODP), `OpcUa:` `http://www.w3id.org/hsu-aut/OpcUa#` | `hsu-opcua.ttl` | `ext/opcua.ttl` | documentary | `maestro:OpcUaServer`, `maestro:OpcUaNode`, `maestro:OpcUaObject`, `maestro:OpcUaVariable`, `maestro:OpcUaMethod` closeMatch `OpcUa:UAServer`, `UANode`, `UAObject`, `UAVariable`, `UAMethod` |
| AutomationML (HSU-AUT ODP), `AML:` `https://w3id.org/hsu-aut/AutomationML#` | `hsu-automationml.ttl` | `ext/automationml.ttl` | documentary | `maestro:InternalElement` relatedMatch `AML:InternalElement` (the ODP term is the CAEX model element, ours the plant element); `maestro:ExternalInterface` closeMatch `AML:ExternalInterface`; `maestro:InternalLink` closeMatch `AML:InternalLink` |
| DTDL v3 (Azure/opendigitaltwins-dtdl), full `dtmi:` IRIs | `dtdl-v3-classes.ttl` | `ext/dtdl.ttl` | documentary | `maestro:DtdlInterface`, `maestro:DtdlCommand`, `maestro:DtdlTelemetry`, `maestro:DtdlProperty` closeMatch `<dtmi:dtdl:class:Interface;3>`, `<dtmi:dtdl:class:Command;3>`, `<dtmi:dtdl:class:Telemetry;3>`, `<dtmi:dtdl:class:Property;3>` |
| W3C PROV-O, `prov:` `http://www.w3.org/ns/prov#` | `prov-o.ttl` | `ext/prov.ttl` | logical bridge (and one documentary) | `maestro:SkillExecution` subClassOf `prov:Activity`; `maestro:executes`, `maestro:hasInput`, `maestro:executedOn` subPropertyOf `prov:used`; `maestro:startedAtTime` subPropertyOf `prov:startedAtTime`; `maestro:endedAtTime` subPropertyOf `prov:endedAtTime`; `maestro:ExecutionRecord` broadMatch `prov:Entity` |
| W3C ODRL 2.2 core profile, `odrl:` `http://www.w3.org/ns/odrl/2/` | `odrl-core-profile-22.ttl` | `ext/odrl.ttl` | logical bridge (and one documentary) | `maestro:Policy` subClassOf `odrl:Policy`; `maestro:Permission` subClassOf `odrl:Permission`; `maestro:hasPermission` subPropertyOf `odrl:permission`; `maestro:action` subPropertyOf `odrl:action`; `maestro:target` subPropertyOf `odrl:target`; `maestro:Action` closeMatch `odrl:Action` |

Notes on the table:

- The `maestro:Action` individuals `Invoke`, `Read`, `Write`, `Configure` carry no ODRL
  mapping: `odrl:execute`, `odrl:read` and `odrl:modify` belong to the ODRL Common
  Vocabulary, which is not in the pinned core profile.
- `maestro:hasTime` (object property to a `maestro:TimeInterval`) is not a sub-property of the
  PROV-O time properties, which are datatype properties; `ext/prov.ttl` adds the two
  datatype aliases `maestro:startedAtTime` and `maestro:endedAtTime` on the execution instead.
- `ext/isa88.ttl` declares no class or property of its own; it holds only the four
  matches and their scope notes. `ext/odrl.ttl` likewise declares no term.
- The DTDL identifiers are written as full IRIs in angle brackets because `dtmi:` is
  not a namespace prefix.
- `maestro:Recipe` is close to, not the same as, `ISA88:RecipeProcedure`: the ODP orders
  procedural children through list cells, this package through `maestro:stepOrder` and
  control-flow constraints. `maestro:Station` does not adopt the ISA-88 presumption that a
  unit processes one batch at a time.

Two more targets appear in generated files only and are outside the rule:

| Target | File | Kind |
|---|---|---|
| HHM-Core v1 placeholder namespace `hhm:` `https://w3id.org/hhm-core#` (project reference model, not a standard; exempt from CHG-023) | `alignment/hhm-core.ttl` (generated) | `owl:equivalentClass` / `owl:equivalentProperty`, with `skos:closeMatch` for the documented design differences |
| MAESTRO 1.0 terms `https://w3id.org/maestro/<module>#` | `alignment/maestro-1.0.ttl` (generated from `dct:source` / `dct:references`) | `skos:exactMatch` / `skos:closeMatch` |

Gate 7 allows `hhm:` only in `alignment/hhm-core.ttl`.

## Hooks: named, not mapped

The HHM diagram names further standards and vocabularies as extension points. None of
them is published in one of the repositories listed in `references/README.md`, so the
package does not point at them. **Hooks carry no IRIs and no mappings: they are named
in module comments only, and gate 7 fails if one of these names appears next to an IRI
or a match predicate in any `.ttl` file.** Naming a technology (for example as a
protocol or interface-description-language individual) is not a conformance claim.

| Hook | Named in | Where it would attach |
|---|---|---|
| ECLASS / eClassOWL | `core/product.ttl` header | a semanticId on `maestro:Feature` and `maestro:ParameterDef` |
| DPP / DPPO / RePlanIT digital product passport | `core/product.ttl` header | a passport view over `maestro:ProductType` / `maestro:ProductInstance` |
| PRONTO | `core/product.ttl` header | variant and bill-of-materials semantics |
| CaSkMan / CSS capability-skill patterns | `core/skill.ttl` header | `maestro:Capability` and `maestro:Skill` |
| AAS (Asset Administration Shell) | `core/invocation.ttl` header, `ext/digital-twin.ttl` header | submodel publication of a skill interface; `maestro:mapsTo` on a twin binding stays a plain IRI. The individual `maestro:AasSubmodelTemplateIDL`, declared in `ext/digital-twin.ttl`, is a plain name of the technology |
| OpenAPI | `ext/rest.ttl` header | REST interface description; the individual `maestro:OpenApiIDL`, declared in `ext/rest.ttl`, is a plain name. WADL is the REST description in the basis |
| SAREF4INMA | `core/execution.ttl` header | traceability of executions and items |
| XACML | `core/policy.ttl`, `ext/odrl.ttl` headers | rule and policy languages beyond the ODRL core profile |

Two vocabularies are pinned under `references/` but not referenced, because the
modules that would use them were removed (next section):

| Vocabulary | Pinned file | Position |
|---|---|---|
| QUDT (`qudt-extract.ttl`) | `references/qudt-extract.ttl` | extension point on `maestro:ParameterDef`: `maestro:unitRef` holds a QUDT unit IRI as an `xsd:anyURI` literal; no `qudt:` IRI appears in the ontology |
| SOSA/SSN (`sosa.ttl`) | `references/sosa.ttl` | extension point on `maestro:Skill` for observation evidence; no `sosa:` IRI appears in the ontology |

## The two removed modules

**Unit** (`ontologies/cross-cutting/unit.ttl`: `Unit`, `Quantity`, `hasUnit`,
`numericValue`, `symbol`, `baseUnit`, `conversionFactor`, `conversionOffset`, the QUDT
bridge) is not included. Consequences:

- `maestro:unitRef` is a datatype property with range `xsd:anyURI`; its value is a QUDT unit
  IRI (`"http://qudt.org/vocab/unit/MilliM"^^xsd:anyURI` in the example). There are no
  unit individuals to point at.
- Numeric properties carry the unit in their name: `maestro:energyKwh`, `maestro:powerWatts`,
  `maestro:carbonGCO2eqPerKwh`, `maestro:leadTimeDays`, `maestro:maxLeadTimeDays`, `maestro:mtbfHours`,
  `maestro:remainingUsefulLifeHours`.
- The MAESTRO 1.0 quantity-valued object properties `energy:energyValue`,
  `energy:powerValue`, `maas:leadTime` and `maas:maxLeadTime` have no counterpart here.
- A consumer that needs unit conversion resolves the `unitRef` IRI against QUDT outside
  this ontology.

**Sensor** (`ontologies/cross-cutting/sensor.ttl`: `Sensor`, `Observation`,
`ObservableProperty`, `FeatureOfInterest`, `hasObservationEvidence`, the SOSA bridge)
is not included. Consequences:

- No observation class exists; evidence for a state assertion or a policy is an
  `maestro:Evidence` with `maestro:evidenceRef`, and a power or energy reading is an
  `maestro:PowerMeasurement` or `maestro:EnergyMeasurement` of the energy module.
- The SOSA/SSN extension point on `maestro:Skill` stays documented in the `core/skill.ttl`
  header; a deployment that models sensors adds SOSA alongside this package rather than
  through it.
