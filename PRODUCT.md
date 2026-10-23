# BPMN Workflow Skill

## Platform
Local browser tool and agent skill; Python 3.11+ generation, Node 24 editor server.

## Users and purpose
Process analysts and engineers turn a process narrative into inspectable BPMN, then
edit and export it using bpmn.io. No legal domain, account or model API is required.

## Confirmed scope and visual direction
This is an extraction of the existing process editor, not a visual redesign. Preserve
the familiar bpmn.io palette and canvas. Retain the existing workspace's near-white
surface, dark ink, restrained green actions and legible system controls. The canvas
leads; a compact toolbar opens XML, fits the diagram and downloads XML/SVG. An
inspector exposes the selected element's name and documentation. A visible boundary
states that diagram validation and editing do not execute a business workflow.

## Direction contract
THESIS: An independent working BPMN editor with the diagram immediately available.
OWN-WORLD: The inherited quiet working surface and original bpmn.io notation.
STORY: Generate or open BPMN, inspect/edit it, and export the actual model.
FIRST VIEWPORT: Compact title/toolbar, large canvas, narrow element inspector.
FORM: Precisely scoped extraction; seed: none (unavailable).
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
