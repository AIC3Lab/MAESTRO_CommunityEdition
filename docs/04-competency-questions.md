# Competency questions

The fifteen competency questions in `queries/cq/` are the acceptance test of the
ontology: each one is a SPARQL query that returns at least its floor of rows
over the union of every module and the `examples/widget-cell/` data. Run one with
`python tools/check.py examples/widget-cell --query queries/cq/<file>.rq`.

The questions follow the HHM-Core clusters and the added modules:

| Cluster or module | Questions |
|---|---|
| Physical resources | CQ01 stations, modules, capabilities |
| Skills | CQ02 composite skills and their constituents |
| Recipe / planning | CQ03 recipe steps in order with skills and control flow; CQ04 data bindings output to input |
| Product | CQ05 product type structure; CQ06 bill of materials, recursively |
| Safety / security / policy | CQ07 who may do what under which policy; CQ08 hazards, risks, mitigations and achieved levels |
| Invocation hooks | CQ09 interface to endpoint to binding to signature |
| Minimal execution | CQ10 execution trace; CQ11 faults raised and fault specifications |
| Runtime state | CQ12 current state per dimension from open assertions |
| Energy | CQ13 energy over an interval and its source |
| Maintenance | CQ14 plan, task, action, finding, return to service |
| Manufacturing as a service | CQ15 request, quote, contract, production order |

The full list of questions, files and floors is in `queries/README.md`.

Rules for writing a question:

- Prefix every term with `maestro:`; local names coincide with MAESTRO 1.0 names, so a
  bare name is ambiguous when both stacks are loaded.
- Keep OPTIONAL blocks nested under the pattern that binds their subject, and put
  FILTER clauses inside the group whose variables they test; rdflib evaluates a
  filter placed after a UNION or OPTIONAL against an empty binding.
- Every file should parse on its own with `rdflib.plugins.sparql.prepareQuery`.
