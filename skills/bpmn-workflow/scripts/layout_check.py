"""Geometry check for generated BPMN diagrams: connectors must not cross unrelated
shapes, and labels must stay inside the diagram and clear of activities.

    python scripts/layout_check.py output/order/process.bpmn
"""
import sys
import xml.etree.ElementTree as ET

B = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
D = "{http://www.omg.org/spec/DD/20100524/DI}"
CONTAINERS = {"participant", "lane", "subProcess"}


def rect(el):
    b = el.find(DC + "Bounds")
    return tuple(float(b.get(k)) for k in ("x", "y", "width", "height"))


def crosses(p, q, r, inset=2):
    """True if the axis-aligned or straight segment p-q passes through the inside of r."""
    x, y, w, h = r
    x0, y0, x1, y1 = x + inset, y + inset, x + w - inset, y + h - inset
    if x0 >= x1 or y0 >= y1:
        return False
    # Liang-Barsky clipping against the inset rectangle.
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for edge_p, edge_q in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if edge_p == 0:
            if edge_q < 0:
                return False
            continue
        t = edge_q / edge_p
        if edge_p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return t1 - t0 > 1e-6


def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def check(xml):
    root = ET.fromstring(xml)
    kinds, ends = {}, {}
    for el in root.iter():
        if el.get("id") and el.tag.startswith(B):
            kinds[el.get("id")] = el.tag[len(B):]
        if el.get("sourceRef") and el.get("targetRef"):
            ends[el.get("id")] = {el.get("sourceRef"), el.get("targetRef")}
    shapes = {s.get("bpmnElement"): rect(s) for s in root.iter(DI + "BPMNShape")}
    solid = {k: r for k, r in shapes.items() if kinds.get(k) not in CONTAINERS}
    left = min(r[0] for k, r in shapes.items() if kinds.get(k) == "participant")
    problems = []
    for edge in root.iter(DI + "BPMNEdge"):
        ref = edge.get("bpmnElement")
        pts = [(float(w.get("x")), float(w.get("y"))) for w in edge.findall(D + "waypoint")]
        for k, r in solid.items():
            if k in ends.get(ref, ()):
                continue
            if any(crosses(p, q, r) for p, q in zip(pts, pts[1:])):
                problems.append(f"connector {ref} crosses {k}")
    for owner in list(root.iter(DI + "BPMNShape")) + list(root.iter(DI + "BPMNEdge")):
        label = owner.find(DI + "BPMNLabel")
        if label is None:
            continue
        r, ref = rect(label), owner.get("bpmnElement")
        if r[0] < left:
            problems.append(f"label of {ref} starts {left - r[0]:.0f}px left of the diagram")
        for k, s in solid.items():
            if k != ref and k not in ends.get(ref, ()) and kinds.get(k) not in {"textAnnotation"} and overlap(r, s):
                problems.append(f"label of {ref} overlaps {k}")
    return problems


if __name__ == "__main__":
    found = check(open(sys.argv[1], encoding="utf-8").read())
    print("\n".join(found) or "layout ok")
    sys.exit(1 if found else 0)
