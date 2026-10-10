# LTU Festo MPS line (HHM-Core)

The LTU use case as a MAESTRO HHM-Core knowledge graph: a four-station Festo
Didactic **Modular Production System (MPS)** line, Distributing → Testing →
Processing → Handling. The T-box is the HHM-Core package
(`https://w3id.org/maestro/hhm`, prefix `maestro:`); these files are its A-box.

**The graphs contain document data only.** Every module, component, part number,
signal, step and limit comes from the Festo documents of the use case. Where they
give no value (a PLC address, a stroke, a maintenance interval, a network address)
none is invented; the gap is stated in `maestro:description` and listed under
[open data items](#open-data-items). Inferences that combine documents say
"inferred" in their description.

## Sources

| Station | Documents |
|---|---|
| Distributing (VE, station 1) | `Distributing Station design documents/`: manual 648811 (DE/EN 04/06 R2.2), `01_Distributing_GRAFCET.pdf`, `Function.pdf`, `Function0.pdf`, `Changer.pdf` |
| Testing (PR, station 2) | `FESTO CD/02_Testing/`: manual 648812, electric and pneumatic circuit diagrams, parts list 526881, assembly instructions, data sheets, operating instructions, GRAFCET |
| Processing (BE, station 3) | `FESTO CD/03_Processing/`: manual 648813, electric circuit diagram, parts list 526882, assembly instructions (Processing, Drilling, Indexing table), data sheets, GRAFCET |
| Handling (HA, station 4) | `FESTO CD/04_Handling/`: manual 655633, electric and pneumatic circuit diagrams, parts list 526883, assembly instructions, data sheets, operating instructions, GRAFCET |

The Distributing documents do not include its circuit diagrams or parts list (the
manual points to CD-ROM 665871). So that station has no I/O addresses, BMKs or
quantities; its signals are named after the GRAFCET transitions and actions.

## Files

The layout is the standard one of the HHM-Core examples: `shared/shared.ttl`, then one
folder per production unit with `plant.ttl` (equipment, design time) and `product.ttl`
(what it makes and the recipes that make it). The four stations and the line are the
production units. There is no `market.ttl` (the documents describe no offer; LTU is the
operator, not a marketplace provider) and no `runtime.ttl` (no readings exist).

```
ltu-festo-mps/
  shared/shared.ttl          reference data all units share
  distributing/              station 1   plant.ttl  product.ttl
  testing/                   station 2   plant.ttl  product.ttl
  processing/                station 3   plant.ttl  product.ttl
  handling/                  station 4   plant.ttl  product.ttl
  line/                      the line    plant.ttl  product.ttl
```

| File | Content | Triples |
|---|---|---|
| [`shared/shared.ttl`](shared/shared.ttl) | LTU (`maestro:Enterprise`, `maestro:Actor`), site, lab, the MPS line (`maestro:WorkCenter`); 19 capabilities; protocols SysLink digital / analogue and StationLink; trainee and instructor roles; the shared safety rules, hazards, risks and mitigations; the four cleaning tasks; the **Festo component catalogue** (one `maestro:ProductType` + `maestro:Identifier` per part number) | 817 |
| [`distributing/plant.ttl`](distributing/plant.ttl) | Distributing station: modules, bill of materials, signals, I/O path, skills, safety, maintenance | 569 |
| [`distributing/product.ttl`](distributing/product.ttl) | Its GRAFCET control sequence as an `maestro:Recipe` | 167 |
| [`testing/plant.ttl`](testing/plant.ttl) | Testing station, incl. the analogue height value on XMA3 | 1 001 |
| [`testing/product.ttl`](testing/product.ttl) | Its GRAFCET control sequence (accept / reject branch) | 203 |
| [`processing/plant.ttl`](processing/plant.ttl) | Processing station, incl. the relay logic | 966 |
| [`processing/product.ttl`](processing/product.ttl) | Its GRAFCET control sequence with the three parallel branches and the orientation data bindings | 232 |
| [`handling/plant.ttl`](handling/plant.ttl) | Handling station | 874 |
| [`handling/product.ttl`](handling/product.ttl) | Its GRAFCET control sequence (black / red-silver branch) | 186 |
| [`line/plant.ttl`](line/plant.ttl) | The material and StationLink links between the stations | 33 |
| [`line/product.ttl`](line/product.ttl) | The workpiece and its red / silver / black variants, and the line recipe | 105 |

Import chain: `<unit>/product.ttl → <unit>/plant.ttl → shared/shared.ttl → umbrella`;
`line/plant.ttl` imports the four station plants and `line/product.ttl` imports
`line/plant.ttl` and the four station products, so loading `line/product.ttl` with
catalog support pulls in everything. Prefixes: `ltu:` (`…/ltu-festo-mps/shared#`),
`dis:`, `tes:`, `pro:`, `han:` (`…/ltu-festo-mps/<station>#`) and `lin:`
(`…/ltu-festo-mps/line#`). A unit's `plant.ttl` and `product.ttl` share its namespace;
the ontology IRIs are `…/<unit>` and `…/<unit>/product`.

The graphs declare **no class and no property**: everything is an instance of an `maestro:`
class linked by `maestro:` properties, plus `rdfs:label` and the `owl:Ontology` headers.

## Figures

Knowledge-graph figures of this use case are in [`examples/`](..), as PNG and SVG
(the SVG stays sharp at any zoom):

| Figure | What it shows |
|---|---|
| [`kg-ltu-overview.png`](../kg-ltu-overview.png) | The whole use case on one sheet, clustered by file: the LTU hierarchy and shared data, the four stations in line order with their modules, capabilities and counts, each station's cycle skill and GRAFCET recipe, the material and StationLink links between the stations, the line recipe and the workpiece |
| [`kg-ltu-distributing.png`](../kg-ltu-distributing.png), [`-testing`](../kg-ltu-testing.png), [`-processing`](../kg-ltu-processing.png), [`-handling`](../kg-ltu-handling.png), [`-line`](../kg-ltu-line.png) | The full graph of one production unit (`plant.ttl` + `product.ttl`): every individual in the cluster of the HHM-Core module that declares its class, its literal values, and every object-property link, as in `figures/artifact-graphs/png/kg-*.png`. Identifiers (bit, pin, BMK), pre- and postconditions are rows inside their owner; shared nodes are grey dashed |

The figures were generated from the Turtle files; they do not update when you edit them.

## How the documents become a graph

Every station `plant.ttl` has the same sections (station, technical data, modules, bill of
materials, signals, I/O path, skills, safety, maintenance); its `product.ttl` holds the
GRAFCET:

| Document content | HHM-Core |
|---|---|
| Station, order / material number | `maestro:Station` + `maestro:WorkUnit`, `maestro:partOfWorkCenter ltu:MPSLine`, `maestro:hasIdentifier` (manual order number, station material number); `ltu:LTU maestro:operates` it |
| Technical data (pressure, voltage, current, I/O count, capacities, angles) | `maestro:ParameterDef` + `maestro:DtdlProperty` on the station with `maestro:unitRef` (QUDT) and `maestro:minValue` / `maestro:maxValue` |
| Modules of the manual (Stack magazine, Lifting, Rotary indexing table, PicAlfa …), valve terminal, service unit, I/O terminal, PLC board, console, StationLink transmitter / receiver | `maestro:Module` with `maestro:providesCapability`; `maestro:EnergyConsumer` `maestro:suppliedBy maestro:CompressedAir` and / or the station's 24 V DC supply (`maestro:EnergySource`); the part number shared with the catalogue type |
| Parts list and component tables | `maestro:ProductType` "station (equipment type)" `maestro:hasBOM` → `maestro:BOMNode` per assembly → `maestro:hasPart` per component, with `maestro:refDesignator` = BMK, `maestro:quantity` and `maestro:nodeFor` the catalogue type |
| I/O allocation (circuit diagram) | One `maestro:ParameterDef` per signal: sensor = `maestro:Output` + `maestro:DtdlTelemetry`, actuator command = `maestro:Input` + `maestro:DtdlProperty`; three `maestro:Identifier`s for the terminal bit (`XMA2 bit` = I0…O7), the connector pin and the BMK |
| SysLink connectors XMA2, XMA3, XMG1 | `maestro:Endpoint` with `maestro:usesProtocol` and a `urn:ltu:festo-mps:<station>:<connector>` address (the cable is parallel wiring, so there is no network address); `maestro:DtdlInterface` per connector `maestro:exposedVia` it; one `maestro:SkillService` (the PLC program) exposes them |
| GRAFCET actions | One `maestro:AtomicSkill` per elementary action (eject, swivel, raise, measure, clamp, open gripper …) with its signals as `maestro:hasParameterDef`, `maestro:Precondition` / `maestro:Postcondition` written over the signal names, and the capability it needs; one `maestro:CompositeSkill` per station cycle (`DistributeWorkpiece`, `TestWorkpiece`, `ProcessWorkpiece`, `PickAndSortWorkpiece`) |
| GRAFCET chart (`product.ttl`) | `maestro:Recipe` `<station>:ControlSequence`; one `maestro:PlanStep` per step with an action, `maestro:stepOrder` = GRAFCET step number; each transition is an `maestro:ControlFlowConstraint` with `maestro:flowType` (`Precedes`, `Alternative` for OR-divergence, `Parallel` for the Processing fork, `Loop` for jumps back) and the transition condition as `maestro:expression`. Empty steps and flag-only steps are folded into the conditions ("via step 5") |
| GRAFCET timers, comparator thresholds | `maestro:ParameterDef` with `maestro:unitRef` SEC / V |
| Processing's "workpiece orientation" shift register | `maestro:DataBinding` from the check result (bit 1, `maestro:Output`) to the drilling and output steps (bits 2 and 3, `maestro:Input`) |
| Error lights MAG. EMPTY, WORKPIECE NOK | `maestro:FaultSpecification` with the lamp text as `maestro:faultCode`, raised by the cycle skill |
| Notes on safety | `ltu:MPSSafetyRules` (`maestro:Policy`) with eight `maestro:Constraint`s; trainees `maestro:Invoke` the cycle skills under instructor supervision; `maestro:Hazard` → `maestro:Risk` ← `maestro:Mitigation`; a console `maestro:EmergencyStop` per station ("if available", no performance level stated); the Testing safety light barrier B4 as `maestro:SafetyFunction` |
| Maintenance chapter | `maestro:MaintenancePlan` per station over its modules with the shared cleaning tasks (and the task notes from operating instructions); no interval is stated |
| Line (`line/`) | `plant.ttl`: `maestro:InternalLink`s between the stations' material ports and between each StationLink transmitter and the upstream station's receiver. `product.ttl`: the workpiece and `lin:MPSLineRecipe` with four steps realised by the station cycle skills |

A signal row of the Handling circuit diagram,

| Bit | XMA2 pin | BMK | Description |
|---|---|---|---|
| I6 | 19 | 3B1 | Werkstück ist nicht schwarz / Workpiece is not black |

becomes

```turtle
han:DI_NotBlack a maestro:ParameterDef , maestro:DtdlTelemetry ;
    rdfs:label "Workpiece is not black"@en ;
    maestro:description "Fibre-optic diffuse sensor in the gripper jaw; 1 = red or metallic, 0 = black (or no workpiece)."@en ;
    maestro:paramType "http://www.w3.org/2001/XMLSchema#boolean"^^xsd:anyURI ;
    maestro:parameterDirection maestro:Output ;
    maestro:hasIdentifier han:ID_DI_NotBlack_Bit ,     # "XMA2 bit" = "I6"
                     han:ID_DI_NotBlack_Pin ,     # "XMA2 pin" = "19"
                     han:ID_DI_NotBlack_BMK .     # BMK = "3B1"

han:StationIO a maestro:DtdlInterface ;
    maestro:hasTelemetry han:DI_NotBlack ;              # ... and the other 12 signals
    maestro:exposedVia han:XMA2 .                       # maestro:Endpoint, ltu:SysLinkDigitalIO
```

## What the graphs answer

`queries/ltu/` (row counts over the LTU graphs):

| Query | Question | Rows |
|---|---|---|
| `lq01-io-allocation.rq` | Every signal of every station: connector, bit, pin, BMK, direction, data type | 85 |
| `lq02-line-route.rq` | Which station can run each line step (the station whose modules provide every capability the step's skill requires), and the hand-over condition | 4 |
| `lq03-grafcet-sequences.rq` | Each station's GRAFCET: step, realising skills, transitions with flow type and condition | 73 |
| `lq04-station-bom.rq` | Each station's assemblies and components with BMK, quantity, part number and type code | 103 |

The generic competency questions in `queries/cq/` (station modules and capabilities,
composite skills, recipe steps, data bindings, product structure, bills of materials,
policy grants, hazards, invocation paths, maintenance plans) also return LTU rows.

## Modelling choices and their limits

- **Line order.** Distributing → Testing → Processing → Handling follows the Festo
  station numbering (1-4). The combination matrices allow exactly these neighbours,
  but the LTU layout itself is not in the documents. The material and StationLink
  links in `line/plant.ttl` rest on this order. Handling is taken as the last
  station: sorting onto its two slides, not passing workpieces on.
- **Modules and components.** The manual's modules (and the valve terminal, service
  unit, I/O terminal, PLC board, console and StationLink parts) are `maestro:Module`s.
  Sensors, cylinders and valves are not modules: they are the `maestro:BOMNode`s of the
  parts list and, by BMK, the identifiers of the signals they produce or receive.
  HHM-Core has no module-in-module relation.
- **Skills from GRAFCET actions.** The station control programs themselves are only
  named (file names on the Festo CD), so the skills are derived from the GRAFCET
  actions; pre- and postconditions use the signal names, not a PLC language.
- **Folded GRAFCET steps.** Empty steps and steps that only set a flag carry no
  skill and are folded into the transition expressions of their neighbours. The
  Testing step 12, drawn empty, is kept as the 2 s measuring dwell.
- **One command per direction.** Where the documents name a command but not its
  output (Distributing), one command data point stands for it; the 7 outputs of the
  technical data are not mapped one to one.
- **Workpiece.** "The basic body of an assemblable pneumatic cylinder" (Processing
  assembly instructions) with red, silver and black variants. Red is 25 mm high and
  red/silver are 2.5 mm higher than black; the 22.5 mm of black is derived and says so.
  The diameter is not stated.
- **No market, runtime or digital twin.** The documents describe design-time
  equipment only; LTU is the operator, not a marketplace provider, and no readings
  exist.

## Validation

```bash
python tools/check.py examples/ltu-festo-mps
```

The SHACL check gives four expected **warnings** for these graphs: `lin:Workpiece`
and its three variants carry no `maestro:Identifier`, because no workpiece order
number is stated. There are no violations.

## Open data items

What the documents leave open, i.e. what to ask or measure at LTU:

| Topic | Open |
|---|---|
| LTU set-up | Which PLC and program each station runs (the manuals offer Siemens S7-31x, Festo FEC/IPC, Allen-Bradley ML1500, Mitsubishi FX1N); the actual line layout and neighbours; any network (PROFIBUS, Ethernet, OPC UA) above the parallel SysLink wiring |
| Distributing | The whole I/O allocation and BMKs (circuit diagram not supplied); sensor counts; valve-to-actuator mapping; ejecting-cylinder stroke |
| All stations | PLC addresses of the control console (only XMG1 is named); StationLink light/dark polarity; EMERGENCY-STOP category and wiring ("if available"); cycle times; dimensions and weight; maintenance intervals ("at regular intervals") |
| Testing | Cylinder strokes; height window in mm or V (comparator set by scale marks); analogue scaling at the PLC; behaviour when the downstream station stays busy |
| Processing | Installed axis stroke; solenoid part numbers (M4-M6); feedback for "workpiece fixed" and "ejected" (no sensors); behaviour after STOP / EMERGENCY-STOP |
| Handling | Linear-axis stroke and position coordinates; gripper open/closed (not sensed); what the receiver reads with no downstream station |
| Workpiece | Diameter, mass, materials of red and black, an order number |

Document conflicts kept as stated, with both values in the descriptions:

| Station | Conflict |
|---|---|
| Distributing | Vacuum switch 152619 (English text) vs 152629 (German text and lists); "inductive" vs magnet-actuated SME-8 sensors; the manual sequence returns the arm to "magazine" each cycle, the GRAFCET only in MAN |
| Testing | 7 digital inputs (technical data) vs 8 wired; BMK 3A1 = comparator (electric) and air slide (pneumatic); COLOUR lamp off for black (manual) vs on for black (GRAFCET) |
| Processing | Purely electric, yet the English commissioning text asks for 6 bar air; motor ratings in the circuit diagram (M1 5 W, M3 25 W) vs data sheets (3.14 W, 50 W) |
| Handling | 7 digital outputs (technical data) vs 5 wired; 1 slide module (parts list) vs 2 (manual, assembly instructions); DZF data-sheet file named 18-180 but content DZF-18-80; shock absorber file 158891 vs 158981 |
