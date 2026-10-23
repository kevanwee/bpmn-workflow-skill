# Verification

Checked on 23 October 2026 with Python 3.14 and Node 24 on Windows.

- The skill-creator structural validator passes.
- Three automated end-to-end checks pass: BPMN generation/parsing and output preservation;
  invalid-reference, reachability and performer rejection; actual bpmn.io import, editing,
  XML/SVG downloads and loopback server boundaries.
- The browser check additionally imports two documentation entries with different text
  formats. Name-only changes preserve both; an explicit edit changes only its selected
  entry and preserves both formats on export.
- The illustrative example has 15 flow nodes, four internal lanes, an external customer
  pool, three systems and three work products. It includes refusal, replenishment,
  parallel packing/invoicing and message flows. bpmn-moddle imports it without warnings.
- Actual desktop/mobile fitted and detail captures are recorded in screenshots.json.
  Header/inspector axe checks report no violations or page overflow. This does not
  establish accessibility of every third-party canvas interaction.

The Impeccable finish review found and prompted documentation-fidelity and screenshot
framing corrections. The reviewer scored all three findings resolved and issued a
scoped **ship** verdict. The generated XML also passes the official OMG BPMN XSD
validation using an external schema bundle; that bundle is not an installation dependency.
No business process was executed. No legal adequacy, target-engine compatibility or
deadlock-freedom claim follows from these checks. Python 3.11 and Linux are CI targets;
the local measurements above are Windows/Python 3.14 only.
