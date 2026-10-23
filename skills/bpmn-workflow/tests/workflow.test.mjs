import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile,mkdtemp,writeFile,rm,mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {BpmnModdle} from 'bpmn-moddle';
import {chromium} from 'playwright';
import {serve} from '../scripts/serve.mjs';
const python=process.env.PYTHON||'python';
test('Generator emits importable lanes, routes, products and external messages',async()=>{
 const dir=await mkdtemp(path.join(tmpdir(),'bpmn-'));
 try{execFileSync(python,['scripts/bpmn.py','generate','examples/order-fulfilment.json','--out',path.join(dir,'model')]);
  const xml=await readFile(path.join(dir,'model/process.bpmn'),'utf8');const {rootElement,warnings}=await new BpmnModdle().fromXML(xml);
  assert.deepEqual(warnings,[]);assert.equal(rootElement.diagrams.length,1);assert.ok(xml.includes('manualTask'));assert.ok(xml.includes('messageFlow'));
  assert.ok((await readFile(path.join(dir,'model/process-guide.md'),'utf8')).includes('Inventory system'));
  assert.throws(()=>execFileSync(python,['scripts/bpmn.py','generate','examples/order-fulfilment.json','--out',path.join(dir,'model')],{stdio:'pipe'}));
 }finally{await rm(dir,{recursive:true,force:true})}
});
test('Invalid references, disconnected work and incompatible performers are rejected',async()=>{
 const dir=await mkdtemp(path.join(tmpdir(),'bpmn-'));const spec=JSON.parse(await readFile('examples/order-fulfilment.json','utf8'));
 try{for(const change of [s=>s.flows[0].target='unknown',s=>s.nodes.push({id:'orphan',name:'Unreachable work',type:'user',lane:'operations'}),s=>s.nodes.find(n=>n.id==='create-invoice').responsible_role='customer',s=>s.nodes.find(n=>n.id==='pack-order').system_refs=['inventory-system'],s=>s.flows.find(e=>e.id==='f-valid').label='']){
  const copy=structuredClone(spec);change(copy);const file=path.join(dir,'invalid.json');await writeFile(file,JSON.stringify(copy));
  assert.throws(()=>execFileSync(python,['scripts/bpmn.py','validate',file],{stdio:'pipe'}));
 }}finally{await rm(dir,{recursive:true,force:true})}
});
test('Independent bpmn.io editor imports, edits, and downloads real XML and SVG',async()=>{
 const browser=await chromium.launch(),server=await serve(0),origin=`http://127.0.0.1:${server.address().port}`;
 try{const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.getByRole('status').filter({hasText:'Ready to inspect'}).waitFor();
  await page.locator('.djs-element[data-element-id="user_record_order"] .djs-hit').click();
  await page.getByLabel('Name',{exact:true}).fill('Record and reconcile the customer order');
  await page.getByLabel('Instructions and context').fill('Check the actual order fields before proceeding.');await page.getByRole('button',{name:'Apply to element'}).click();
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download BPMN',exact:true}).click();const file=await (await download).path();
  const xml=await readFile(file,'utf8');assert.ok(xml.includes('Record and reconcile the customer order'));assert.ok(xml.includes('Check the actual order fields'));
  assert.deepEqual((await new BpmnModdle().fromXML(xml)).warnings,[]);
  const svgEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Download SVG',exact:true}).click();assert.ok((await readFile(await (await svgEvent).path(),'utf8')).includes('<svg'));
  // Name-only edits must retain arbitrary imported documentation entries/formats.
  const moddle=new BpmnModdle(),loaded=await moddle.fromXML(xml),task=loaded.elementsById.user_record_order;
  task.documentation=[moddle.create('bpmn:Documentation',{text:'First original entry',textFormat:'text/plain'}),moddle.create('bpmn:Documentation',{text:'<p>Second original entry</p>',textFormat:'text/html'})];
  const imported=(await moddle.toXML(loaded.rootElement,{format:true})).xml;
  await page.getByLabel('Open BPMN file').setInputFiles({name:'multiple-docs.bpmn',mimeType:'application/xml',buffer:Buffer.from(imported)});
  await page.getByRole('status').filter({hasText:'multiple-docs.bpmn'}).waitFor();
  await page.locator('.djs-element[data-element-id="user_record_order"] .djs-hit').click();
  await page.getByLabel('Name',{exact:true}).fill('Name-only edit');await page.getByRole('button',{name:'Apply to element'}).click();
  const preservedDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Download BPMN',exact:true}).click();
  const preserved=await new BpmnModdle().fromXML(await readFile(await (await preservedDownload).path(),'utf8'));
  assert.deepEqual(preserved.elementsById.user_record_order.documentation.map(d=>[d.text,d.textFormat]),[['First original entry','text/plain'],['<p>Second original entry</p>','text/html']]);
  await page.getByLabel('Documentation entry').selectOption('1');await page.getByLabel('Instructions and context').fill('<p>Explicitly revised second entry</p>');await page.getByRole('button',{name:'Apply to element'}).click();
  const editedDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Download BPMN',exact:true}).click();
  const edited=await new BpmnModdle().fromXML(await readFile(await (await editedDownload).path(),'utf8'));
  assert.deepEqual(edited.elementsById.user_record_order.documentation.map(d=>[d.text,d.textFormat]),[['First original entry','text/plain'],['<p>Explicitly revised second entry</p>','text/html']]);
  assert.equal((await page.request.get(origin+'/package.json')).status(),404);
  assert.equal((await page.request.post(origin+'/')).status(),405);
  assert.equal((await page.request.get(origin+'/',{headers:{Host:'hostile.example'}})).status(),403);
  assert.deepEqual(errors,[]);
 }finally{await browser.close();await new Promise(r=>server.close(r))}
});
