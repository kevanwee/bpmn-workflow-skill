import {BpmnModdle} from 'bpmn-moddle';
import {readFile} from 'node:fs/promises';
if(!process.argv[2])throw Error('Usage: node scripts/inspect.mjs process.bpmn');
const {rootElement,warnings}=await new BpmnModdle().fromXML(await readFile(process.argv[2],'utf8'));
const processes=rootElement.rootElements.filter(e=>e.$type==='bpmn:Process');
console.log(JSON.stringify({processes:processes.length,flowElements:processes.reduce((n,p)=>n+(p.flowElements||[]).length,0),diagrams:rootElement.diagrams?.length||0,warnings:warnings.map(w=>w.message),execution:false},null,2));
if(!processes.length||!rootElement.diagrams?.length||warnings.length)process.exitCode=1;
