# Modelling and interchange

Use `examples/order-fulfilment.json` for the generator's format. `lanes` identify
human/system performers; external lanes become black-box participant pools. Activities
belong to internal lanes. `flows` connect process nodes; `messages` connect a process
node to an external participant. Sequence flow must not cross participant boundaries.

Supported generator node types: `start`, `end`, `user`, `manual`, `service`, `receive`,
`exclusive`, `parallel-split`, `parallel-join`. System activities require a human
`responsible_role`. `system_refs` refer to the systems catalogue; `work_products_in`
and `work_products_out` refer to documents or data stores. They are descriptive
associations. Inputs and outputs are not collected or executed by this tool.

Give exclusive branches readable `label` values and a descriptive string `condition`,
or mark one as `default: true`. Expressions are descriptive formal expressions, not
evaluated rules. Pair parallel splits/joins and inspect synchronisation and rework
visually. Structural validation checks IDs, references, activity placement, branching,
start/end reachability and paths to end states; it is not a deadlock proof.

The generator lays out lanes and nodes deterministically. Long processes require
overview and detail views. Use bpmn.io to reposition complex diagrams and save the
XML. Layout follows input ordering; order forward work before the branches it feeds.
Loops can return to an earlier activity. Existing output directories are never replaced.

Nested subprocesses, timer/boundary events and specialised BPMN constructs are edited
in bpmn.io directly. They are outside the JSON generator's declared subset. Opened
BPMN stays XML; the tool does not attempt a lossy XML-to-JSON conversion.

The modeler and interchange parser are independent upstream libraries:
[bpmn-js](https://github.com/bpmn-io/bpmn-js) and
[bpmn-moddle](https://github.com/bpmn-io/bpmn-moddle). Import success is not legal,
operational or engine-specific validation. Check the target engine's contracts if
the diagram will be deployed to an execution engine.
