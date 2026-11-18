# Figures (ontology 0.2.0)

Figures of the MAESTRO package, using the 0.2.0 ontology and current example data. The
house style uses a muted palette, DejaVu Sans, rounded boxes with hairline borders and a
reserved title band. Matplotlib figures are 300 DPI; Graphviz `dot` draws the class and
instance graphs.

```bash
# from the package root, with rdflib, matplotlib, Pillow and Graphviz `dot` on PATH
python figures/v0.2.0/scripts/render_v020.py                 # render everything (about 2.5 min)
python figures/v0.2.0/scripts/render_figures.py --check     # check the hand-authored 03 and 07 only
```

| Folder | Content |
|---|---|
| `png/` | Every figure as PNG |
| `svg/` | Vector versions of the large Graphviz figures (03, 07, 13, 14, proposed model and knowledge graphs). No DOCTYPE line, so they can be published as artifact files. |
| `src/` | Graphviz sources, `model-0.2.0.json` (the class and property model `tools/gen_graph.py` derives from the Turtle files), and the count summaries. Everything is generated except `03-hhm-schema.gv` and `07-beyond-clusters.gv`, which are hand-authored. |
| `scripts/` | `render_v020.py` (entry point; figures 13 to 16), `render_figures.py` (01 to 07), `render.py` (proposed model), `render_kg.py` (helpers shared by the knowledge-graph figures), `render_kg_ltu.py` (LTU graphs) |

## Figures

| # | PNG | Built by | What it shows |
|---|---|---|---|
| 01 | `01-module-stack.png` | matplotlib | Umbrella, the twenty modules by layer (`core/`, `modules/`, `ext/`), and the satellites that hang off the umbrella without being imported by it |
| 02 | `02-import-graph.png` | generated `.gv` | The acyclic `owl:imports` graph rooted at `core/resource.ttl`; A → B means A imports B |
| 03 | `03-hhm-schema.png` (+ svg) | hand-authored `.gv` | Class-relationship schema of the seven HHM-Core v1 clusters and the digital-twin extension. Additions made in 0.2.0 are green: `Resource`, `Condition`, `realizesStep`, `hasOutput`, `recommendsMitigation`, `specializes`, `InOut`, `paramName`, `mappingSpec`. |
| 04 | `04-standards-basis.png` | matplotlib | Every link from an `maestro:` term to an external vocabulary, by vocabulary, pinned copy, module and link kind; plus the hooks that are named but not mapped |
| 05 | `05-widget-cell.png` | generated `.gv` | Instance graph of the widget cell (now the synthetic fixture `queries/fixtures/widget-cell/`): every individual and object-property triple, clustered by concern and file |
| 06 | `06-maestro-alignment.png` | matplotlib | Where the definitions come from: a module × MAESTRO 1.0 module matrix of exact, close and new terms |
| 07 | `07-beyond-clusters.png` (+ svg) | hand-authored `.gv` | Runtime state, energy, maintenance and manufacturing as a service, and the HHM-Core classes they attach to |
| 13 | `13-class-taxonomy.png` (+ svg) | generated `.gv` | Every `maestro:` class and `rdfs:subClassOf` edge by declaring module. The grouping classes and `maestro:ValueSet` are bold tinted boxes, and value-set classes list their individuals. |
| 14 | `14-property-structure.png` (+ svg) | generated `.gv` | The sub-property hierarchy (transitive `hasPart` over `hasModule`, `hasStep`, `hasSubSkill`, `hasSubItem`; the PROV-O and ODRL bridges), the ten `owl:inverseOf` pairs, and the 27 functional properties |
| 15 | `15-renamed-terms.png` | matplotlib | 0.1.0 name → 0.2.0 name → HHM-Core v1 name for every renamed term |
| 16 | `16-version-comparison.png` | matplotlib | Vocabulary and axiom counts for 0.1.0 (read from the first commit, `920094a`) and 0.2.0; numbers in `src/16-version-comparison.json` |
| — | `proposed-maestro.png`, `…-with-extensions.png` (+ svg) | `render.py` | The whole model as one graph: the seven clusters plus the four modules, and the same with the extensions. About 7000 px wide; the SVG stays sharp. The `subClassOf` edges to `maestro:ValueSet` are drawn only in 13. |
| — | `kg-ltu-overview.png`, `kg-ltu-{distributing,testing,processing,handling,line}.png` (+ svg) | `render_kg_ltu.py` | The LTU Festo MPS line: one overview and one full graph per production unit; counts in `src/kg-ltu-summary.json` |

`03-hhm-schema.gv` and `07-beyond-clusters.gv` are hand-authored so that their layout stays
readable. When a class or relation changes in `core/`, `modules/` or `ext/digital-twin.ttl`,
edit them by hand. `render_figures.py --check` also runs at the start of every render. It
fails if a name or edge label in them is undeclared or is a deprecated 0.1.0 name, so a
rename fails the render instead of leaving a stale picture.

## Reading the Graphviz figures

- **Box** = a class (03, 07, 13) or an individual (05). In 05 the italic second line is
  the individual's type, for example `ex:Transfer (maestro:CompositeSkill)`.
- **Gold box with a double border** = a class drawn in the HHM-Core v1 diagram, or an
  individual typed by one (05). The package carries all 43 of those classes; two of them
  carry a clearer name since 0.2.0 (`BOMNode` → `BOMItem`, `Mode` → `OperatingMode`, see
  `docs/hhm-conformance.md`). A plain box is a class folded in from MAESTRO 1.0 or added by
  the package.
- **Solid arrow** = one of the 47 HHM-Core v1 relations. **Dashed arrow** = a relation the
  package added (`targetStep`, `bindsFrom`, `bindsTo` and the ones folded in from
  MAESTRO 1.0). In 07 every relation is an addition, so dashed marks the open-domain
  shortcuts `hasState` and `hasTime`. **Dotted arrow** = `rdfs:subClassOf` or a
  documentary match.
- **Green** (03) = added in 0.2.0.
- **Orange «EXT» note** = an `ext/` file realising an extension point, or a documentary
  match to a vocabulary pinned under `references/` (CHG-023, gate 7).
- **Grey dashed note** = a hook: a vocabulary the HHM diagram names but the package does
  not point at (ECLASS, DPP, PRONTO, CaSkMan / CSS, AAS, OpenAPI, SAREF4INMA, XACML).
- **Grey ellipse** = a controlled-vocabulary individual (05), or a PROV-O / ODRL term (14).
- **Purple dashed double arrow** (14) = `owl:inverseOf`.
- **Coloured rounded outline** = a cluster. In 03 it is an HHM cluster file, in 07, 13 and
  14 a module, in 05 a concern and source file. The runtime snapshot in 05 has a dashed
  outline because it is a separate graph (`maestro:Snapshot`).

In the LTU graphs, enumeration values (direction, protocol, data format,
action, role, state) are rows inside the node, so they do
not become hubs. Shared capabilities and materials have a grey dashed
border, and `maestro:description` and `rdfs:comment` are left out. Edges take the colour of the
module that declares the property: solid for core, dashed for modules, dotted for
extensions and `rdfs:seeAlso`.

Figure 16 uses amber `#C98B2B` for 0.1.0 and blue `#2563A8` for 0.2.0. The data-viz palette
validator gives colour-blind ΔE 26.8 and normal-vision ΔE 31.8 for the pair, and every bar
carries its value as a label.

To change the look, edit `PALETTE` and `plt.rcParams` at the top of
`scripts/render_figures.py` (matplotlib) or the `node` / `edge` defaults in the builders
(Graphviz), then re-run.
