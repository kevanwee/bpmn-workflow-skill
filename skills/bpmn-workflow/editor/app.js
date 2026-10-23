/* global BpmnJS */
const modeler=new BpmnJS({container:'#canvas'}),status=document.querySelector('#status');
let selected,documentationIndex=0;
const announce=(message,error=false)=>{status.textContent=message;status.classList.toggle('error',error)};
async function open(xml,name){
 try{const {warnings}=await modeler.importXML(xml);modeler.get('canvas').zoom('fit-viewport');announce(`${name} · ${warnings.length?warnings.length+' import warnings':'Ready to inspect and edit'}`);}
 catch(error){announce('Could not open BPMN: '+error.message+'. Choose a valid BPMN XML file.',true)}
}
modeler.on('selection.changed',({newSelection})=>{
 selected=newSelection.length===1?newSelection[0]:null;
 const editable=selected&&!selected.waypoints&&selected.businessObject?.$type!=='bpmn:Collaboration';
 document.querySelector('#inspector').hidden=!editable;
 document.querySelector('#selection').textContent=selected?selected.businessObject.$type.replace('bpmn:','')+' · '+selected.id:'Select an activity, event or gateway.';
 if(editable){
  document.querySelector('#name').value=selected.businessObject.name||'';
  const docs=selected.businessObject.documentation||[],entry=document.querySelector('#entry');entry.replaceChildren();documentationIndex=0;
  docs.forEach((doc,i)=>entry.add(new Option(`Entry ${i+1} · ${doc.textFormat||'text/plain'}`,String(i))));
  document.querySelector('#documentation-entries').hidden=docs.length<2;
  document.querySelector('#documentation').value=docs[0]?.text||'';
 }
});
document.querySelector('#entry').addEventListener('change',event=>{documentationIndex=Number(event.target.value);document.querySelector('#documentation').value=selected?.businessObject.documentation?.[documentationIndex]?.text||''});
document.querySelector('#inspector').addEventListener('submit',event=>{
 event.preventDefault();if(!selected)return;
 const modeling=modeler.get('modeling'),text=document.querySelector('#documentation').value,docs=selected.businessObject.documentation||[],doc=docs[documentationIndex];
 modeling.updateProperties(selected,{name:document.querySelector('#name').value});
 if(text!==(doc?.text||'')){
  if(doc)modeling.updateModdleProperties(selected,doc,{text});
  else modeling.updateProperties(selected,{documentation:[...docs,modeler.get('moddle').create('bpmn:Documentation',{text})]});
 }
 announce('Element updated. Download BPMN to keep your changes.');
});
modeler.on('commandStack.changed',()=>announce('Unsaved edits in this browser. Download BPMN to keep them.'));
document.querySelector('#file').addEventListener('change',async event=>{const file=event.target.files[0];if(file)await open(await file.text(),file.name);event.target.value=''});
document.querySelector('#fit').addEventListener('click',()=>modeler.get('canvas').zoom('fit-viewport'));
function download(data,type,name){const url=URL.createObjectURL(new Blob([data],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
for(const format of ['xml','svg'])document.querySelector('#'+format).addEventListener('click',async()=>{
 try{const result=format==='xml'?await modeler.saveXML({format:true}):await modeler.saveSVG();download(result[format],format==='xml'?'application/xml':'image/svg+xml',format==='xml'?'process.bpmn':'process.svg');announce('Downloaded '+(format==='xml'?'BPMN XML':'SVG')+'.');}
 catch(error){announce('Could not export the diagram: '+error.message,true)}
});
fetch('/example.bpmn').then(r=>{if(!r.ok)throw Error('Example unavailable');return r.text()}).then(xml=>open(xml,'Order fulfilment · illustrative process')).catch(error=>announce(error.message+'. Open an existing BPMN file to continue.',true));
