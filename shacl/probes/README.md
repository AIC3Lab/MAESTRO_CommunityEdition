# SHACL probes

Small synthetic graphs that test the shapes themselves. Each file is one case:
either deliberately invalid data that a shape must reject, or valid data that
no shape may reject. None of them describes a real plant, and none is loaded
with the use-case graphs.

`tools/validate.py` (gate 10) validates each probe together with the ontology
and compares the results with the expectation in its `SHACL_PROBES` table. A
probe file without an entry, or an entry without a file, fails the gate.

| Probe | Expected result |
|---|---|
| `parameter-value-wrong-datatype.ttl` | `sh:Violation` from `msh:ParameterValueDatatypeShape` |
| `parameter-bounds-inverted.ttl` | `sh:Violation` from `msh:ParameterDefBoundsOrderShape` |
| `state-assertion-reversed-interval.ttl` | `sh:Violation` from `msh:StateAssertionIntervalOrderShape` |
| `execution-step-skill-mismatch.ttl` | `sh:Warning` (not a violation) from `msh:ExecutionStepSkillShape` |
| `deprecated-instanceOf-alias.ttl` | no result: a deprecated 0.1.0 name validates like its replacement |
| `deprecated-alias-wrong-datatype.ttl` | `sh:Violation` from `msh:ParameterValueDatatypeShape` through the deprecated name |
| `description-language-tagged.ttl` | no result: plain and language-tagged descriptions are both text |
| `description-not-text.ttl` | `sh:Violation` from `msh:DescriptionTextShape` |

To add a case, write the smallest graph that shows it, state the expectation in
its leading comment, and add the file to `SHACL_PROBES` and to this table.
