# Query fixtures

Synthetic data for testing the competency questions in `../cq/`. Nothing here describes
a real plant, partner or product, and no file in this folder is ever loaded together
with the source-derived graphs in `usecase-knowledge-graphs/`.

`widget-cell/` is one small invented production cell, built so that every one of the
fifteen competency questions has a complete answer: `plant.ttl` holds the design-time
description, `runtime.ttl` a runtime snapshot (executions, a fault, state assertions,
energy and maintenance records) and `market.ttl` a request, quote, contract and
production order.

`tools/validate.py` gate 11 runs each competency question over the ontology plus this
fixture and requires its row floor and a row that binds every answer field; gates 6, 8
and 10 check the fixture against the ontology and the shapes like any other data. See
[`docs/04-competency-questions.md`](../../docs/04-competency-questions.md).
