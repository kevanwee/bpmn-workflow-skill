# Adapted from MIT-licensed exports.py, Kevan Wee, 2026. See repository NOTICE.md.
"""BPMN interchange + SVG share one deterministic layout."""
import html
import json
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

__version__ = '0.1.0'

B = "http://www.omg.org/spec/BPMN/20100524/MODEL"
DI = "http://www.omg.org/spec/BPMN/20100524/DI"
DC = "http://www.omg.org/spec/DD/20100524/DC"
D = "http://www.omg.org/spec/DD/20100524/DI"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
for prefix, ns in (("bpmn", B), ("bpmndi", DI), ("dc", DC), ("di", D), ("xsi", XSI)):
    ET.register_namespace(prefix, ns)


def element(parent, tag, ns=B, **attrs):
    return ET.SubElement(parent, f"{{{ns}}}{tag}", {k: str(v) for k, v in attrs.items()})


def layout(model):
    lanes = [l for l in model["swimlanes"] if l["scope"] == "internal"]
    rich = bool(model.get("systems") or model.get("work_products"))
    spacing = max([350] + [145 * (len(n.get("work_products_in", [])) + len(n.get("work_products_out", []))) + 40 for n in model["nodes"]]) if rich else 205
    node_heights={n['id']:max(100,25+16*len(textwrap.wrap(n['name'],33))) if rich else 70 for n in model['nodes']}
    sys_names={s['id']:s['name'] for s in model.get('systems',[])}
    max_sys=max([65]+[20+14*len(textwrap.wrap('Uses: '+'; '.join(sys_names[s] for s in n.get('system_refs',[])),32)) for n in model['nodes']])
    row_height = max(node_heights.values())+max_sys+130 if rich else 150
    # Forward ranks align parallel tasks. Back edges use a visible rework arc.
    indices = {n["id"]: i for i,n in enumerate(model["nodes"])}
    _, _, incoming = graph(model)
    ranks, slots, counts = {}, {}, {}
    for node in model["nodes"]:
        predecessors = [e["source"] for e in incoming[node["id"]] if indices[e["source"]] < indices[node["id"]]]
        rank = max((ranks[n]+1 for n in predecessors), default=0)
        ranks[node["id"]] = rank
        key = (node["lane"], rank)
        slots[node["id"]] = counts.get(key, 0)
        counts[key] = slots[node["id"]]+1
    bounds, y = {}, 60
    for lane in lanes:
        height = row_height * max((count for (lid,_),count in counts.items() if lid == lane["id"]), default=1) + 70
        bounds[lane["id"]] = (y, height)
        y += height
    positions = {n["id"]: (250+ranks[n["id"]]*spacing, bounds[n["lane"]][0]+(max_sys+35 if rich else 55)+slots[n["id"]]*row_height, 240 if rich else 154, node_heights[n['id']]) for n in model["nodes"]}
    return positions, 470 + (max(ranks.values())+1)*spacing, y, bounds


def waypoints(source, target, index):
    x, y, w, h = source
    tx, ty, tw, th = target
    if tx > x:
        if abs(ty-y) < 45 and tx-(x+w) > 250:
            corridor = min(y,ty)-35 if index%2 == 0 else max(y+h,ty+th)+35
            return [(x+w/2, y if index%2 == 0 else y+h), (x+w/2, corridor),
                    (tx+tw/2, corridor), (tx+tw/2, ty if index%2 == 0 else ty+th)]
        middle = x + w + 25
        return [(x+w, y+h/2), (middle, y+h/2), (middle, ty+th/2), (tx, ty+th/2)]
    top = min(y, ty) - 22 - (index % 3) * 9
    return [(x+w/2, y), (x+w/2, top), (tx+tw/2, top), (tx+tw/2, ty)]


def condition_label(edge):
    if edge.get("label"):
        return edge["label"]
    if edge.get("default"):
        return "otherwise"
    c = edge.get("condition", {})
    if c.get("op") in {"eq", "ne", "lt", "lte", "gt", "gte", "in"}:
        value = "yes" if c["value"] is True else "no" if c["value"] is False else str(c["value"])
        return f"{c['path'].split('.')[-1]} {c['op']} {value}"
    return c.get("op", "")


def information_items(model, positions):
    """Visible references, repeated beside each activity to avoid long data lines.

    Systems are labelled annotations, not invented BPMN system-symbol semantics.
    Work products use standard data objects/stores; these are descriptive and do
    not substitute for executable mappings or proof that a document was created.
    """
    systems = {s['id']: s for s in model.get('systems', [])}
    products = {p['id']: p for p in model.get('work_products', [])}
    for node in model['nodes']:
        x,y,w,h = positions[node['id']]
        system_height=65
        if node.get('system_refs'):
            names = '; '.join(systems[s]['name'] for s in node['system_refs'])
            system_height=max(65,20+14*len(textwrap.wrap('Uses: '+names,32)))
            yield {'id':'sys_info_'+node['id'].replace('-','_'), 'node':node['id'], 'kind':'system',
                   'name':'Uses: '+names,'bounds':(x,y-system_height-10,w,system_height)}
        refs = [('input',p) for p in node.get('work_products_in',[])] + [('output',p) for p in node.get('work_products_out',[])]
        for index,(direction,pid) in enumerate(refs):
            product=products[pid]
            yield {'id':f'sys_product_{node["id"].replace("-","_")}_{direction}_{index}',
                   'node':node['id'],'product':pid,'kind':product['kind'],'direction':direction,
                   'name':product['name'],'bounds':(x+index*145,y+h+35,125,max(70,20+14*len(textwrap.wrap(product['name'],18))))}


def message_points(message, positions, nodes):
    # Connect external pools vertically near the receiving/sending task, rather
    # than running a message line through intervening activity labels.
    internal = message["source"] if message["source"] in nodes else message["target"]
    external = message["target"] if internal == message["source"] else message["source"]
    x,y,w,h = positions[internal]
    _,py,_,_ = positions[external]
    corridor = x+w+28
    points = [(x+w,y+h/2), (corridor,y+h/2), (corridor,py)]
    return points if internal == message["source"] else list(reversed(points))


def bpmn_xml(manifest, model_name):
    model = manifest[model_name]
    nodes, _, _ = graph(model)
    positions, width, height, lane_bounds = layout(model)
    # Prefix all generated structural IDs so user IDs cannot collide.
    xid = lambda x: "user_" + x.replace("-", "_")
    process_id, collab_id = "sys_process", "sys_collaboration"
    root = ET.Element(f"{{{B}}}definitions", {"id": "sys_definitions", "targetNamespace": "urn:bpmn-workflow",
                                           "exporter": "bpmn-workflow", "exporterVersion": __version__})
    collab = element(root, "collaboration", id=collab_id)
    element(collab, "participant", id="sys_participant", name=manifest["name"], processRef=process_id)
    for lane in model["swimlanes"]:
        if lane["scope"] == "external":
            element(collab, "participant", id=xid(lane["id"]), name=lane["name"])
    for message in model["messages"]:
        element(collab, "messageFlow", id=xid(message["id"]), name=message["name"],
                sourceRef=xid(message["source"]), targetRef=xid(message["target"]))
    process = element(root, "process", id=process_id, name=manifest["name"], isExecutable="false")
    element(process, "documentation").text = "Descriptive BPMN interchange model; no execution engine is included."
    lane_set = element(process, "laneSet", id="sys_lanes")
    subs = {s["id"]: s for s in model["subprocesses"]}
    for lane in model["swimlanes"]:
        if lane["scope"] == "external":
            continue
        lane_el = element(lane_set, "lane", id=xid(lane["id"]), name=lane["name"])
        for node in model["nodes"]:
            if node["lane"] == lane["id"] and not node.get("subprocess"):
                element(lane_el, "flowNodeRef").text = xid(node["id"])
        for sub in subs.values():
            if nodes[sub["entry"]]["lane"] == lane["id"]:
                element(lane_el, "flowNodeRef").text = xid(sub["id"])
    containers = {None: process}
    for sub in subs.values():
        containers[sub["id"]] = element(process, "subProcess", id=xid(sub["id"]), name=sub["name"])
    tags = {"start": "startEvent", "end": "endEvent", "human": "userTask", "wait": "receiveTask",
            "ai": "serviceTask", "integration": "serviceTask", "exclusive": "exclusiveGateway",
            "parallel_split": "parallelGateway", "parallel_join": "parallelGateway"}
    for node in model["nodes"]:
        attrs = {"id": xid(node["id"]), "name": node["name"]}
        defaults = [e for e in model["conditional_edges"] if e["source"] == node["id"] and e.get("default")]
        if defaults:
            attrs["default"] = xid(defaults[0]["id"])
        if node["type"] in {"parallel_split", "parallel_join"}:
            attrs["gatewayDirection"] = "Diverging" if node["type"] == "parallel_split" else "Converging"
        tag = 'manualTask' if node['type']=='human' and node['activity']=='manual' else tags[node['type']]
        el = element(containers[node.get("subprocess")], tag, **attrs)
        element(el, "documentation").text = '\n'.join(filter(None, [
            node.get('description',''), node.get('instructions',''),
            'Performer: '+node['lane'],
            'Accountable role: '+node['responsible_role'] if node.get('responsible_role') else ''
        ]))
    info = list(information_items(model, positions))
    for item in info:
        if item['kind']=='system':
            annotation=element(process,'textAnnotation',id=item['id'])
            element(annotation,'text').text=item['name']
            element(process,'association',id=item['id']+'_link',sourceRef=xid(item['node']),targetRef=item['id'])
        else:
            tag='dataStoreReference' if item['kind']=='data_store' else 'dataObjectReference'
            attrs={'id':item['id'],'name':item['name']}
            if tag=='dataObjectReference':
                element(process,'dataObject',id=item['id']+'_object')
                attrs['dataObjectRef']=item['id']+'_object'
            reference=element(process,tag,**attrs)
            element(reference,'documentation').text='Work product: '+item['name']+'\nDirection: '+item['direction'].title()
            source,target=(item['id'],xid(item['node'])) if item['direction']=='input' else (xid(item['node']),item['id'])
            element(process,'association',id=item['id']+'_link',sourceRef=source,targetRef=target,associationDirection='One')
    flow_refs = {}
    for edge in model["edges"] + model["conditional_edges"]:
        source_sub = nodes[edge["source"]].get("subprocess")
        target_sub = nodes[edge["target"]].get("subprocess")
        same = source_sub == target_sub
        src = edge["source"] if same or not source_sub else source_sub
        dst = edge["target"] if same or not target_sub else target_sub
        el = element(containers[source_sub if same else None], "sequenceFlow", id=xid(edge["id"]),
                     sourceRef=xid(src), targetRef=xid(dst))
        if "condition" in edge or edge.get("default"):
            el.set("name", condition_label(edge))
        elif edge.get('label'):
            el.set('name',edge['label'])
        if "condition" in edge:
            condition = element(el, "conditionExpression", language="urn:bpmn-workflow:condition:v1")
            condition.set(f"{{{XSI}}}type", "bpmn:tFormalExpression")
            condition.text = edge["condition"]
        flow_refs[edge["id"]] = (src, dst)
    # BPMN's XSD orders flow elements before informational artifacts.
    for artifact in [e for e in process if e.tag in {f'{{{B}}}textAnnotation',f'{{{B}}}association'}]:
        process.remove(artifact)
        process.append(artifact)
    diagram = element(root, "BPMNDiagram", DI, id="sys_diagram")
    plane = element(diagram, "BPMNPlane", DI, id="sys_plane", bpmnElement=collab_id)
    def shape(ref, bounds, **attrs):
        sh = element(plane, "BPMNShape", DI, id="shape_" + ref, bpmnElement=ref, **attrs)
        element(sh, "Bounds", DC, **dict(zip(("x", "y", "width", "height"), bounds)))
        return sh
    def label_bounds(parent,bounds):
        label=element(parent,'BPMNLabel',DI)
        element(label,'Bounds',DC,**dict(zip(('x','y','width','height'),bounds)))
    shape("sys_participant", (30, 60, width, height-60), isHorizontal="true")
    row = 0
    for lane in model["swimlanes"]:
        if lane["scope"] == "internal":
            y, lane_height = lane_bounds[lane["id"]]
            shape(xid(lane["id"]), (60, y, width-30, lane_height), isHorizontal="true")
            row += 1
    for sub in subs.values():
        children = [positions[n["id"]] for n in model["nodes"] if n.get("subprocess") == sub["id"]]
        x, y = min(p[0] for p in children)-15, min(p[1] for p in children)-30
        bounds = (x, y, max(p[0]+p[2] for p in children)-x+15, max(p[1]+p[3] for p in children)-y+15)
        positions[sub["id"]] = bounds
        shape(xid(sub["id"]), bounds, isExpanded="true")
    for node in model["nodes"]:
        x, y, w, h = positions[node["id"]]
        if node["type"] in {"start", "end"}:
            positions[node["id"]] = (x+(w-36)/2, y+(h-36)/2, 36, 36)
        elif node["type"] in {"exclusive", "parallel_split", "parallel_join"}:
            positions[node["id"]] = (x+(w-50)/2, y+(h-50)/2, 50, 50)
        sh=shape(xid(node["id"]), positions[node["id"]], **({"isMarkerVisible": "true"} if node["type"] == "exclusive" else {}))
        px,py,pw,ph=positions[node['id']]
        if node['type'] in {'exclusive','parallel_split','parallel_join'}:
            # Keep questions clear of the central return/rework connector.
            label_bounds(sh,(px-200,py-95,220,70))
        elif node['type'] in {'start','end'}:
            label_bounds(sh,(px+pw/2-120,py+ph+10,240,65))
    for item in info:
        shape(item['id'],item['bounds'])
        edge=element(plane,'BPMNEdge',DI,id='di_'+item['id']+'_link',bpmnElement=item['id']+'_link')
        x,y,w,h=positions[item['node']];tx,ty,tw,th=item['bounds']
        points=[(x+w/2,y),(tx+tw/2,ty+th)] if item['kind']=='system' else [(x+w/2,y+h),(tx+tw/2,ty)]
        if item.get('direction')=='input':points.reverse()
        for px,py in points:element(edge,'waypoint',D,x=px,y=py)
    for index, (eid, (src, dst)) in enumerate(flow_refs.items()):
        edge = element(plane, "BPMNEdge", DI, id="di_"+xid(eid), bpmnElement=xid(eid))
        points=waypoints(positions[src], positions[dst], index)
        for x, y in points:
            element(edge, "waypoint", D, x=x, y=y)
        declared=next(e for e in model['edges']+model['conditional_edges'] if e['id']==eid)
        if declared.get('label') or 'condition' in declared or declared.get('default'):
            a,b=max(zip(points,points[1:]),key=lambda p:abs(p[1][0]-p[0][0])+abs(p[1][1]-p[0][1]))
            if a[0]==b[0]:bounds=(a[0]+12,(a[1]+b[1])/2-30,220,60)
            else:bounds=((a[0]+b[0])/2-110,a[1]-68,220,60)
            label_bounds(edge,bounds)
    for i, lane in enumerate(l for l in model["swimlanes"] if l["scope"] == "external"):
        positions[lane["id"]] = (30, height+100+i*130, width, 90)
        shape(xid(lane["id"]), positions[lane["id"]], isHorizontal="true")
    for index, message in enumerate(model["messages"]):
        edge = element(plane, "BPMNEdge", DI, id="di_"+xid(message["id"]), bpmnElement=xid(message["id"]))
        for x, y in message_points(message, positions, nodes):
            element(edge, "waypoint", D, x=x, y=y)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)



def graph(model):
    nodes={n['id']:n for n in model['nodes']}
    outgoing,incoming=defaultdict(list),defaultdict(list)
    for edge in model['edges']+model['conditional_edges']:
        outgoing[edge['source']].append(edge)
        incoming[edge['target']].append(edge)
    return nodes,outgoing,incoming
