# Competency questions

`tools/validate.py` (gate 11) runs every query; the floors are listed in `CQ_MINIMUMS`
there, and every query must parse with rdflib on its own (gate 1).

The competency questions in `cq/` are tested over the modules plus the synthetic
fixture in [`fixtures/widget-cell/`](fixtures/widget-cell/): each must return at least
its floor of rows, and at least one row must bind every answer field of the question
(`CQ_ANSWER_FIELDS`). The fixture is invented test data, kept apart from
`usecase-knowledge-graphs/` and never loaded with it. The gate also runs each
competency question over the use-case graphs and reports it as answered, partial or
without data; that report does not fail the gate, because a record the source documents
do not contain is not invented. See
[`docs/04-competency-questions.md`](../docs/04-competency-questions.md).

| CQ | Question | File | Floor |
|---|---|---|---|
| CQ01 | Which stations have which modules, and which capabilities does each module provide? | `cq/cq01-station-modules-capabilities.rq` | 1 |
| CQ02 | Which skills compose a composite skill, and which capability does each constituent require? | `cq/cq02-composite-subskills.rq` | 1 |
| CQ03 | Which plan steps make up a recipe, in what order, realised by which skill, under which control-flow constraint? | `cq/cq03-recipe-steps-skills.rq` | 3 |
| CQ04 | Which output (or bidirectional) parameter feeds which input (or bidirectional) parameter of which step, and in which unit? | `cq/cq04-data-bindings.rq` | 3 |
| CQ05 | Which variants, features, requirements, identifiers and instances does a product type have? | `cq/cq05-product-structure.rq` | 1 |
| CQ06 | Which parts, in what quantity and of which material, appear anywhere in the bill of materials of a product type? | `cq/cq06-bom.rq` | 1 |
| CQ07 | Which role may perform which action on which target, under which policy, required mode and evidence? | `cq/cq07-policy-grants.rq` | 1 |
| CQ08 | Which hazards raise which risks, which mitigations reduce them, which safety function covers the hazard, and what level does it achieve? | `cq/cq08-hazards-risks-mitigations.rq` | 1 |
| CQ09 | Through which endpoint, protocol, binding and operation signature is a skill interface invoked? | `cq/cq09-invocation-path.rq` | 1 |
| CQ10 | Which executions of which skill ran on which resource via which endpoint, with which status, start and end time? | `cq/cq10-execution-trace.rq` | 2 |
| CQ11 | Which executions raised which fault, of which specified kind that the skill declares it may raise? | `cq/cq11-faults.rq` | 1 |
| CQ12 | What is the current state of each resource in each state dimension? | `cq/cq12-current-state.rq` | 2 |
| CQ13 | How much energy did a subject consume over which interval, and from which source? | `cq/cq13-energy-and-power.rq` | 1 |
| CQ14 | Which maintenance plan and tasks apply to an asset, which action performed a task, what did it find, and may the asset return to service? | `cq/cq14-maintenance-status.rq` | 1 |
| CQ15 | Which quotes answer which request, from which provider on which marketplace, at what price and lead time, and which became a contract and order? | `cq/cq15-quotes-contracts.rq` | 1 |

## LTU use-case questions

The `ltu/` queries ask about the four Festo MPS stations of the LTU line in
`usecase-knowledge-graphs/ltu-festo-mps/`. Their floors, in the same `CQ_MINIMUMS`
dictionary, apply over the modules plus the use-case graphs.

| LQ | Question | File | Floor |
|---|---|---|---|
| LQ01 | Which signal sits on which SysLink connector, terminal bit, pin and BMK of each station, in which direction and data type? | `ltu/lq01-io-allocation.rq` | 80 |
| LQ02 | Which station can run each step of the line recipe (capability matching), and when does the line pass on to the next step? | `ltu/lq02-line-route.rq` | 4 |
| LQ03 | What is each station's GRAFCET sequence: steps, realising skills, transitions, flow types and conditions? | `ltu/lq03-grafcet-sequences.rq` | 60 |
| LQ04 | Which assemblies and components, with designation, quantity and Festo part number, make up each station? | `ltu/lq04-station-bom.rq` | 90 |
