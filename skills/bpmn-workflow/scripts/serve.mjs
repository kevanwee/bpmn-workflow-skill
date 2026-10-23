import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
export async function serve(port=8790){
 const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
 const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.woff':'font/woff','.woff2':'font/woff2','.ttf':'font/ttf','.eot':'application/vnd.ms-fontobject'};
 const routes={'/':'editor/index.html','/app.js':'editor/app.js','/style.css':'editor/style.css',
  '/modeler.js':'node_modules/bpmn-js/dist/bpmn-modeler.development.js','/diagram.css':'node_modules/bpmn-js/dist/assets/diagram-js.css',
  '/bpmn.css':'node_modules/bpmn-js/dist/assets/bpmn-font/css/bpmn.css','/example.bpmn':'examples/order-fulfilment.bpmn'};
 const server=createServer(async(req,res)=>{
  const address=`127.0.0.1:${server.address().port}`;
  if(![address,`localhost:${server.address().port}`].includes(req.headers.host)){res.writeHead(403);res.end('Use the printed loopback URL');return;}
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
  if(req.method!=='GET'){res.writeHead(405);res.end('Read-only local editor server');return;}
  const name=new URL(req.url,'http://'+address).pathname;
  let relative=routes[name];
  if(/^\/font\/bpmn\.(woff2?|ttf|eot|svg)$/.test(name))relative='node_modules/bpmn-js/dist/assets/bpmn-font'+name;
  if(!relative){res.writeHead(404);res.end('Resource not found');return;}
  try{const file=path.join(root,relative);res.setHeader('Content-Type',types[path.extname(file)]||'application/xml');res.end(await readFile(file));}
  catch{res.writeHead(404);res.end('Resource unavailable. Run npm ci from the skill folder.');}
 });
 await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));return server;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const index=process.argv.indexOf('--port'),port=index>=0?Number(process.argv[index+1]):8790;
 if(!Number.isInteger(port)||port<0||port>65535)throw Error('Choose a valid local port');
 const server=await serve(port);console.log(`BPMN Workflow: http://127.0.0.1:${server.address().port}`);
}
