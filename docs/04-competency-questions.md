# Competency questions

The fifteen competency questions in `queries/cq/` are the acceptance test of the
ontology. Gate 11 of `tools/validate.py` runs each one twice, over two different
datasets, because "the schema can answer this" and "our data answers this" are
different claims:

- **Acceptance, over synthetic data.** Each query runs over the modules plus the
  widget-cell fixture in `queries/fixtures/widget-cell/`. It must return at least its
  floor of rows (`CQ_MINIMUMS`), and at least one row must bind every answer field of
  the question (`CQ_ANSWER_FIELDS`), so a result that leaves the asked-for values
  empty does not count. The fixture is invented test data: it is kept out of
  `usecase-knowledge-graphs/` and is never loaded with the use-case graphs. A failure
  here fails the gate.
- **Coverage, over the use-case graphs.** Each query also runs over the modules plus
  the source-derived graphs. The gate reports the question as *answered* (some row
  binds every answer field), *partial* (rows exist, none complete; the fields no row
  binds are named) or *no data* (no rows). This never fails the gate: a source
  document that records no executions, states, energy readings or quotes is a gap in
  the source material, not in the schema, and nothing is invented to close it.

At the time of writing the use-case graphs answer CQ01 to CQ07, answer CQ08 and CQ14
in part (no achieved safety level; no performed maintenance action, finding or
outcome) and hold no records for CQ09 to CQ13 and CQ15.

A query file without a floor, or a competency question without answer fields, fails
the gate.

The questions follow the HHM-Core clusters and the added modules:

| Cluster or module | Questions |
|---|---|
| Physical resources | CQ01 stations, modules, capabilities |
| Skills | CQ02 composite skills and their constituents |
| Recipe / planning | CQ03 recipe steps in order with skills and control flow; CQ04 data bindings from an output or bidirectional parameter to an input or bidirectional parameter |
| Product | CQ05 product type structure; CQ06 bill of materials, recursively |
| Safety / security / policy | CQ07 who may do what under which policy; CQ08 hazards, risks, mitigations and achieved levels |
| Invocation hooks | CQ09 interface to endpoint to binding to signature |
| Minimal execution | CQ10 execution trace; CQ11 faults raised and fault specifications |
| Runtime state | CQ12 current state per dimension from open assertions |
| Energy | CQ13 energy over an interval and its source |
| Maintenance | CQ14 plan, task, action, finding, return to service |
| Manufacturing as a service | CQ15 request, quote, contract, production order |

The full list of questions, files and floors is in `queries/README.md`.

A second set, `queries/ltu/` (LQ01 to LQ04), asks about the LTU Festo MPS
line. These questions are about the use-case data itself, so gate 11 holds them to
their row floors over the use-case graphs, without the fixture.

Rules for writing a question:

- Prefix every term with `maestro:`; local names coincide with MAESTRO 1.0 names, so a
  bare name is ambiguous when both stacks are loaded.
- Keep OPTIONAL blocks nested under the pattern that binds their subject, and put
  FILTER clauses inside the group whose variables they test; rdflib evaluates a
  filter placed after a UNION or OPTIONAL against an empty binding.
- Every file must parse on its own with `rdflib.plugins.sparql.prepareQuery`
  (gate 1).
- Add the floor to `CQ_MINIMUMS` in `tools/validate.py` and a row to
  `queries/README.md` in the same change. For a competency question, also list its
  answer fields in `CQ_ANSWER_FIELDS` (the variables the question asks for; leave out
  what it treats as optional, and write `a|b` where either variable answers it) and
  give the fixture the data that answers it.
- Never add invented records to a use-case graph to satisfy a question; synthetic
  data belongs in `queries/fixtures/`.
