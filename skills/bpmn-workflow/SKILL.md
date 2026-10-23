---
name: bpmn-workflow
description: Model business processes as BPMN with lanes, decisions, parallel work, rework, systems and documents; generate BPMN XML and inspect, edit or export it with a local bpmn.io modeler.
---

# BPMN Workflow

Use this skill for process modelling and BPMN interchange in any domain. The local
editor uses bpmn.io. It does not execute business tasks or provide a workflow engine.

## Model a process

Establish the trigger, boundary, owner, roles, systems, inputs, products, decisions,
exceptions and end outcomes. Preserve supplied facts and distinguish proposals from
the current process. Ask for missing criteria that change the route; do not invent them.

Read [references/modelling.md](references/modelling.md) and use
`examples/order-fulfilment.json` as the input format. Name activities as actions on
objects, gateways as questions, branches as answers and end events as outcomes.
Human and system lanes identify performers; automated work retains an accountable
human role. Systems and product associations describe use, not a live integration.

Generate with Python, from this skill's folder:

```text
python scripts/bpmn.py generate examples/order-fulfilment.json --out output/order
```

The result includes BPMN XML and a readable operator guide. The generator supports
the subset documented in the reference. For BPMN constructs outside that subset,
use the modeler and preserve the exported XML as the authoritative diagram.

## Inspect or edit BPMN

From this skill's folder, install the locked dependencies once, then serve locally:

```text
npm ci
npm start
```

Open the printed loopback URL. Choose Open BPMN, select the generated XML, inspect
the process, edit labels or routes and download BPMN/SVG. The tool uploads nothing;
opened content stays in browser memory. The modeler supports its own BPMN feature
set, broader than the JSON generator. Preserve the bpmn.io attribution.

For automated import/export checking:

```text
node scripts/inspect.mjs output/order/process.bpmn
```

Import warnings and diagram completeness are evidence about interchange, not proof
of process correctness. Review the visual result and exception routes with the owner.
Canvas changes are saved to BPMN XML; they are not round-tripped into the source JSON.
Never claim a signature, notification, approval or other business effect from a diagram.
