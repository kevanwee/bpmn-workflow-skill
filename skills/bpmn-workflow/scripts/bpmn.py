"""Domain-neutral BPMN generation. Standard library only; no workflow execution."""
import argparse
import copy
import json
import re
import sys
from pathlib import Path
from diagram import bpmn_xml

TYPES = {'start':'start','end':'end','user':'human','manual':'human','service':'integration',
         'receive':'wait','exclusive':'exclusive','parallel-split':'parallel_split','parallel-join':'parallel_join'}
ID = re.compile(r'[a-z][a-z0-9-]{0,62}\Z')

def normalise(spec):
    if not isinstance(spec,dict) or not str(spec.get('name','')).strip():
        raise ValueError('Provide a process name and a JSON object')
    allowed={'name','purpose','trigger','lanes','nodes','flows','systems','work_products','messages'}
    if set(spec)-allowed: raise ValueError('Unknown process fields: '+', '.join(sorted(set(spec)-allowed)))
    model={'version':'1.0.0','swimlanes':copy.deepcopy(spec.get('lanes',[])),
           'nodes':copy.deepcopy(spec.get('nodes',[])),'edges':[],'conditional_edges':[],
           'subprocesses':[],'messages':copy.deepcopy(spec.get('messages',[])),
           'systems':copy.deepcopy(spec.get('systems',[])),'work_products':copy.deepcopy(spec.get('work_products',[]))}
    seen=set()
    def identify(item):
        if not isinstance(item,dict) or not ID.fullmatch(item.get('id','')): raise ValueError('IDs must be lowercase words separated by hyphens')
        if item['id'] in seen: raise ValueError('Duplicate ID: '+item['id'])
        seen.add(item['id'])
        if not str(item.get('name','')).strip(): raise ValueError('Name required: '+item['id'])
    for lane in model['swimlanes']:
        identify(lane);lane.setdefault('participant','human');lane.setdefault('scope','internal')
        if lane['participant'] not in {'human','system'} or lane['scope'] not in {'internal','external'}:raise ValueError('Invalid lane type or scope')
    lanes={l['id']:l for l in model['swimlanes']}
    if not any(l['scope']=='internal' for l in lanes.values()):raise ValueError('At least one internal lane is required')
    for key in ['systems','work_products']:
        for item in model[key]:
            identify(item);item.setdefault('description','')
            if key=='work_products' and item.get('kind') not in {'document','data_store'}:raise ValueError('Work products require document or data_store kind')
    systems={s['id'] for s in model['systems']};products={p['id'] for p in model['work_products']}
    for node in model['nodes']:
        identify(node);kind=node.get('type');lane=lanes.get(node.get('lane'))
        if kind not in TYPES:raise ValueError('Unsupported generator node type: '+str(kind))
        if not lane or lane['scope']!='internal':raise ValueError('Activities and events require an internal lane')
        control=kind in {'start','end','exclusive','parallel-split','parallel-join'}
        if not control:
            if kind=='service' and (lane['participant']!='system' or lanes.get(node.get('responsible_role'),{}).get('participant')!='human' or lanes.get(node.get('responsible_role'),{}).get('scope')!='internal'):
                raise ValueError('Service tasks require a system performer and internal human responsible_role')
            if kind in {'user','manual','receive'} and lane['participant']!='human':raise ValueError('Human activities belong to human lanes')
        for key,available in [('system_refs',systems),('work_products_in',products),('work_products_out',products)]:
            if not isinstance(node.get(key,[]),list) or any(ref not in available for ref in node.get(key,[])):raise ValueError('Unknown or invalid '+key+' at '+node['id'])
            if control and node.get(key):raise ValueError('Attach systems/products to activities, not control nodes')
        if kind=='manual' and node.get('system_refs'):raise ValueError('Manual activities do not use systems; choose user instead')
        node.update(type=TYPES[kind],activity='control' if control else 'manual' if kind=='manual' else 'automated' if kind=='service' else 'interactive',
                    executor='runner' if control else 'agent' if kind=='service' else 'human',source_refs=[])
    nodes={n['id']:n for n in model['nodes']};out={k:[] for k in nodes};incoming={k:[] for k in nodes}
    for flow in spec.get('flows',[]):
        flow=copy.deepcopy(flow);identify(flow|{'name':flow.get('label','flow') or 'flow'})
        src,dst=flow.get('source'),flow.get('target')
        if src not in nodes or dst not in nodes:raise ValueError('Unknown flow endpoint')
        if flow.get('default') and 'condition' in flow:raise ValueError('A default flow cannot also have a condition')
        if ('condition' in flow or flow.get('default')) and nodes[src]['type']!='exclusive':raise ValueError('Conditional routes require an exclusive gateway')
        if nodes[src]['type']=='exclusive' and not flow.get('label'):raise ValueError('Label each exclusive answer')
        if 'condition' in flow:
            if not isinstance(flow['condition'],str) or not flow['condition'].strip():raise ValueError('Conditions must be nonempty descriptive expressions')
        out[src].append(dst);incoming[dst].append(src)
        model['conditional_edges' if 'condition' in flow or flow.get('default') else 'edges'].append(flow)
    starts=[n['id'] for n in nodes.values() if n['type']=='start'];ends=[n['id'] for n in nodes.values() if n['type']=='end']
    if not starts or not ends:raise ValueError('Provide start and end events')
    for node in nodes.values():
        key,kind=node['id'],node['type']
        if kind=='start' and (incoming[key] or len(out[key])!=1):raise ValueError('Start events require one outgoing flow and no incoming flow')
        if kind=='end' and (out[key] or not incoming[key]):raise ValueError('End events require incoming flows and no outgoing flow')
        if kind not in {'start','end','exclusive','parallel_split','parallel_join'} and (not incoming[key] or len(out[key])!=1):raise ValueError('Activities require incoming work and one next route')
        if kind in {'exclusive','parallel_split'} and (not incoming[key] or len(out[key])<2):raise ValueError('Decision/split gateways require multiple outgoing routes')
        if kind=='parallel_join' and (len(incoming[key])<2 or len(out[key])!=1):raise ValueError('Parallel joins require multiple arrivals and one next route')
        if sum(e.get('default',False) for e in model['conditional_edges'] if e['source']==key)>1:raise ValueError('Only one default route is allowed')
    def reachable(seeds,edges):
        visited=set(seeds);todo=list(seeds)
        while todo:
            for target in edges[todo.pop()]:
                if target not in visited:visited.add(target);todo.append(target)
        return visited
    if reachable(starts,out)!=set(nodes) or reachable(ends,incoming)!=set(nodes):raise ValueError('Every node must be reachable from a start and have a path to an end')
    for message in model['messages']:
        identify(message)
        endpoints=[message.get('source'),message.get('target')]
        if not(any(e in nodes for e in endpoints) and any(lanes.get(e,{}).get('scope')=='external' for e in endpoints)):
            raise ValueError('Message flows connect an internal node and an external participant')
    return {'name':spec['name'],'purpose':spec.get('purpose',''),'trigger':spec.get('trigger',''),'process':model}

def guide(manifest):
    m=manifest['process'];names={n['id']:n['name'] for n in m['nodes']};lanes={l['id']:l['name'] for l in m['swimlanes']}
    systems={s['id']:s['name'] for s in m['systems']};products={p['id']:p['name'] for p in m['work_products']}
    lines=['# '+manifest['name'],'',manifest['purpose'],'','Trigger: '+manifest['trigger'],'',
           'This describes the process. It does not execute tasks or establish business effects.','']
    for n in m['nodes']:
        lines += ['## '+n['name'],'','Performer: '+lanes[n['lane']]+'.',n.get('instructions',n.get('description',''))]
        if n.get('responsible_role'):lines += ['Accountable role: '+lanes[n['responsible_role']]+'.']
        for key,title,lookup in [('system_refs','Systems',systems),('work_products_in','Receives',products),('work_products_out','Produces',products)]:
            if n.get(key):lines += [title+': '+', '.join(lookup[r] for r in n[key])+'.']
        for e in m['edges']+m['conditional_edges']:
            if e['source']==n['id']:lines += ['- '+e.get('label','Then')+': '+names[e['target']]]
        lines += ['']
    return '\n'.join(lines).strip()+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for command in ['generate','validate']:
        cmd=sub.add_parser(command);cmd.add_argument('spec',type=Path)
        if command=='generate':cmd.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    try:
        manifest=normalise(json.loads(args.spec.read_text(encoding='utf-8-sig')))
        if args.command=='generate':
            # A new directory avoids silently replacing edited XML.
            args.out.mkdir(parents=True,exist_ok=False)
            (args.out/'process.bpmn').write_bytes(bpmn_xml(manifest,'process'))
            (args.out/'process-guide.md').write_text(guide(manifest),encoding='utf-8',newline='\n')
        print(json.dumps({'valid':True,'nodes':len(manifest['process']['nodes']),'execution':False}))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'valid':False,'error':str(exc)}),file=sys.stderr);return 1
    return 0

if __name__=='__main__':sys.exit(main())
